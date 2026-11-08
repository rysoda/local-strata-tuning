"""Adaptive reserve floor search. Default checks only; --run executes.
Expected allocation-boundary failures are preserved/reviewed outcomes, not retried.
Unexpected errors or quality failures pause. Startup is never modified.
"""
import argparse
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO))
from tools import benchmark as bench

STATE = ROOT / 'state/queue-state.json'
LOCK = ROOT / 'state/reserve.lock'
GPU_FIELDS = 'timestamp,index,uuid,temperature.gpu,clocks.sm,power.draw,utilization.gpu,memory.used,memory.free,pcie.link.gen.current,pcie.link.width.current,clocks_event_reasons.sw_thermal_slowdown,clocks_event_reasons.hw_thermal_slowdown'
ALLOCATION = re.compile(r'out of memory|cudaErrorMemoryAllocation|cudaMalloc[^\n]*failed|cublas[^\n]*(?:alloc|memory)|device buffers[^\n]*do not fit|expert cache: no room|too little free VRAM|fatal\s*:\s*Memory allocation failure', re.I)
BAD = re.compile(r'non-finite logits|fatal\s*:|watchdog[^\n]*restart|engine stopped unexpectedly', re.I)
LEVELS = [700, 512, 256, 128, 64, 0]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def check():
    baseline = read(ROOT / 'configs/private/baseline.json')
    frozen = read(ROOT / 'results/frozen-inputs.json')
    clean = {k: v for k, v in baseline.items() if k != 'api_key'}
    if hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest() != frozen['baseline_scientific_sha256']:
        raise RuntimeError('Frozen baseline changed')
    for item in frozen['files']:
        if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() != item['sha256']:
            raise RuntimeError('Frozen input changed: ' + item['path'])
    for item in frozen['model_files']:
        st = Path(item['path']).stat()
        if (st.st_size, st.st_mtime_ns) != (item['size'], item['mtime_ns']):
            raise RuntimeError('Model artifact changed: ' + item['path'])
    cards = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,pcie.link.width.current', '--format=csv,noheader,nounits'], text=True)
    expected = [('0', 'GPU-bab5c751-1e02-b6a7-cf6f-b6256c3a5999', '16'), ('1', 'GPU-7d8ccb39-60d5-bc52-5e38-1cb26b742a23', '4')]
    if [tuple(x.strip() for x in r.split(',')) for r in cards.strip().splitlines()] != expected:
        raise RuntimeError('Hardware topology changed; do not pool results')
    return baseline


def idle():
    command = ('Get-CimInstance Win32_Process | Where-Object { '
               '$_.Name -match "^strata.*\\.exe$|^betterbench" -or '
               '($_.Name -match "^python.*\\.exe$" -and $_.CommandLine -match '
               '"serve.server|server.py|strata_control.runtime|monitor_power.py|capture.py|reference.py|benchmark|scripts[\\\\/](run|continue).py") '
               '} | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json')
    raw = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command', command], text=True).strip()
    rows = json.loads(raw) if raw else []
    rows = [rows] if isinstance(rows, dict) else rows
    if any(r['ProcessId'] != os.getpid() for r in rows):
        raise RuntimeError('Competing inference/queue processes; nothing stopped')
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1', 8080)) == 0:
            raise RuntimeError('Port occupied; nothing stopped')


def config(p100, ti, label, projection=False):
    if not all(isinstance(v, int) and v >= 0 for v in (p100, ti)):
        raise ValueError('Reserves must be nonnegative integer MiB')
    cfg = read(ROOT / 'configs/private/baseline.json')
    a = cfg['args']
    a[a.index('--vram-reserve-mib') + 1] = str(p100)
    a[a.index('--vram-reserve-later-mib') + 1] = str(ti)
    cfg['log'] = str(ROOT / f'results/{label}.engine.log')
    assert cfg['gpu'] == [0, 1] and cfg['layer_split'] == '36'
    assert a[a.index('--max-context') + 1] == '262144'
    assert a[a.index('--kv') + 1] == 'int8' and a[a.index('--kv-resident') + 1] == '32768'
    assert cfg['drafting'] == 'mtp' and cfg['env']['STRATA_ROUTE_PRIOR'] == cfg['env']['STRATA_ROUTE_TAIL_SKIP'] == '0'
    assert not any('control-vector' in v or 'cvec' in v for v in a)
    if projection:
        original = read(ROOT / 'configs/private/original-installed-profile.snapshot')['args']
        for flag, count in [('--control-vector-scaled', 1), ('--control-vector-layer-range', 2), ('--cvec-mode', 1), ('--cvec-dir', 1)]:
            at = original.index(flag)
            a.extend(original[at:at + count + 1])
        vector = Path(a[a.index('--control-vector-scaled') + 1].rsplit(':', 1)[0])
        if not vector.is_file():
            raise RuntimeError('Existing projection vector missing; no substitute')
    return cfg


def checkpoint(state):
    state['updated_utc'] = datetime.now(timezone.utc).isoformat()
    bench.save(STATE, state)
    text = ['# Reserve minimization — live results', '', 'Fixed 36/12 split, 256K, IQ3_S, full experts, int8 KV. No arbitrary minimum free-memory criterion. Expected allocation boundaries are preserved, never retried.', '',
            '| Run | P100 MiB | 1080 MiB | Result | Decode | Prefill |', '|---|---:|---:|---|---:|---:|']
    for label, item in state.get('definitions', {}).items():
        r = state['runs'].get(label, {})
        m = r.get('metrics', {})
        outcome = state.get('outcomes', {}).get(label, {})
        d, p = m.get('decode'), m.get('prefill')
        text.append(f"| {label} | {item['p100']} | {item['ti']} | {outcome.get('classification', r.get('phase', 'pending'))} | {f'{d:.2f}' if d else '—'} | {f'{p:.2f}' if p else '—'} |")
    text += ['', 'Progress: `' + state['phase'] + '`. Floors are conditional on this hardware/software/desktop and the exercised requests, not a universal guarantee.', '',
             'The projection-enabled deployment check is separate and is not pooled into projection-free performance comparisons.']
    (ROOT / 'RESULTS.md').write_text('\n'.join(text) + '\n', encoding='utf-8')
    manifest = read(ROOT / 'manifest.json')
    manifest.update(status=state['phase'], completed_benchmarks=sum(r.get('phase') == 'complete' for r in state['runs'].values()), rejected_configurations=sum(not v.get('accepted') for v in state.get('outcomes', {}).values()))
    bench.save(ROOT / 'manifest.json', manifest)


def kill_owned_benchmark(state, label):
    run = state['runs'].get(label, {})
    for key, owned in [('benchmark_pid', str(ROOT / f'results/{label}.json')),
                       ('sanity_pid', str(ROOT / f'configs/private/{label}.json'))]:
        pid = run.get(key)
        if pid:
            command = f'$p=Get-CimInstance Win32_Process -Filter "ProcessId={int(pid)}"; if ($p -and $p.CommandLine -like "*{owned}*") {{ taskkill /PID {int(pid)} /T /F }}'
            subprocess.run(['powershell.exe', '-NoProfile', '-Command', command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def watch(state, label, stop, guard):
    previous, changed, phase_before = None, time.monotonic(), None
    while not stop.wait(3):
        phase = state['runs'].get(label, {}).get('phase')
        if phase not in ('benchmark-running', 'sanity-running'):
            previous, changed, phase_before = None, time.monotonic(), phase
            continue
        paths = [ROOT / f'results/{label}.{kind}.log' for kind in ('engine', 'server', 'bench', 'sanity')]
        signature = tuple((p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else (0, 0) for p in paths)
        if phase_before != phase or signature != previous:
            previous, changed, phase_before = signature, time.monotonic(), phase
        text = '\n'.join(p.read_text(encoding='utf-8', errors='replace') for p in paths[:2] if p.exists())
        if ALLOCATION.search(text):
            guard['reason'] = 'allocation-failure'
        elif BAD.search(text):
            guard['reason'] = 'unexpected-engine-error'
        elif time.monotonic() - changed > (1800 if phase == 'sanity-running' else 360):
            guard['reason'] = 'no-progress-for-1800s-during-smoke' if phase == 'sanity-running' else 'no-engine-or-benchmark-progress-for-360s'
        if guard.get('reason'):
            kill_owned_benchmark(state, label)
            return


class ProcessTools:
    def __init__(self, state):
        self.state = state

    def __getattr__(self, name):
        return getattr(subprocess, name)

    def run(self, cmd, *args, **kwargs):
        if isinstance(cmd, list) and len(cmd) > 1 and Path(cmd[1]) == REPO / 'tools/sanity.py':
            cmd = [cmd[0], str(ROOT / 'scripts/sanity_combo.py'), *cmd[2:]]
            timeout = kwargs.pop('timeout', None)
            proc = subprocess.Popen(cmd, *args, **kwargs)
            label = self.state['current']
            self.state['runs'][label]['sanity_pid'] = proc.pid
            checkpoint(self.state)
            try:
                return subprocess.CompletedProcess(cmd, proc.wait(timeout=timeout))
            except BaseException:
                if proc.poll() is None:
                    kill_owned_benchmark(self.state, label)
                    proc.wait(timeout=30)
                raise
        return subprocess.run(cmd, *args, **kwargs)


def inspect(label, item, state, guard):
    r = state['runs'][label]
    paths = [ROOT / f'results/{label}.{kind}.log' for kind in ('engine', 'server')]
    text = '\n'.join(p.read_text(encoding='utf-8', errors='replace') for p in paths if p.exists())
    # Explicit predeclared negative outcomes: keep raw failure/error and evidence.
    if r['phase'] != 'complete':
        allocation = ALLOCATION.search(text)
        if re.search(r'non-finite logits|watchdog[^\n]*restart', text, re.I):
            raise RuntimeError('Numerical/restart error requires explicit review: ' + label)
        stalled = guard.get('reason') in ('no-engine-or-benchmark-progress-for-360s', 'no-progress-for-1800s-during-smoke')
        if allocation or stalled:
            r.update(reviewed_skip=True, review_note='Predeclared reserve-boundary rejection; no retry. ' + (allocation.group(0) if allocation else guard['reason']))
            return dict(accepted=False, classification='allocation-boundary' if allocation else 'stall-boundary', guard=guard)
        raise RuntimeError('Unexpected failure/quality failure requires review: ' + label + ': ' + r.get('error', r['phase']))
    if BAD.search(text):
        raise RuntimeError('Non-finite/restart/fatal evidence despite result; pause: ' + label)
    if 'session is up (engine 0.1.57)' not in text or 'draft layer loaded' not in text:
        raise RuntimeError('Engine/MTP not verified: ' + label)
    if 'KV streaming: 32768 of 262144 cells' not in text or 'layer split: layers 0-35 (CUDA0), 36-47 (CUDA1)' not in text:
        raise RuntimeError('Actual KV residency/context or layer placement changed: ' + label)
    if text.count('engine started:') != 1:
        raise RuntimeError('Automatic retry/fallback must be reviewed: ' + label)
    health = read(ROOT / f'results/{label}.health.json')
    if health.get('max_context') != 262144 or health.get('model') != 'qwen3.8-flash-next-iq3_s':
        raise RuntimeError('Context/model changed')
    if '--control-vector' in text and not item.get('projection'):
        raise RuntimeError('Projection contaminated main comparison')
    effective = re.search(r'expert cache auto:.*?, (\d+) MiB reserved', text)
    if effective and int(effective.group(1)) != item['p100']:
        raise RuntimeError('Requested reserve was overwritten/clamped; review semantics')
    hardware = {}
    with (ROOT / f'results/{label}.hardware.csv').open() as f:
        rows = list(csv.DictReader(f, skipinitialspace=True))
    for card in ('0', '1'):
        samples = [x for x in rows if x.get('index') == card]
        if not samples:
            raise RuntimeError('Missing GPU telemetry')
        maximum = max(float(x['temperature.gpu']) for x in samples)
        flags = sum(x['clocks_event_reasons.sw_thermal_slowdown'] == 'Active' or x['clocks_event_reasons.hw_thermal_slowdown'] == 'Active' for x in samples)
        if maximum >= 85 or flags:
            raise RuntimeError('Thermal condition changed; pause')
        hardware[card] = dict(min_free_mib=min(float(x['memory.free [MiB]'].split()[0]) for x in samples), max_temp_c=maximum, thermal_active_samples=flags)
    m = r['metrics']
    if not m.get('valid'):
        raise RuntimeError('Missing exact requested samples')
    reference = state['runs'].get('control-original-reserves', {}).get('metrics')
    if reference and label != 'control-original-reserves' and not item.get('projection'):
        if m['decode'] < .75 * reference['decode'] or m['prefill'] < .75 * reference['prefill']:
            return dict(accepted=False, classification='severe-throughput-loss', hardware=hardware, note='Predeclared 25% loss threshold; cause is not proven paging')
    return dict(accepted=True, classification='passed-extended' if item.get('sanity') else 'passed-screen', hardware=hardware,
                first_effective_reserve_mib=int(effective.group(1)) if effective else None,
                first_slots=re.findall(r'expert cache (\d+) slots', text), later_slots=re.findall(r'CUDA1 runs layers.*?expert cache (\d+) slots', text))


def execute(state, active, p100, ti, label=None, sanity=False, projection=False):
    label = label or f'reserve-p{p100}-t{ti}'
    if label in state.get('outcomes', {}):
        return state['outcomes'][label]['accepted']
    if label in state['runs']:
        raise RuntimeError('Unreviewed existing attempt; preserve before recovery: ' + label)
    if (ROOT / 'state/STOP').exists():
        state.update(phase='paused', current=None)
        checkpoint(state)
        raise SystemExit('Paused between experiments')
    idle()
    check()
    if list((ROOT / 'results').glob(label + '.*')):
        raise RuntimeError('Orphan evidence requires review: ' + label)
    item = dict(p100=p100, ti=ti, sanity=sanity, projection=projection)
    state.setdefault('definitions', {})[label] = item
    active['config'] = config(p100, ti, label, projection)
    state.update(phase='running', current=label)
    checkpoint(state)
    done, guard = threading.Event(), {}
    watcher = threading.Thread(target=watch, args=(state, label, done, guard), daemon=True)
    with (ROOT / f'results/{label}.hardware.csv').open('x') as stream:
        sampler = subprocess.Popen(['nvidia-smi', '--query-gpu=' + GPU_FIELDS, '--format=csv', '--loop=2'], stdout=stream, stderr=subprocess.STDOUT)
        watcher.start()
        try:
            bench.run_one(dict(id=label, args=[], env={}, sanity=sanity), state)
        finally:
            done.set()
            watcher.join(timeout=20)
            if sampler.poll() is None:
                sampler.terminate()
            sampler.wait(timeout=15)
    outcome = inspect(label, item, state, guard)
    state.setdefault('outcomes', {})[label] = outcome
    checkpoint(state)
    return outcome['accepted']


def refine(failed, passed, test):
    """Smallest passing integer under the declared local monotonic assumption."""
    while passed - failed > 1:
        mid = (failed + passed) // 2
        if test(mid):
            passed = mid
        else:
            failed = mid
    return passed


def descend(upper, test):
    passed = upper
    for value in LEVELS:
        if value >= passed:
            continue
        if test(value):
            passed = value
            if value == 0:
                return 0
        else:
            return refine(value, passed, test)
    return passed


def finish(state, p100, ti, deployment):
    from tools.publish_configs import redact
    cfg = read(ROOT / 'configs/private/minimum-repeat.json')
    cfg['log'] = str(ROOT / 'results/recommended.engine.log')
    bench.save(ROOT / 'configs/private/recommended-minimum.json', cfg)
    bench.save(ROOT / 'configs/shareable/recommended-minimum.json', redact(cfg))
    if deployment:
        projected = read(ROOT / 'configs/private/deployment-projection-check.json')
        projected['log'] = str(ROOT / 'results/projection-compatible.engine.log')
        bench.save(ROOT / 'configs/private/projection-compatible.json', projected)
        bench.save(ROOT / 'configs/shareable/projection-compatible.json', redact(projected))
    labels = ['validated-joint-minimum', 'nearby-original-reserves', 'minimum-repeat']
    text = ['# Minimum reliable reserve — results', '', f'**Smallest validated pair found: P100 {p100} MiB / GTX 1080 Ti {ti} MiB.** Fixed 36/12 trimmed placement, 262144 context, IQ3_S, full experts, int8 KV, MTP unchanged.', '',
            'These are explicit reserve flags, NOT total unused VRAM: the installed engine separately budgets late CUDA allocations, later-stage windows and MTP/head. Search refines integer MiB under a local monotonic assumption; display activity, sampling/OS variance and future requests can move the boundary. This is an observed tested floor, not a universal guarantee.', '',
            '[Every attempt, including boundaries](RESULTS.md) · [Plan](PLAN.md) · [Work log](NOTES.md)', '',
            '| Nearby confirmation | Decode tok/s | Prefill tok/s | Smoke checks |', '|---|---:|---:|---|']
    for label in labels:
        r = state['runs'][label]
        text.append(f"| {label} | {r['metrics']['decode']:.2f} | {r['metrics']['prefill']:.2f} | {r.get('sanity')} |")
    text += ['', f'Independent benchmark screening floors: {json.dumps(state.get("screen_floors", {}))}. Extended checks at minimal candidate/control/repeat each include six standard functional/tool/~119K tests and one ~230K actual-content-token recall test. Actual API token counts and raw responses retained. No generated code executed.', '',
             f'Projection-enabled compatibility check: **{"passed" if deployment else "not accepted; do not deploy the minimum with projection"}**. This arm is separately labeled, not pooled with projection-free speeds. Smoke success is not quality equivalence.', '',
             'Acceptance does not require an arbitrary 1 GiB free VRAM. Allocation failures, predeclared no-progress boundary, severe throughput loss, retries, non-finite output and functional failures are preserved; unexpected failures pause. Smaller tested values and per-device observed minima are in state/results. No statistical-significance claim. No application/fan/power/clock/page-file/target precision/context changes.', '',
             '**Startup remains unchanged.** Ready scientific profile is configs/private/recommended-minimum.json with a redacted shareable copy. Projection-compatible copy exists only if that separate check passed. Test processes are stopped; original installed profiles and previous completed campaigns remain untouched.']
    (ROOT / 'REPORT.md').write_text('\n'.join(text) + '\n', encoding='utf-8')
    state.update(phase='complete', current=None, validated_pair=dict(p100_mib=p100, ti_mib=ti), deployment_projection_passed=deployment)
    checkpoint(state)
    manifest = read(ROOT / 'manifest.json')
    manifest.update(completed_phase='complete', recommended_profile='recommended-minimum.json')
    bench.save(ROOT / 'manifest.json', manifest)
    subprocess.run([sys.executable, str(REPO / 'tools/launch.py'), ROOT.name, '--check'], check=True)
    dashboard = REPO / 'README.md'
    lines = dashboard.read_text(encoding='utf-8').splitlines()
    repeated = [state['runs'][k]['metrics'] for k in ('validated-joint-minimum', 'minimum-repeat')]
    for index, line in enumerate(lines):
        if line.startswith('|') and f'campaigns/{ROOT.name}/' in line:
            cells = line.split('|')
            if len(cells) == 9:
                cells[4] = ' **Complete: validated reserve floor** '
                cells[5] = f" {min(x['decode'] for x in repeated):.2f}–{max(x['decode'] for x in repeated):.2f} "
                cells[6] = f" {min(x['prefill'] for x in repeated):.2f}–{max(x['prefill'] for x in repeated):.2f} "
                cells[7] = f' P100 {p100} / 1080 Ti {ti} MiB explicit reserve; see report for boundary/compatibility limits; Startup unchanged '
                lines[index] = '|'.join(cells)
    dashboard.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    with (ROOT / 'NOTES.md').open('a', encoding='utf-8') as log:
        log.write(f'\n## Final checkpoint\n\nValidated explicit reserve pair {p100}/{ti} MiB; separate projected compatibility passed={deployment}. All attempted boundaries and actual token counts preserved. Startup unchanged; owned test processes stopped. See REPORT/RESULTS/state for limits.\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if not args.run:
        check()
        print('Frozen inputs/topology verified; no experiment launched.')
        return
    state = read(STATE)
    if state['phase'] == 'complete':
        print('Complete; no work started.')
        return
    if state['phase'] == 'error' or any(r['phase'] != 'complete' and not r.get('reviewed_skip') for r in state['runs'].values()):
        raise SystemExit('Incomplete/error attempt requires review; no automatic retry')
    idle()
    check()
    with LOCK.open('x') as stream:
        stream.write(str(os.getpid()))
    baseline = read(ROOT / 'configs/private/baseline.json')
    bench.configure(ROOT, baseline['cwd'])
    bench.checkpoint = checkpoint
    old_load, old_process = bench.load, bench.subprocess
    active = {}
    bench.load = lambda path: copy.deepcopy(active['config']) if Path(path) == ROOT / 'configs/private/baseline.json' else old_load(path)
    bench.subprocess = ProcessTools(state)
    try:
        state['runner_pid'] = os.getpid()
        if not execute(state, active, 1400, 2304, 'control-original-reserves', sanity=True):
            raise RuntimeError('High-reserve quality reference failed; pause, do not search')
        p = descend(1400, lambda value: execute(state, active, value, 2304))
        t = descend(2304, lambda value: execute(state, active, 1400, value))
        state['screen_floors'] = dict(p100_mib=p, ti_mib=t)
        checkpoint(state)
        # Validate the P100 floor with a well-reserved display card first. If an
        # actual allocation boundary appears in extended checks, refine upward.
        def pvalid(value):
            return execute(state, active, value, 2304, f'extended-p{value}-t2304', sanity=True)
        if not pvalid(p):
            p = refine(p, 1400, pvalid)
        def tvalid(value):
            return execute(state, active, p, value, f'extended-p{p}-t{value}', sanity=True)
        if not tvalid(t):
            t = refine(t, 2304, tvalid)
        if not execute(state, active, p, t, 'validated-joint-minimum', sanity=True):
            raise RuntimeError('Joint minimum did not reproduce; review variability')
        if not execute(state, active, 1400, 2304, 'nearby-original-reserves', sanity=True):
            raise RuntimeError('Nearby reference changed; pause')
        if not execute(state, active, p, t, 'minimum-repeat', sanity=True):
            raise RuntimeError('Minimum did not reproduce; do not recommend')
        deployment = execute(state, active, p, t, 'deployment-projection-check', sanity=True, projection=True)
        idle()
        finish(state, p, t, deployment)
    except BaseException as error:
        if isinstance(error, SystemExit) and state.get('phase') == 'paused':
            return
        if state.get('current'):
            kill_owned_benchmark(state, state['current'])
        state.update(phase='error', error=str(error) or type(error).__name__)
        checkpoint(state)
        raise
    finally:
        bench.load, bench.subprocess = old_load, old_process
        LOCK.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
