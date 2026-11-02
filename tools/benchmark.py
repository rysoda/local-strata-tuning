"""Shared sequential BetterBench mechanics; campaigns own definitions and checkpoints.
Call configure() before using. Importing never starts a server.
"""
import copy, json, msvcrt, os, pathlib, statistics, subprocess, sys, time, urllib.request
REPO = pathlib.Path(__file__).resolve().parents[1]
LOCAL = pathlib.Path(os.environ['LOCALAPPDATA'])/'Strata'
BB = pathlib.Path.home()/'BetterBench/.venv/Scripts/betterbench.exe'
WORKLOAD = REPO/'workloads/betterbench-16k.json'

def configure(campaign, control):
    global ROOT, RESULTS, CONFIGS, STATE_DIR, STATE, CONTROL
    ROOT = pathlib.Path(campaign)
    RESULTS = ROOT/'results'
    CONFIGS = ROOT/'configs/private'
    STATE_DIR = ROOT/'state'
    STATE = STATE_DIR/'queue-state.json'
    CONTROL = pathlib.Path(control)
    for directory in (RESULTS, CONFIGS, STATE_DIR):
        directory.mkdir(parents=True, exist_ok=True)

def checkpoint(state):
    raise RuntimeError('Campaign must install its own checkpoint callback')

def save(path, data):
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,indent=2))
    tmp.replace(path)

def load(path): return json.loads(path.read_text())

def request(route, cfg):
    req = urllib.request.Request('http://127.0.0.1:8080'+route,headers={'Authorization':'Bearer '+cfg['api_key']})
    with urllib.request.urlopen(req,timeout=5) as r: return json.load(r)

def stop_server(pid):
    if pid:
        # Only our explicitly recorded, still-owned server. Check command line before killing.
        owned_path = str(CONFIGS)
        script = f'$p=Get-CimInstance Win32_Process -Filter "ProcessId={int(pid)}"; if ($p -and $p.CommandLine -like "*{owned_path}*") {{ taskkill /PID {int(pid)} /T /F }}'
        cmd = ['powershell.exe','-NoProfile','-Command',script]
        subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(5)

def summarize(path):
    d = load(path)
    rows = d.get('single_stream',{}).get('code',[])
    dec = [r['decode_tps'] for r in rows if r.get('ok') and r.get('decode_tps')]
    pf = d.get('prefill',[])
    pp = pf[0].get('pp_tps',[]) if pf else []
    return dict(decode=statistics.median(dec) if dec else None,prefill=statistics.median(pp) if pp else None,decode_ok=len(dec),prefill_ok=len(pp),valid=len(dec)==5 and len(pp)==8)


read_json = load

def run_one(item,state):
    id=item['id']
    cfg=copy.deepcopy(load(CONFIGS/'baseline.json'))
    cfg['env']['STRATA_ROUTE_TAIL_SKIP']='0'
    cfg['env'].update(item['env'])
    args=cfg['args']
    # Replace only flags this experiment sets; leave every other original argument alone.
    extra=item['args']
    i=0
    while i<len(extra):
        flag=extra[i]
        group=[flag]
        if i+1<len(extra) and not extra[i+1].startswith('--'):
            group.append(extra[i+1])
        if flag in args:
            at=args.index(flag)
            count=1 if at+1==len(args) or args[at+1].startswith('--') else 2
            del args[at:at+count]
        args.extend(group)
        i+=len(group)
    cfg['log']=str(RESULTS/f'{id}.engine.log')
    path=CONFIGS/f'{id}.json'
    save(path,cfg)
    serverlog=open(RESULTS/f'{id}.server.log','a')
    serverenv=os.environ.copy(); serverenv['STRATA_NO_PRESET']='1'
    p=subprocess.Popen([str(CONTROL/'python/python.exe'),str(CONTROL/'serve/server.py'),'--engine','strata','--config',str(path),'--host','127.0.0.1','--port','8080'],cwd=CONTROL,env=serverenv,stdout=serverlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    r=dict(phase='loading',server_pid=p.pid,started=time.strftime('%Y-%m-%d %H:%M:%S'))
    state['runs'][id]=r
    checkpoint(state)
    try:
        deadline=time.monotonic()+1800
        while time.monotonic()<deadline:
            if p.poll() is not None: raise RuntimeError(f'server exited {p.returncode}')
            try:
                health=request('/health',cfg)
                if health.get('loaded') and health.get('status')=='ok': break
            except Exception: pass
            time.sleep(5)
        else: raise RuntimeError('model load timeout')
        save(RESULTS/f'{id}.health.json',health)
        cmd=[str(BB),'run','--endpoint','http://127.0.0.1:8080/v1','--model',cfg['model_name'],'--quick','--decode','--categories','code','--prefill','--no-concurrency','--config',str(WORKLOAD),'--out',str(RESULTS/f'{id}.json')]
        r['phase']='benchmark-running'
        checkpoint(state)
        env=os.environ.copy(); env['BETTERBENCH_API_KEY']=cfg['api_key']; env['PYTHONUNBUFFERED']='1'; env['PYTHONIOENCODING']='utf-8'
        with open(RESULTS/f'{id}.bench.log','a') as log:
            b=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
            r['benchmark_pid']=b.pid; checkpoint(state)
            deadline=time.monotonic()+10800
            with open(RESULTS/f'{id}.gpu.csv','a') as telemetry:
                telemetry.write('time, temperature_C, gpu_util_pct, memory_used_MiB, sm_MHz, power_W\n')
                while True:
                    try: code=b.wait(timeout=15); break
                    except subprocess.TimeoutExpired:
                        if time.monotonic()>deadline:
                            b.kill(); b.wait(); raise RuntimeError('benchmark exceeded 3-hour safety limit')
                        try:
                            sample=subprocess.check_output(['nvidia-smi','--query-gpu=temperature.gpu,utilization.gpu,memory.used,clocks.sm,power.draw','--format=csv,noheader,nounits'],text=True,timeout=5)
                            telemetry.write(time.strftime('%Y-%m-%d %H:%M:%S')+', '+sample); telemetry.flush()
                        except Exception: pass
        if code: raise RuntimeError(f'BetterBench exited {code}')
        r['metrics']=summarize(RESULTS/f'{id}.json')
        r['phase']='complete' if r['metrics']['valid'] else 'invalid'
        try: save(RESULTS/f'{id}.metrics.json',request('/metrics',cfg))
        except Exception: pass
        if item.get('sanity'):
            r['phase']='sanity-running'; checkpoint(state)
            with open(RESULTS/f'{id}.sanity.log','a') as log:
                result=subprocess.run([str(CONTROL/'python/python.exe'),str(REPO/'tools/sanity.py'),str(path),str(RESULTS/f'{id}.sanity.json')],env=serverenv,stdout=log,stderr=subprocess.STDOUT,timeout=3600)
            sanity=load(RESULTS/f'{id}.sanity.json')
            r['sanity']={k:sanity[k] for k in ('passed','total')}
            r['phase']='complete' if result.returncode==0 and sanity['passed']==sanity['total'] else 'sanity-failed'
    except Exception as exc:
        r['phase']='failed'; r['error']=str(exc)
    finally:
        # p is a process created in this function, so no PID-reuse ambiguity.
        if p.poll() is None:
            subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            p.wait(timeout=30)
        serverlog.close()
        r['finished']=time.strftime('%Y-%m-%d %H:%M:%S')
        checkpoint(state)
        time.sleep(10)
