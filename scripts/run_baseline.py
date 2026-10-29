"""Wait for our isolated server and run the requested unmodified BetterBench workload."""
import json, os, pathlib, subprocess, time, urllib.request
ROOT = pathlib.Path(__file__).resolve().parents[1]
cfg = json.loads((ROOT/'configs/baseline.json').read_text())
state = ROOT/'results/baseline.status.json'
def status(phase, **extra):
    state.write_text(json.dumps(dict(phase=phase, updated=time.strftime('%Y-%m-%d %H:%M:%S'), **extra), indent=2))
status('waiting-for-model')
for _ in range(360):
    try:
        req = urllib.request.Request('http://127.0.0.1:8080/health', headers={'Authorization':'Bearer '+cfg['api_key']})
        with urllib.request.urlopen(req, timeout=5) as r:
            health = json.load(r)
        if health.get('loaded', True) and health.get('status') not in ('loading','error'):
            (ROOT/'results/baseline.health.json').write_text(json.dumps(health, indent=2))
            break
    except Exception:
        pass
    time.sleep(5)
else:
    status('failed', reason='readiness timeout')
    raise SystemExit(1)
env = os.environ.copy()
env['BETTERBENCH_API_KEY'] = cfg['api_key']
env['PYTHONUNBUFFERED'] = '1'
env['PYTHONIOENCODING'] = 'utf-8'
exe = pathlib.Path.home()/'BetterBench/.venv/Scripts/betterbench.exe'
cmd = [str(exe),'run','--endpoint','http://127.0.0.1:8080/v1','--model',cfg['model_name'],'--quick','--decode','--categories','code','--prefill','--no-concurrency','--config',str(ROOT/'16k.json'),'--out',str(ROOT/'results/baseline.json')]
status('benchmark-running', command=cmd)
with open(ROOT/'results/baseline.bench.log','w') as log:
    code = subprocess.call(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
status('complete' if code == 0 else 'failed', returncode=code)
