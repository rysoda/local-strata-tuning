"""Capture three passive cooling runs for one manually confirmed physical setup."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
STATE = ROOT / 'state/queue-state.json'
LOCK = ROOT / 'state/capture.lock'
GPU = 'GPU-bab5c751-1e02-b6a7-cf6f-b6256c3a5999'
MONITOR = REPO / 'campaigns/2026-11-03-p100-open-case-cooling/scripts/monitor_power.py'


def save(state):
    state['updated_utc'] = datetime.now(timezone.utc).isoformat()
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(state, indent=2) + '\n')
    temp.replace(STATE)


def preflight():
    command = ('Get-CimInstance Win32_Process | Where-Object { '
               '$_.Name -match "^strata.*\\.exe$" -or '
               '($_.Name -match "^python.*\\.exe$" -and '
               '$_.CommandLine -match "server.py|monitor_power.py|capture.py|reference.py|benchmark") '
               '} | Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json')
    raw = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command', command], text=True).strip()
    processes = json.loads(raw) if raw else []
    if isinstance(processes, dict):
        processes = [processes]
    for p in processes:
        cmd = p.get('CommandLine') or ''
        if p['ProcessId'] != os.getpid() and p['Name'].lower().startswith('python') and any(s in cmd for s in ('monitor_power.py', 'capture.py', 'reference.py', 'benchmark')):
            raise RuntimeError('Another measurement/queue process exists; inspect live commands before proceeding')
    servers = [p for p in processes if 'server.py' in (p.get('CommandLine') or '')]
    if len(servers) != 1:
        raise RuntimeError('Expected exactly one existing Strata server; no server is started or stopped here')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open('http://127.0.0.1:8080/health', timeout=10) as response:
        health = json.load(response)
    if not health.get('loaded') or health.get('max_context') != 131072 or health.get('model') != 'qwen3.8-flash-next-iq3_s':
        raise RuntimeError('Existing server must be loaded with the fixed model and 131072 context')
    # Use the live server command's config, never a historical PID or guessed profile.
    import shlex
    words = [w.strip('"') for w in shlex.split(servers[0]['CommandLine'], posix=False)]
    cfg = json.loads(Path(words[words.index('--config') + 1]).read_text())
    args = cfg['args']
    if cfg.get('gpu') != 0 or args[args.index('--max-context') + 1] != '131072' or args[args.index('--kv') + 1] != 'int8':
        raise RuntimeError('Unexpected GPU/context/KV settings')
    if any(cfg.get('env', {}).get(key) != '0' for key in ('STRATA_ROUTE_PRIOR', 'STRATA_ROUTE_TAIL_SKIP')):
        raise RuntimeError('Full expert routing must remain enabled')
    if args[args.index('--kv-resident') + 1] != '32768' or '0.1.55' not in cfg['exe'] or '0.1.55' not in cfg['cwd']:
        raise RuntimeError('Unexpected engine/Control or resident KV settings')
    # Compare inference settings, never persist credentials or hash credentials.
    clean = {k: v for k, v in cfg.items() if k not in ('api_key', 'log', 'host', 'port', 'open_browser')}
    digest = hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest()
    gpu_processes = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,process_name', '--format=csv,noheader'], text=True)
    strata_rows = [r for r in gpu_processes.splitlines() if 'strata.exe' in r.lower()]
    if len(strata_rows) != 1 or GPU not in strata_rows[0]:
        raise RuntimeError('Strata compute process must be on P100 only')
    telemetry = subprocess.check_output(['nvidia-smi', '--id=' + GPU, '--query-gpu=uuid,name,driver_version,power.limit,temperature.gpu,utilization.gpu,clocks.sm', '--format=csv'], text=True)
    return dict(health=health, inference_config_sha256=digest, processes=processes, gpu_telemetry=telemetry)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('group', choices=['intake', 'intake-exhaust'])
    parser.add_argument('--ready', action='store_true', help='Confirm physical setup and ongoing steady stress workload')
    parser.add_argument('--workload', required=True, help='Exact workload/command/settings, same for both groups; no credentials')
    parser.add_argument('--setup-notes', required=True, help='Case/shroud, fan placement, curve and exhaust speed; no credentials')
    parser.add_argument('--warmup-minutes', type=float, help='User-observed continuous warm-up after this fan setup')
    parser.add_argument('--heat-soaked', action='store_true', help='User explicitly reports heat soaked; duration may be unknown')
    parser.add_argument('--ambient-c', type=float, help='Measured room temperature; omit if unknown')
    args = parser.parse_args()
    import math
    if args.warmup_minutes is not None and (not math.isfinite(args.warmup_minutes) or args.warmup_minutes < 5):
        parser.error('If supplied, --warmup-minutes must be finite and at least five')
    if not args.ready or (args.warmup_minutes is None and not args.heat_soaked):
        parser.error('Confirm --ready and either observed --warmup-minutes or explicit --heat-soaked declaration')
    if args.ambient_c is not None and not math.isfinite(args.ambient_c):
        parser.error('Ambient must be finite')
    state = json.loads(STATE.read_text())
    if state['phase'] in ('running', 'error') or any(r['status'] != 'complete' for r in state['runs'].values()):
        raise SystemExit('Incomplete/error attempt requires explicit review; no automatic retry or state reset')
    labels = [f'{args.group}-{i}' for i in range(1, 4)]
    if all(state['runs'].get(label, {}).get('status') == 'complete' for label in labels):
        print('This setup already has three completed runs. Nothing started.')
        return
    order = json.loads((ROOT / 'manifest.json').read_text()).get('capture_order', ['intake-exhaust', 'intake'])
    if args.group == order[1] and not all(state['runs'].get(f'{order[0]}-{i}', {}).get('status') == 'complete' for i in range(1, 4)):
        raise SystemExit('Complete the three ' + order[0] + ' captures first')
    if (ROOT / 'state/STOP').exists():
        raise SystemExit('STOP flag present; no measurements started')
    with LOCK.open('x') as f:
        f.write(json.dumps(dict(pid=os.getpid(), host=socket.gethostname())))
    child = None
    measuring = False
    try:
        provenance = preflight()
        comparison = dict(workload=args.workload, inference_config_sha256=provenance['inference_config_sha256'])
        if state.get('comparison') and state['comparison'] != comparison:
            raise RuntimeError('Workload or inference configuration changed; do not pool these captures')
        state['comparison'] = comparison
        state.setdefault('sessions', []).append(dict(group=args.group, declarations=vars(args), provenance=provenance,
                                                     started_utc=datetime.now(timezone.utc).isoformat()))
        save(state)
        for label in labels:
            if state['runs'].get(label, {}).get('status') == 'complete':
                continue
            if (ROOT / 'state/STOP').exists():
                state.update(phase='paused', current=None)
                save(state)
                return
            if list((ROOT / 'results').glob(f'*-{label}.json')):
                raise RuntimeError('Existing evidence requires review: ' + label)
            live = preflight()
            if live['inference_config_sha256'] != comparison['inference_config_sha256']:
                raise RuntimeError('Inference configuration changed between runs')
            cmd = [sys.executable, '-u', str(MONITOR), '--label', label, '--gpu', GPU,
                   '--seconds', '600', '--interval', '1', '--output-dir', str(ROOT / 'results')]
            state.update(phase='running', current=label)
            entry = dict(group=args.group, status='starting', command=cmd, preflight=live)
            state['runs'][label] = entry
            save(state)
            measuring = True
            child = subprocess.Popen(cmd)
            entry.update(status='running', monitor_pid=child.pid)
            save(state)
            code = child.wait()
            child = None
            files = list((ROOT / 'results').glob(f'*-{label}.json'))
            if len(files) != 1:
                raise RuntimeError('Expected one raw summary: ' + label)
            result = json.loads(files[0].read_text())
            entry.update(status=result['status'], result=str(files[0].relative_to(ROOT)), exit_code=code)
            save(state)
            if code or result['status'] != 'complete' or result.get('duration_seconds', 0) < 599:
                raise RuntimeError('Failed/incomplete capture; review evidence before recovery')
            subprocess.run([sys.executable, str(ROOT / 'scripts/report.py')], check=True)
            measuring = False
        next_phase = 'awaiting-intake-setup' if args.group == 'intake-exhaust' else 'awaiting-exhaust-setup'
        state.update(phase='complete' if len(state['runs']) == 6 else next_phase, current=None)
        save(state)
        manifest_path = ROOT / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest.update(status=state['phase'], completed_captures=sum(r['status'] == 'complete' for r in state['runs'].values()),
                        completed_phase='complete' if state['phase'] == 'complete' else None)
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        print('Three captures finished. User-managed server/workload left running; change fans only between groups.')
    except BaseException as error:
        if child is not None and child.poll() is None:
            # Stop only the monitor we just created, never the server/workload.
            child.terminate()
            child.wait()
        if measuring and state.get('current'):
            state['runs'][state['current']]['status'] = 'review-required'
        state.update(phase='error', error=str(error) or type(error).__name__)
        save(state)
        raise
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
