"""Resumable, sequential single-parameter runner. STOP file pauses between runs.
No installed files are edited. Run: python scripts/tune.py
Results are screening only; combined tests require subsequent review.
"""
import copy, json, msvcrt, os, pathlib, statistics, subprocess, sys, time, urllib.request
ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT/'results'
LOCAL = pathlib.Path(os.environ['LOCALAPPDATA'])/'Strata'
CONTROL = LOCAL/'components/control/0.1.51'
BB = pathlib.Path.home()/'BetterBench/.venv/Scripts/betterbench.exe'
STATE = RESULTS/'queue-state.json'

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
        owned_path = str(ROOT / 'configs')
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

def render(state):
    entries = [('baseline',{})] + [(x['id'],x) for x in load(ROOT/'experiments.json')]
    if (ROOT/'combined-experiments.json').exists():
        entries += [(x['id'],x) for x in load(ROOT/'combined-experiments.json')]
    ref = state.get('runs',{}).get('quality-reference',{}).get('metrics',{})
    text = ['# Tuning results','', 'Live checkpoint. Speeds are tokens/s, medians. Five sampled decode passes are provisional; not significance or quality proof. All experiment deltas use the quality reference, NOT the approximate original baseline.','', '| Run | State | Code decode | 16K prefill | Decode delta | Prefill delta | Usage |','|---|---|---:|---:|---:|---:|---|']
    for id, item in entries:
        r = state.get('runs',{}).get(id,{})
        m = r.get('metrics',{})
        dec, pp = m.get('decode'), m.get('prefill')
        dd = (dec/ref['decode']-1)*100 if dec and ref.get('decode') else None
        pd = (pp/ref['prefill']-1)*100 if pp and ref.get('prefill') else None
        mark = 'pending'
        if m:
            mark = 'invalid' if not m.get('valid') else 'reference' if item.get('family')=='reference' else 'baseline only' if id=='baseline' else 'not selected'
            if id!='baseline' and item.get('family')!='reference' and m.get('valid') and dd is not None and pd is not None:
                if (dd>3 and pd>-10) or (pd>5 and dd>-3): mark='provisional gain; confirm'
        final=state.get('final_selection')
        if final:
            if id in final['single_components']: mark='USE (combined-confirmed)'
            elif id in final['confirmation_ids']: mark='recommended combination'
            elif item.get('family')=='reference': mark='reference'
            elif id=='baseline': mark='approximate original baseline only'
            elif r.get('phase')=='failed': mark='incompatible; see log'
            elif m: mark='not selected after combined review'
        vals=[id,r.get('phase','pending'),f'{dec:.2f}' if dec else '—',f'{pp:.2f}' if pp else '—',f'{dd:+.1f}%' if dd is not None else '—',f'{pd:+.1f}%' if pd is not None else '—',mark]
        text.append('| '+' | '.join(vals)+' |')
    text += ['', '## Checkpoint', '', f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"Queue phase: {state.get('phase')}; current: {state.get('current','none')}", '', 'Each run has `results/<id>.json`, `.html`, `.engine.log`, `.server.log`, `.bench.log`, and `configs/<id>.json`. See `TUNING_PLAN.md` for interpretation and exclusions.', '', '## Combined stage', '', 'See `STAGE1_REVIEW.md` and `COMBINED_RESULTS.md` for late-reference comparisons, combination rationale and status. Initial-reference deltas above are screening only; auto-sized cache/chunk drift confounds them.']
    if state.get('final_selection'):
        text += ['', '## Final decision', '', 'Completed. See `FINAL_REPORT.md` for the final nearby-reference comparison and `configs/recommended.json` / `Run-Tuned.cmd` for the ready-to-run profile. Initial-reference deltas in this table are NOT the final claimed gain. Only tasks 36, adaptation interval 1 and PCIe balance are retained as speed changes; approximate routing is disabled.']
    (ROOT/'RESULTS.md').write_text('\n'.join(text)+'\n',encoding='utf-8')

def checkpoint(state):
    save(STATE,state)
    render(state)

def run_one(item,state):
    id=item['id']
    cfg=copy.deepcopy(load(ROOT/'configs/baseline.json'))
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
    path=ROOT/f'configs/{id}.json'
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
        cmd=[str(BB),'run','--endpoint','http://127.0.0.1:8080/v1','--model',cfg['model_name'],'--quick','--decode','--categories','code','--prefill','--no-concurrency','--config',str(ROOT/'16k.json'),'--out',str(RESULTS/f'{id}.json')]
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
                result=subprocess.run([str(CONTROL/'python/python.exe'),str(ROOT/'scripts/sanity.py'),str(path),str(RESULTS/f'{id}.sanity.json')],env=serverenv,stdout=log,stderr=subprocess.STDOUT,timeout=3600)
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

def main():
    lock=open(RESULTS/'queue.lock','a+b'); lock.seek(0); lock.write(b'0'); lock.flush(); lock.seek(0)
    try: msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    except OSError: raise SystemExit('Another tuning runner owns the lock')
    state=load(STATE) if STATE.exists() else {'runs':{}}
    if state.get('phase')=='tuning-complete':
        print('Tuning already complete. See FINAL_REPORT.md; no processes started.')
        return
    state.update(phase='waiting-for-baseline',runner_pid=os.getpid())
    checkpoint(state)
    while True:
        baseline=load(RESULTS/'baseline.status.json')
        if baseline['phase']=='complete': break
        if baseline['phase']=='failed': raise RuntimeError('Baseline failed; inspect before continuing')
        if (ROOT/'STOP').exists(): state['phase']='paused'; checkpoint(state); return
        time.sleep(10)
    m=summarize(RESULTS/'baseline.json')
    state['runs']['baseline']={'phase':'complete' if m['valid'] else 'invalid','metrics':m}
    checkpoint(state)
    if not m['valid']: raise RuntimeError('Baseline missing successful measurements; inspect before continuing')
    stop_server(load(RESULTS/'baseline.process.json')['server_pid'])
    # Do not compete with any server still listening on the benchmark port.
    import socket
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',8080))==0: raise RuntimeError('Port 8080 still occupied; no experiment started')
    for item in load(ROOT/'experiments.json'):
        id=item['id']
        old=state['runs'].get(id,{})
        if old.get('phase') in ('complete','invalid','failed'): continue
        if old.get('server_pid'): raise RuntimeError(f'Interrupted experiment {id}: inspect recorded processes before resuming')
        if (ROOT/'STOP').exists(): state['phase']='paused'; checkpoint(state); return
        state.update(phase='single-parameter-tests',current=id)
        checkpoint(state)
        run_one(item,state)
        if state['runs'][id]['phase']!='complete':
            state['phase']='paused-on-error'; checkpoint(state); return
    state.update(phase='singles-complete-review-required',current=None)
    checkpoint(state)

if __name__=='__main__': main()
