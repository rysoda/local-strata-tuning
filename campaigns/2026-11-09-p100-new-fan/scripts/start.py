"""Start an isolated P100-only server, without a stress workload or preset changes."""
import datetime
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'tools'))
from launch import resolve


def main():
    state_path = ROOT / 'state/queue-state.json'
    state = json.loads(state_path.read_text())
    if state['phase'] != 'planned':
        raise SystemExit('Inspect existing state and live ownership before recovery; refusing repeat launch.')
    processes = subprocess.check_output([
        'powershell.exe', '-NoProfile', '-Command',
        'Get-CimInstance Win32_Process | Where-Object { $_.Name -match "^strata.*\\.exe$" -or ($_.Name -match "^python.*\\.exe$" -and $_.CommandLine -match "server.py|benchmark|monitor_power") } | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json'
    ], text=True).strip()
    if processes:
        raise SystemExit('Existing workload requires review:\n' + processes)
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1', 8080)) == 0:
            raise SystemExit('Port 8080 occupied. Nothing stopped.')
    _, control, cfg = resolve('2026-11-08-p100-1080ti-reserve-performance', 131072)
    installed = Path(os.environ['LOCALAPPDATA']) / 'Strata/launch/iq3_s-128k.json'
    installed_cfg = json.loads(installed.read_text(encoding='utf-8'))
    if installed_cfg.get('api_key'):
        cfg['api_key'] = installed_cfg['api_key']
    cfg.update(gpu=0, host='0.0.0.0', port=8080, open_browser=False,
               log=str(ROOT / 'results/p100.engine.log'))
    cfg.pop('layer_split', None)
    args = cfg['args']
    for flag in ('--vram-reserve-mib', '--vram-reserve-later-mib', '--layer-split'):
        if flag in args:
            i = args.index(flag)
            del args[i:i + 2]
    if '--trim-stage-weights' in args:
        args.remove('--trim-stage-weights')
    runtime = ROOT / 'configs/private/p100.runtime.json'
    runtime.write_text(json.dumps(cfg, indent=2) + '\n', encoding='utf-8')
    (ROOT / 'results/hardware.txt').write_text(subprocess.check_output(['nvidia-smi'], text=True), encoding='utf-8')
    cmd = [str(control / 'python/python.exe'), str(control / 'serve/server.py'),
           '--engine', 'strata', '--config', str(runtime), '--host', '0.0.0.0', '--port', '8080']
    state.update(phase='starting', current='p100-server',
                 started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=cmd)
    state_path.write_text(json.dumps(state, indent=2) + '\n')
    env = os.environ.copy()
    env.update(STRATA_NO_PRESET='1', PYTHONIOENCODING='utf-8')
    try:
        with (ROOT / 'results/server.log').open('ab') as log:
            proc = subprocess.Popen(cmd, cwd=control, env=env, stdin=subprocess.DEVNULL,
                                    stdout=log, stderr=subprocess.STDOUT,
                                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
        state['server_pid'] = proc.pid
        state_path.write_text(json.dumps(state, indent=2) + '\n')
        print(f'P100-only server PID {proc.pid}, 131072 context, 0.0.0.0:8080; loading.')
    except Exception as error:
        state.update(phase='launch-failed', error=str(error))
        state_path.write_text(json.dumps(state, indent=2) + '\n')
        raise


if __name__ == '__main__':
    main()
