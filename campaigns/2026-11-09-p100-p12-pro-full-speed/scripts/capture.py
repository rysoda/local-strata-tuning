"""Three read-only 600-second cooling surveys; never starts/stops the workload."""
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'state/queue-state.json'
SERVER_CONFIG = ROOT.parent / '2026-11-09-p100-new-fan/configs/private/p100.runtime.json'
LOCK = ROOT / 'state/capture.lock'
GPU = 'GPU-bab5c751-1e02-b6a7-cf6f-b6256c3a5999'
FIELDS = ['power.draw', 'power.limit', 'temperature.gpu', 'utilization.gpu',
          'utilization.memory', 'clocks.sm', 'clocks.mem', 'memory.used', 'pstate',
          'clocks_event_reasons.sw_power_cap', 'clocks_event_reasons.sw_thermal_slowdown',
          'clocks_event_reasons.hw_thermal_slowdown', 'clocks_event_reasons.hw_power_brake_slowdown']
KEYS = ['power_w', 'power_limit_w', 'temperature_c', 'utilization_percent',
        'memory_utilization_percent', 'sm_clock_mhz', 'memory_clock_mhz', 'memory_used_mib',
        'pstate', 'sw_power_cap', 'sw_thermal_slowdown', 'hw_thermal_slowdown', 'hw_power_brake_slowdown']


def stamp():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temp.replace(path)


def query():
    raw = subprocess.check_output(['nvidia-smi', '--id=' + GPU,
        '--query-gpu=' + ','.join(FIELDS), '--format=csv,noheader,nounits'], text=True, timeout=10)
    values = next(csv.reader(raw.splitlines(), skipinitialspace=True))
    if len(values) != len(KEYS):
        raise RuntimeError('Unexpected NVIDIA telemetry shape')
    row = dict(zip(KEYS, values))
    for key in KEYS[:8]:
        row[key] = float(row[key])
        if not math.isfinite(row[key]):
            raise RuntimeError('Unavailable numeric telemetry: ' + key)
    if any(row[k] not in ('Active', 'Not Active') for k in KEYS[9:]):
        raise RuntimeError('Unavailable throttle telemetry')
    return row


def preflight():
    cmd = ('Get-CimInstance Win32_Process | Where-Object { $_.Name -match "^strata.*\\.exe$" -or '
           '($_.Name -match "^python.*\\.exe$" -and $_.CommandLine -match "server.py|capture.py|monitor_power.py|reference.py|benchmark") } '
           '| Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json')
    raw = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command', cmd], text=True)
    processes = json.loads(raw) if raw.strip() else []
    if isinstance(processes, dict):
        processes = [processes]
    for p in processes:
        command = p.get('CommandLine') or ''
        if p['ProcessId'] != os.getpid() and p['Name'].lower().startswith('python') and any(x in command for x in ('capture.py', 'monitor_power.py', 'reference.py', 'benchmark')):
            raise RuntimeError('Another measurement queue exists; inspect ownership')
    servers = [p for p in processes if 'server.py' in (p.get('CommandLine') or '')]
    if len(servers) != 1:
        raise RuntimeError('Expected exactly one live server')
    words = [s.strip('"') for s in shlex.split(servers[0]['CommandLine'], posix=False)]
    config_path = Path(words[words.index('--config') + 1])
    if config_path.resolve() != SERVER_CONFIG.resolve():
        raise RuntimeError('Not this campaign server')
    cfg = json.loads(config_path.read_text())
    args = cfg['args']
    if cfg['gpu'] != 0 or '0.1.57' not in cfg['exe'] or '0.1.57' not in cfg['cwd']:
        raise RuntimeError('Unexpected GPU or software')
    for flag, expected in [('--max-context', '131072'), ('--kv', 'int8'), ('--kv-resident', '32768')]:
        if args[args.index(flag) + 1] != expected:
            raise RuntimeError('Unexpected setting: ' + flag)
    if any(cfg['env'].get(k) != '0' for k in ('STRATA_ROUTE_PRIOR', 'STRATA_ROUTE_TAIL_SKIP')):
        raise RuntimeError('Full expert routing required')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open('http://127.0.0.1:8080/health', timeout=10) as response:
        health = json.load(response)
    if not health.get('loaded') or health.get('max_context') != 131072 or health.get('model') != cfg['model_name']:
        raise RuntimeError('Unexpected server health')
    compute = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,process_name', '--format=csv,noheader'], text=True)
    rows = [r for r in compute.splitlines() if 'strata.exe' in r.lower()]
    if len(rows) != 1 or GPU not in rows[0]:
        raise RuntimeError('Inference must remain P100 only')
    clean = {k: v for k, v in cfg.items() if k not in ('api_key', 'log', 'host', 'port', 'open_browser')}
    return dict(health=health, processes=processes, telemetry=query(),
                inference_config_sha256=hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest())


def capture(label):
    base = ROOT / 'results' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ') + '-' + label)
    csv_path = Path(str(base) + '.csv')
    result_path = Path(str(base) + '.json')
    result = dict(label=label, status='running', started_utc=stamp(), gpu_uuid=GPU,
                  requested_seconds=600, interval_seconds=1, csv_file=csv_path.name)
    save(result_path, result)
    samples = []
    start = None
    try:
        with csv_path.open('x', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=['utc', 'elapsed_seconds'] + KEYS)
            writer.writeheader()
            while True:
                data = query()
                now = time.monotonic()
                if start is None:
                    start = now
                row = dict(utc=stamp(), elapsed_seconds=min(now - start, 600), **data)
                samples.append(row)
                writer.writerow(row)
                stream.flush()
                remaining = 600 - (time.monotonic() - start)
                if remaining <= 0:
                    break
                time.sleep(min(remaining, max(0, 1 - (time.monotonic() - now))))
                if time.monotonic() - start >= 600:
                    break
        result['status'] = 'complete'
    except BaseException as error:
        result.update(status='failed', error=str(error) or type(error).__name__)
        raise
    finally:
        duration = min(time.monotonic() - start, 600) if start is not None else 0
        weights = [(samples[i+1]['elapsed_seconds'] if i+1 < len(samples) else duration) - r['elapsed_seconds'] for i, r in enumerate(samples)]
        stats = {}
        for key in KEYS[:8]:
            values = [r[key] for r in samples]
            if values and duration:
                mean = sum(v*w for v, w in zip(values, weights)) / duration
                stats[key] = dict(mean=mean, min=min(values), max=max(values),
                                 sd=math.sqrt(sum(w*(v-mean)**2 for v, w in zip(values, weights))/duration))
        flags = {k: sum(w for r, w in zip(samples, weights) if r[k] == 'Active') / duration * 100
                 for k in KEYS[9:]} if duration else {}
        result.update(finished_utc=stamp(), duration_seconds=duration, sample_count=len(samples),
                      max_sample_gap_seconds=max(weights, default=None), metrics=stats,
                      throttle_active_percent=flags,
                      energy_wh=stats['power_w']['mean'] * duration / 3600 if stats else None)
        save(result_path, result)
    return str(result_path.relative_to(ROOT))


def report(state):
    lines = ['# ARCTIC P12 Pro — P100 cooling survey', '',
             f"Completed: {sum(r['status'] == 'complete' for r in state['runs'].values())}/3 ten-minute captures.", '',
             'Fan fixed at 100%, approximately 2900 RPM (user reported), continuing the extractor setup. Heat-soak duration after changing speed is unknown; initial settling is retained, not discarded. Fan RPM is not measured by NVIDIA telemetry. Ambient, case/shroud and exact stress settings unknown.', '',
             '| Run | Temp mean/max °C | SM clock mean/max MHz | Board power mean W | GPU mean % |',
             '| --- | --- | --- | --- | --- |']
    details = []
    for label, entry in state['runs'].items():
        if entry['status'] != 'complete':
            continue
        r = json.loads((ROOT / entry['result']).read_text())
        m = r['metrics']
        lines.append(f"| {label} | {m['temperature_c']['mean']:.2f}/{m['temperature_c']['max']:.0f} | {m['sm_clock_mhz']['mean']:.2f}/{m['sm_clock_mhz']['max']:.0f} | {m['power_w']['mean']:.2f} | {m['utilization_percent']['mean']:.2f} |")
        details += ['', f"{label}: {r['sample_count']} samples; max gap {r['max_sample_gap_seconds']:.2f}s; throttle-active percentages: {json.dumps(r['throttle_active_percent'])}.", '']
    lines += details
    lines += ['', 'CSV/JSON under results retain all samples, min/max/SD, memory clocks/utilization/usage, P-state, power limit and power/thermal throttle flags. Means and flag percentages use time-weighted sample-and-hold; extrema are sampled, not continuous. External fan power excluded. Three sequential runs are not independent controlled trials; no inference-speed or quality claim, nor controlled comparison with historical fans. User-managed workload/server left untouched.']
    (ROOT / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    state = json.loads(STATE.read_text())
    if state['phase'] in ('running', 'error') or any(r['status'] != 'complete' for r in state['runs'].values()):
        raise SystemExit('Incomplete attempt requires explicit review, not automatic retry')
    if state['phase'] == 'complete':
        print('Already complete; nothing started.')
        return
    if (ROOT / 'state/STOP').exists():
        raise SystemExit('STOP flag present')
    with LOCK.open('x') as f:
        json.dump(dict(pid=os.getpid(), started_utc=stamp()), f)
    try:
        for i in range(1, 4):
            label = f'p12-pro-100pct-{i}'
            if state['runs'].get(label, {}).get('status') == 'complete':
                continue
            if (ROOT / 'state/STOP').exists():
                state.update(phase='paused', current=None)
                save(STATE, state)
                return
            live = preflight()
            digest = live['inference_config_sha256']
            if state.get('inference_config_sha256', digest) != digest:
                raise RuntimeError('Inference configuration changed')
            if list((ROOT / 'results').glob('*-' + label + '.json')):
                raise RuntimeError('Existing evidence requires review')
            state.update(phase='running', current=label, supervisor_pid=os.getpid(), inference_config_sha256=digest)
            state['runs'][label] = dict(status='running', started_utc=stamp(), preflight=live)
            save(STATE, state)
            print(stamp(), 'Starting', label, flush=True)
            result = capture(label)
            metadata = json.loads((ROOT / result).read_text())
            if metadata['status'] != 'complete' or metadata['duration_seconds'] != 600 or metadata['sample_count'] < 2:
                raise RuntimeError('Incomplete survey requires review')
            state['runs'][label].update(status='complete', result=result, finished_utc=stamp())
            save(STATE, state)
            report(state)
        state.update(phase='complete', current=None, finished_utc=stamp())
        save(STATE, state)
        path = ROOT / 'manifest.json'
        manifest = json.loads(path.read_text())
        manifest.update(status='complete', completed_captures=3, completed_phase='complete')
        save(path, manifest)
        print('Three surveys complete; workload/server left running.', flush=True)
    except BaseException as error:
        if state.get('current'):
            state['runs'][state['current']]['status'] = 'review-required'
        state.update(phase='error', error=str(error) or type(error).__name__)
        save(STATE, state)
        raise
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
