"""Start only the isolated P100 server; no stress workload or telemetry run."""
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
        raise SystemExit('Not a fresh launch. Inspect live processes and existing state before recovery.')
    processes = subprocess.check_output([
        'powershell.exe', '-NoProfile', '-Command',
        'Get-CimInstance Win32_Process | Where-Object { $_.Name -match "^strata.*\\.exe$" -or ($_.Name -match "^python.*\\.exe$" -and $_.CommandLine -match "server.py|benchmark|monitor_power") } | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json'
    ], text=True).strip()
    if processes:
        raise SystemExit('Possible existing workload; review before launch:\n' + processes)
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1', 8080)) == 0:
            raise SystemExit('Port 8080 occupied. Nothing stopped.')
    _, control, credential_source = resolve('2026-11-02-p100-1080ti-x8-x8')
    source = REPO / 'campaigns/2026-11-02-p100-1080ti-x8-x8/configs/shareable/x8-p100-only.json'
    cfg = json.loads(source.read_text())
    cfg.update(api_key=credential_source['api_key'], host='0.0.0.0', port=8080,
               open_browser=False, log=str(ROOT / 'results/p100-rear-pull.engine.log'))
    assert cfg['gpu'] == 0 and cfg['args'][cfg['args'].index('--max-context') + 1] == '131072'
    runtime = ROOT / 'configs/private/p100.runtime.json'
    runtime.write_text(json.dumps(cfg, indent=2) + '\n')
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state.update(phase='starting', current='p100-server', started_utc=stamp)
    state_path.write_text(json.dumps(state, indent=2) + '\n')
    env = os.environ.copy()
    env.update(STRATA_NO_PRESET='1', PYTHONIOENCODING='utf-8')
    cmd = [str(control / 'python/python.exe'), str(control / 'serve/server.py'),
           '--engine', 'strata', '--config', str(runtime), '--host', '0.0.0.0', '--port', '8080']
    try:
        with (ROOT / 'results/p100-server.log').open('ab') as log:
            proc = subprocess.Popen(cmd, cwd=control, env=env, stdin=subprocess.DEVNULL,
                                    stdout=log, stderr=subprocess.STDOUT,
                                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
        state.update(server_pid=proc.pid, command=cmd)
        state_path.write_text(json.dumps(state, indent=2) + '\n')
        print(f'Started P100-only server PID {proc.pid}; context 131072; 0.0.0.0:8080. Loading, not yet confirmed ready.')
    except Exception as error:
        state.update(phase='launch-failed', error=str(error))
        state_path.write_text(json.dumps(state, indent=2) + '\n')
        raise


if __name__ == '__main__':
    main()
