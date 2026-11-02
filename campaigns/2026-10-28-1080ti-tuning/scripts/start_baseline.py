from pathlib import Path
import sys
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
"""Start an isolated copy of the existing 128K profile; never edit the installation."""
import json, os, pathlib, subprocess, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[1]
checkpoint = ROOT/'state/queue-state.json'
if checkpoint.exists() and json.loads(checkpoint.read_text()).get('phase') == 'tuning-complete':
    print('Campaign complete; no baseline server started.')
    raise SystemExit(0)
LOCAL = pathlib.Path(os.environ['LOCALAPPDATA']) / 'Strata'
source = LOCAL / 'launch/iq3_s-128k.json'
cfg = json.loads(source.read_text())
(ROOT / 'configs/private/original-profile.json').write_text(json.dumps(cfg, indent=2))
cfg['exe'] = str(LOCAL / 'components/engine/0.1.52-windows-x86_64-cuda-cuda12/strata.exe')
cfg['host'] = '127.0.0.1'
cfg['port'] = 8080
cfg['open_browser'] = False
cfg['log'] = str(ROOT / 'results/baseline.engine.log')
config = ROOT / 'configs/private/baseline.json'
config.write_text(json.dumps(cfg, indent=2))
control = LOCAL / 'components/control/0.1.51'
log = open(ROOT / 'results/baseline.server.log', 'w')
p = subprocess.Popen([str(control/'python/python.exe'), str(control/'serve/server.py'), '--engine','strata','--config',str(config),'--host','127.0.0.1','--port','8080'], cwd=control, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
(ROOT / 'state/baseline.process.json').write_text(json.dumps({'server_pid':p.pid,'started':time.strftime('%Y-%m-%d %H:%M:%S'),'config':str(config)}, indent=2))
print('Server started, PID',p.pid)
