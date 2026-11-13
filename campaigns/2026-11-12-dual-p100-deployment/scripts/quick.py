"""Three diagnostic runs against the existing user server; never manages that server."""
import datetime, hashlib, json, os, pathlib, statistics, subprocess, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO/'tools'))
import benchmark as bm
CFG = pathlib.Path(os.environ['LOCALAPPDATA'])/'Strata/launch/iq3_s-128k.json'
STATE = ROOT/'state/queue-state.json'
def save(path, data): bm.save(path, data)
def now(): return datetime.datetime.now().isoformat()
def main():
    import msvcrt
    lock = open(ROOT/'state/runner.lock', 'a+b'); lock.write(b'0'); lock.flush(); lock.seek(0)
    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    state = bm.load(STATE)
    if state['phase'] == 'complete': print('Already complete'); return
    if state['phase'] not in ('planned','paused'): raise RuntimeError('Incomplete/failed attempt requires review; refusing restart')
    cfg = bm.load(CFG)
    save(ROOT/'configs/private/installed.json', cfg)
    fingerprint = hashlib.sha256(CFG.read_bytes()).hexdigest()
    def inspect():
        if hashlib.sha256(CFG.read_bytes()).hexdigest() != fingerprint: raise RuntimeError('Installed profile changed')
        health = bm.request('/health',cfg); metrics = bm.request('/metrics',cfg)
        if metrics.get('engine',{}).get('version') != '0.1.59': raise RuntimeError('Unexpected engine version')
        if metrics.get('live',{}).get('state') != 'idle' or metrics.get('live',{}).get('queued',0): raise RuntimeError('Server busy; refusing competing load')
        return health,metrics
    health,metrics = inspect()
    save(ROOT/'results/initial.health.json',health); save(ROOT/'results/initial.metrics.json',metrics)
    save(ROOT/'results/settings.json',{k:cfg.get(k) for k in ('exe','args','env','model_name','gpu','layer_split','drafting','tokenizer')})
    inventory = subprocess.run(['nvidia-smi','-q'],capture_output=True,text=True,timeout=20)
    (ROOT/'results/nvidia-smi.txt').write_text(inventory.stdout,encoding='utf-8')
    processes = subprocess.run(['powershell.exe','-NoProfile','-Command','Get-CimInstance Win32_Process | Where-Object { $_.Name -match "strata|python|betterbench" } | Select-Object ProcessId,Name,CommandLine | Format-List'],capture_output=True,text=True,timeout=20)
    (ROOT/'results/processes.txt').write_text(processes.stdout,encoding='utf-8')
    state.update(phase='running',started=now(),server_owned=False,supervisor_pid=os.getpid()); save(STATE,state)
    try:
        for i in range(1,4):
            rid=f'quick-{i}'
            if rid in state['runs']:
                if state['runs'][rid]['phase']=='complete': continue
                raise RuntimeError('Ambiguous previous run')
            if (ROOT/'state/STOP').exists(): state['phase']='paused'; save(STATE,state); return
            health,metrics=inspect()
            save(ROOT/f'results/{rid}.before.metrics.json',metrics)
            out=ROOT/f'results/{rid}.json'
            if out.exists(): raise RuntimeError('Existing artifact without complete checkpoint')
            cmd=[str(bm.BB),'run','--endpoint','http://127.0.0.1:8080/v1','--model',cfg['model_name'],'--quick','--decode','--categories','code','--prefill','--no-concurrency','--config',str(bm.WORKLOAD),'--out',str(out)]
            save(ROOT/f'results/{rid}.command.json',cmd)
            run={'phase':'starting','started':now()};state['runs'][rid]=run;state['current']=rid;save(STATE,state)
            env=os.environ.copy();env.update(BETTERBENCH_API_KEY=cfg['api_key'],PYTHONUNBUFFERED='1',PYTHONIOENCODING='utf-8')
            with open(ROOT/f'results/{rid}.bench.log','w',encoding='utf-8') as log,open(ROOT/f'results/{rid}.gpu.csv','w',encoding='utf-8') as gpu:
                gpu.write('time, name, bus, temperature_C, utilization_pct, memory_MiB, sm_MHz, power_W\n')
                p=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
                run.update(phase='running',benchmark_pid=p.pid);save(STATE,state)
                deadline=time.monotonic()+3600
                try:
                    while True:
                        try: code=p.wait(timeout=15);break
                        except subprocess.TimeoutExpired:
                            if time.monotonic()>deadline: raise RuntimeError('One-hour benchmark timeout')
                            sample=subprocess.run(['nvidia-smi','--query-gpu=name,pci.bus_id,temperature.gpu,utilization.gpu,memory.used,clocks.sm,power.draw','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
                            for line in sample.stdout.splitlines():gpu.write(now()+', '+line+'\n')
                            gpu.flush()
                finally:
                    if p.poll() is None: p.kill();p.wait()
            if code:raise RuntimeError(f'BetterBench exit {code}')
            summary=bm.summarize(out)
            save(ROOT/f'results/{rid}.summary.json',summary)
            save(ROOT/f'results/{rid}.after.metrics.json',bm.request('/metrics',cfg))
            run.update(phase='complete' if summary['valid'] else 'invalid',finished=now(),summary=summary);save(STATE,state)
            print(rid,json.dumps(summary),flush=True)
            if not summary['valid']:raise RuntimeError('Incomplete benchmark samples; review required')
        state.update(phase='complete',current=None,finished=now());save(STATE,state)
        manifest=bm.load(ROOT/'manifest.json');manifest.update(status='complete',completed_phase='complete',completed_benchmarks=3,report='REPORT.md');save(ROOT/'manifest.json',manifest)
        rows=[r['summary'] for r in state['runs'].values()]
        means={k:statistics.mean(r[k] for r in rows) for k in ('decode','prefill')}
        save(ROOT/'results/summary.json',means)
        report='# Dual P100: three quick benchmarks\n\nComplete. Existing user server was not restarted, modified or stopped.\n\n| Run | Decode tok/s | Prefill tok/s |\n|---|---:|---:|\n'
        for rid,r in state['runs'].items():report+=f"| {rid} | {r['summary']['decode']:.3f} | {r['summary']['prefill']:.3f} |\n"
        report+=f"| **Mean of medians** | **{means['decode']:.3f}** | **{means['prefill']:.3f}** |\n\n"
        report+='Each run: 5/5 decode and 8/8 prefill samples. Exact quick code/16K-target workload; all actual token counts, samples and errors retained in results/*.json. Generated code not executed. No functional or long-context quality tests requested or performed.\n\n'
        report+='## Conditions and limitations\n\nTwo Tesla P100 16GB GPUs; actual link details retained in nvidia-smi.txt. Engine 0.1.59 / Control 0.1.57, IQ3_S, 262144 context, int8 KV, resident32768, MTP, full experts, 36/12 split, reserves640/896. Existing experimental projection retained as diagnostic baseline, not validated here. No settings, installation or startup launcher changed by the benchmark runner.\n\nThree sequential quick runs are screening, not statistical significance or quality equivalence. User-server cache history and other activity are uncontrolled. Prior P100/1080 Ti results are different hardware and not a controlled comparison. Server left running at user request.\n'
        (ROOT/'REPORT.md').write_text(report,encoding='utf-8')
    except BaseException as exc:
        state.update(phase='failed',error=str(exc),finished=now());save(STATE,state);raise
if __name__=='__main__': main()
