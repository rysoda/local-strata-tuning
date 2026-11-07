"""Reviewed follow-ups, automatic nearby confirmations and smoke checks.
Stops on errors, never retries incomplete evidence or changes model quality.
"""
import argparse
import copy
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys

import run as core

ROOT = core.ROOT
bench = core.bench
SAFE = dict(p100_reserve=1400, ti_reserve=2304)
FOLLOWUPS = [
    dict(id='r06-trim32-p100-headroom', gpu=[0, 1], split='32', trim=True, p100_reserve=1400, reason='Only raise physical P100 reserve after low-memory warnings'),
    dict(id='r07-trim32-both-headroom', gpu=[0, 1], split='32', trim=True, **SAFE, reason='Then raise display-card reserve; isolate second budget'),
    dict(id='r08-trim28-safe', gpu=[0, 1], split='28', trim=True, **SAFE, reason='Neighbor split: 28 P100 / 20 display Main'),
    dict(id='r09-trim36-safe', gpu=[0, 1], split='36', trim=True, **SAFE, reason='Neighbor split: 36 P100 / 12 display Main'),
    dict(id='r10-reverse14-explicit', gpu=[1, 0], split='14', **SAFE, reason='Explicit reverse auto boundary, full dense copies if feasible'),
    dict(id='r11-reverse14-trim', gpu=[1, 0], split='14', trim=True, **SAFE, reason='Isolate trim at same reverse boundary'),
    dict(id='r12-trim32-mmap', gpu=[0, 1], split='32', trim=True, args=['--ple-io', 'mmap'], **SAFE, reason='One I/O change motivated by slow direct PLE probe'),
    dict(id='r13-trim32-prefill-pipe', gpu=[0, 1], split='32', trim=True, args=['--prefill-pipe', '1'], **SAFE, reason='One chunk-balancing change for decode/prefill tradeoff'),
    dict(id='r14-p100-safe-reference', gpu=0, **SAFE, reason='Fresh headroom-safe single-P100 reference for selection'),
]


def review(item):
    label = item['id']
    state = core.read(core.STATE)
    run = state['runs'][label]
    if run['phase'] != 'complete' or not run.get('metrics', {}).get('valid'):
        raise RuntimeError('Incomplete/invalid result: ' + label)
    health = core.read(ROOT / f'results/{label}.health.json')
    if health.get('max_context') != 262144 or health.get('model') != 'qwen3.8-flash-next-iq3_s':
        raise RuntimeError('Quality/context mismatch: ' + label)
    text = (ROOT / f'results/{label}.engine.log').read_text(encoding='utf-8', errors='replace')
    server = (ROOT / f'results/{label}.server.log').read_text(encoding='utf-8', errors='replace')
    if 'session is up (engine 0.1.57)' not in text or 'draft layer loaded' not in text or '--max-context 262144' not in text:
        raise RuntimeError('Version/context/MTP not verified: ' + label)
    if re.search(r'non-finite logits|fatal\s*:|watchdog[^\n]*restart|engine stopped unexpectedly', text + server, re.I):
        raise RuntimeError('Engine error requires review: ' + label)
    if '--control-vector' in text or '--cvec-mode' in text:
        raise RuntimeError('Unexpected projection: ' + label)
    cards = item['gpu'] if isinstance(item['gpu'], list) else [item['gpu']]
    grouped = {str(i): [] for i in cards}
    with (ROOT / f'results/{label}.hardware.csv').open() as f:
        for row in csv.DictReader(f, skipinitialspace=True):
            if row.get('index') in grouped:
                grouped[row['index']].append(row)
    hardware = {}
    for card, rows in grouped.items():
        if not rows:
            raise RuntimeError('Missing hardware evidence: ' + label)
        maximum = max(float(r['temperature.gpu']) for r in rows)
        active = sum(r['clocks_event_reasons.sw_thermal_slowdown'] == 'Active' or r['clocks_event_reasons.hw_thermal_slowdown'] == 'Active' for r in rows)
        free = min(float(r['memory.free [MiB]'].split()[0]) for r in rows)
        hardware[card] = dict(max_temp_c=maximum, thermal_active_samples=active, min_free_mib=free)
        if maximum >= 85 or active:
            raise RuntimeError('Thermal condition changed; review before next arm: ' + label)
    return dict(auto_trim='short of GPU memory:' in text, hardware=hardware,
                low_vram_warning='WARNING: only' in text,
                caveat='Observed sample minima include loading/graph/prefill buffers; not a guarantee beside other GPU apps')


def checkpoint(state):
    state['updated_utc'] = datetime.now(timezone.utc).isoformat()
    bench.save(core.STATE, state)
    rows = ['# 256K topology tuning — live results', '',
            'Full-quality IQ3_S, int8 KV, full experts; fixed noise-limited two-fan cooling. Quick screens are not significance claims.', '',
            '| Run | Phase | Decode tok/s | Prefill tok/s |', '|---|---|---:|---:|']
    for item in state.get('experiment_definitions', core.INITIAL + FOLLOWUPS):
        run = state['runs'].get(item['id'], {})
        metrics = run.get('metrics', {})
        d, p = metrics.get('decode'), metrics.get('prefill')
        rows.append(f"| {item['id']} | {run.get('phase', 'pending')} | {d:.2f} | {p:.2f} |" if d and p else f"| {item['id']} | {run.get('phase', 'pending')} | — | — |")
    rows += ['', 'Initial auto/1080-Main silently enabled dense stage trimming at K=35; it is not an untrimmed control. No model layers/experts were removed. Confirmation includes functional/tool/~119K and separate ~230K actual-token recall smokes.', '', 'State: `' + state['phase'] + '`.']
    (ROOT / 'RESULTS.md').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    manifest = core.read(ROOT / 'manifest.json')
    manifest.update(status=state['phase'], completed_benchmarks=sum(r.get('phase') == 'complete' for r in state['runs'].values()))
    bench.save(ROOT / 'manifest.json', manifest)


class ProcessTools:
    """Redirect only the shared runner's standard sanity entry point locally."""
    def __getattr__(self, name):
        return getattr(subprocess, name)

    def run(self, cmd, *args, **kwargs):
        if isinstance(cmd, list) and len(cmd) > 1 and Path(cmd[1]) == core.REPO / 'tools/sanity.py':
            cmd = [cmd[0], str(ROOT / 'scripts/sanity_combo.py'), *cmd[2:]]
        return subprocess.run(cmd, *args, **kwargs)


def execute(item, state, active):
    label = item['id']
    if label in state['runs']:
        if state['runs'][label]['phase'] != 'complete':
            raise RuntimeError('Incomplete attempt requires explicit review: ' + label)
        state.setdefault('reviews', {})[label] = review(item)
        return
    if (ROOT / 'state/STOP').exists():
        state.update(phase='paused', current=None)
        checkpoint(state)
        raise SystemExit('Paused between runs; no further work started')
    core.idle()
    core.check()
    if list((ROOT / 'results').glob(label + '.*')):
        raise RuntimeError('Orphan evidence requires review: ' + label)
    active['config'] = core.build(item)
    state.update(phase='followup-running', current=label)
    checkpoint(state)
    with (ROOT / f'results/{label}.hardware.csv').open('x') as stream:
        sampler = subprocess.Popen(['nvidia-smi', '--query-gpu=' + core.GPU_FIELDS, '--format=csv', '--loop=2'], stdout=stream, stderr=subprocess.STDOUT)
        try:
            bench.run_one(dict(id=label, args=[], env={}, sanity=item.get('sanity', False)), state)
        finally:
            if sampler.poll() is None:
                sampler.terminate()
            sampler.wait(timeout=15)
    state.setdefault('reviews', {})[label] = review(item)
    checkpoint(state)


def finish(state, candidate, definitions):
    a, reference, b = [state['runs'][k]['metrics'] for k in ('f01-candidate', 'f02-p100-reference', 'f03-candidate-repeat')]
    decode = statistics.mean([a['decode'], b['decode']])
    prefill = statistics.mean([a['prefill'], b['prefill']])
    score = (decode / reference['decode']) ** .55 * (prefill / reference['prefill']) ** .45
    chosen = 'f03-candidate-repeat' if score > 1 else 'f02-p100-reference'
    cfg = core.read(ROOT / f'configs/private/{chosen}.json')
    cfg['log'] = str(ROOT / 'results/recommended.engine.log')
    bench.save(ROOT / 'configs/private/recommended-256k.json', cfg)
    from tools.publish_configs import redact
    bench.save(ROOT / 'configs/shareable/recommended-256k.json', redact(cfg))
    text = ['# P100 x16 + 1080 Ti chipset x4 — 256K report', '',
            '**Completed:** targeted screens and nearby confirmation. Full quality, 262144 context; no speed projection. No significance or intelligence-equivalence claim.', '',
            '[Every measured arm](RESULTS.md) · [Plan and limitations](PLAN.md) · [Work log](NOTES.md)', '',
            '| Confirmation | Decode tok/s | Prefill tok/s | Smoke checks |', '|---|---:|---:|---|']
    for label in ('f01-candidate', 'f02-p100-reference', 'f03-candidate-repeat'):
        r = state['runs'][label]
        text.append(f"| {label} | {r['metrics']['decode']:.2f} | {r['metrics']['prefill']:.2f} | {r.get('sanity', 'not repeated')} |")
    text += ['', f'Candidate repeat mean: **{decode:.2f} decode / {prefill:.2f} prefill tok/s**. Against the intervening P100 reference: **{100*(decode/reference["decode"]-1):+.2f}% decode / {100*(prefill/reference["prefill"]-1):+.2f}% prefill**. Preference score ratio: {score:.4f} (55% decode / 45% prefill).', '',
             f'Selected profile derives from `{chosen}`. Candidate configuration: `{json.dumps(candidate)}`. A near-tie needs further confirmation; the score is a stated preference, not a confidence interval.', '',
             'Candidate and P100 reference each ran six standard functional/tool/32K/~119K checks plus a separate above-128K (~230K actual content tokens) recall check. Raw responses, actual API usage and prompt hashes are retained in the sanity artifacts. These do not validate all 256K workloads or comprehensive model quality. Generated code was never executed.', '',
             'Cooling fixed: open case, intake + exhaust, 75°C target, intake capped at 45%. Per-run UUID-labeled hardware samples and reviews are preserved; memory headroom is only for the observed desktop workload. No fan, power, clock, page-file or installed-profile changes. Original low-reserve baselines remain evidence, not deployment recommendations.', '',
             'Initial auto/1080-Main used automatic trim at K=35, so no claim of a clean no-trim control for that arm. mmap I/O results can depend on OS file-cache state. Pipeline and expert-peer arms were deliberately deferred given earlier instability/OOM and no evidence justifying risk on this constrained chipset arrangement. All performance results are for this topology/software, not future two-P100 x8+x8.', '',
             'Ready profile: `configs/private/recommended-256k.json` (credential-bearing, ignored) and redacted shareable copy. Launch with repository `tools/launch.py` using this campaign ID. Test servers are stopped by owned-run cleanup.']
    (ROOT / 'REPORT.md').write_text('\n'.join(text) + '\n', encoding='utf-8')
    state.update(phase='complete', current=None, selected_run=chosen)
    checkpoint(state)
    manifest = core.read(ROOT / 'manifest.json')
    manifest.update(completed_phase='complete', recommended_profile='recommended-256k.json')
    bench.save(ROOT / 'manifest.json', manifest)
    subprocess.run([sys.executable, str(core.REPO / 'tools/launch.py'), ROOT.name, '--check'], check=True)
    # Update only this campaign's dashboard row, leaving unrelated edits intact.
    dashboard = core.REPO / 'README.md'
    lines = dashboard.read_text(encoding='utf-8').splitlines()
    for i, line in enumerate(lines):
        if f'campaigns/{ROOT.name}/' in line and line.startswith('|'):
            cells = line.split('|')
            if len(cells) == 9:
                cells[4] = f" **Complete: {sum(r['phase'] == 'complete' for r in state['runs'].values())} benchmarks** "
                cells[5] = f" {min(a['decode'], b['decode']):.2f}–{max(a['decode'], b['decode']):.2f} " if chosen != 'f02-p100-reference' else f" {reference['decode']:.2f} "
                cells[6] = f" {min(a['prefill'], b['prefill']):.2f}–{max(a['prefill'], b['prefill']):.2f} " if chosen != 'f02-p100-reference' else f" {reference['prefill']:.2f} "
                cells[7] = ' Nearby confirmations and 256K recall smoke complete; see report for memory/quality limits '
                lines[i] = '|'.join(cells)
    dashboard.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    with (ROOT / 'NOTES.md').open('a', encoding='utf-8') as log:
        log.write(f"\n## Automatic final checkpoint\n\nCompleted all reviewed screens and nearby confirmations. Selected {chosen}; preference-score ratio {score:.4f}. Candidate/reference each passed 7/7 smoke checks including above-128K recall. No active owned test server remains. Raw evidence and limitations are in REPORT/RESULTS/state.\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Explicitly execute reviewed continuation, confirmations and smokes')
    args = parser.parse_args()
    if not args.run:
        core.check()
        print('Reviewed continuation prepared; nothing started. Use --run explicitly.')
        return
    state = core.read(core.STATE)
    if state['phase'] == 'complete':
        print('Campaign complete; nothing started.')
        return
    if state['phase'] == 'error' or any(r['phase'] != 'complete' for r in state['runs'].values()):
        raise SystemExit('Incomplete/error evidence requires explicit review; no automatic retry')
    if not all(state['runs'].get(i['id'], {}).get('phase') == 'complete' for i in core.INITIAL):
        raise SystemExit('Initial five screens must be complete')
    core.idle()
    core.check()
    with core.LOCK.open('x') as stream:
        stream.write(str(os.getpid()))
    bench.configure(ROOT, core.CONTROL)
    bench.checkpoint = checkpoint
    old_load, old_process = bench.load, bench.subprocess
    active = {}
    def load(path):
        return copy.deepcopy(active['config']) if Path(path) == ROOT / 'configs/private/baseline.json' else old_load(path)
    bench.load = load
    bench.subprocess = ProcessTools()
    try:
        state['runner_pid'] = os.getpid()
        state['experiment_definitions'] = core.INITIAL + FOLLOWUPS
        for item in core.INITIAL:
            state.setdefault('reviews', {})[item['id']] = review(item)
        checkpoint(state)
        for item in FOLLOWUPS:
            execute(item, state, active)
        reference = state['runs']['r14-p100-safe-reference']['metrics']
        candidates = FOLLOWUPS[1:]
        def score(item):
            m = state['runs'][item['id']]['metrics']
            return (m['decode'] / reference['decode']) ** .55 * (m['prefill'] / reference['prefill']) ** .45
        eligible = [i for i in candidates if all(v['min_free_mib'] >= 768 for v in state['reviews'][i['id']]['hardware'].values())]
        if not eligible:
            raise RuntimeError('No candidate has observed headroom; explicit review required')
        candidate = max(eligible, key=score)
        state['provisional_selection'] = dict(source_id=candidate['id'], score=score(candidate), candidate=candidate)
        confirms = [dict(candidate, id='f01-candidate', sanity=True),
                    dict(id='f02-p100-reference', gpu=0, sanity=True, **SAFE),
                    dict(candidate, id='f03-candidate-repeat', sanity=False)]
        state['experiment_definitions'] += confirms
        checkpoint(state)
        for item in confirms:
            execute(item, state, active)
        core.idle()
        finish(state, candidate, state['experiment_definitions'])
    except BaseException as error:
        if isinstance(error, SystemExit) and state.get('phase') == 'paused':
            return
        current = state.get('current')
        r = state['runs'].get(current, {})
        if r.get('benchmark_pid') and current:
            owned = str(ROOT / f'results/{current}.json')
            command = f'$p=Get-CimInstance Win32_Process -Filter "ProcessId={int(r["benchmark_pid"])}"; if ($p -and $p.CommandLine -like "*{owned}*") {{ taskkill /PID {int(r["benchmark_pid"])} /T /F }}'
            subprocess.run(['powershell.exe', '-NoProfile', '-Command', command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        state.update(phase='error', error=str(error) or type(error).__name__)
        checkpoint(state)
        raise
    finally:
        bench.load, bench.subprocess = old_load, old_process
        core.LOCK.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
