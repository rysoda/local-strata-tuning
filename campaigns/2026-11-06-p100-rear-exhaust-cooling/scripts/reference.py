"""Three sequential passive 600-second captures. No workload/GPU changes."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
STATE = ROOT / 'state/reference-state.json'
LOCK = ROOT / 'state/reference.lock'
MONITOR = REPO / 'campaigns/2026-11-03-p100-open-case-cooling/scripts/monitor_power.py'
GPU = 'GPU-bab5c751-1e02-b6a7-cf6f-b6256c3a5999'


def save(state):
    state['updated_utc'] = datetime.now(timezone.utc).isoformat()
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    temp.replace(STATE)


def main():
    with LOCK.open('x') as f:
        f.write(str(os.getpid()))
    state = {'phase': 'planned', 'pid': os.getpid(), 'runs': {},
             'user_report': 'Stress test running about five minutes before request; user considers heat soaked',
             'workload_control': 'User-managed; exact invocation not captured',
             'gpu_uuid': GPU, 'seconds_per_run': 600, 'interval_seconds': 1}
    try:
        if STATE.exists():
            state = json.loads(STATE.read_text())
            if state['phase'] == 'complete':
                print('Reference already complete; no work started.', flush=True)
                return
            raise RuntimeError('Existing incomplete reference requires explicit review; no automatic retry.')
        existing = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command',
            'Get-CimInstance Win32_Process | Where-Object { $_.Name -match "^python.*\\.exe$" -and $_.CommandLine -match "monitor_power.py" } | Select-Object ProcessId,CommandLine | ConvertTo-Json'], text=True).strip()
        if existing:
            raise RuntimeError('Another monitor exists: ' + existing)
        save(state)
        for i in range(1, 4):
            if (ROOT / 'state/STOP').exists():
                state.update(phase='paused', current=None)
                save(state)
                return
            label = f'rear-pull-reference-{i}'
            # Never silently reuse evidence from a failed or interrupted attempt.
            if list((ROOT / 'results').glob(f'*-{label}.json')):
                raise RuntimeError('Evidence already exists for ' + label)
            cmd = [sys.executable, '-u', str(MONITOR), '--label', label,
                   '--gpu', GPU, '--seconds', '600', '--interval', '1',
                   '--output-dir', str(ROOT / 'results')]
            state.update(phase='running', current=label)
            state['runs'][label] = {'status': 'starting', 'command': cmd}
            save(state)
            proc = subprocess.Popen(cmd)
            state['runs'][label].update(status='running', monitor_pid=proc.pid)
            save(state)
            code = proc.wait()
            files = list((ROOT / 'results').glob(f'*-{label}.json'))
            if len(files) != 1:
                raise RuntimeError(f'{label}: expected exactly one result, found {len(files)}')
            result = json.loads(files[0].read_text())
            state['runs'][label].update(status=result['status'], result=str(files[0].relative_to(ROOT)),
                                        average_power_w=result.get('average_power_w'), exit_code=code)
            save(state)
            if code or result['status'] != 'complete' or result.get('duration_seconds', 0) < 599:
                raise RuntimeError(label + ': incomplete/failed; queue paused for review')
        state.update(phase='complete', current=None)
        save(state)
        print('All three reference captures complete. Stress workload left running.', flush=True)
    except Exception as error:
        state.update(phase='error', error=str(error))
        save(state)
        raise
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
