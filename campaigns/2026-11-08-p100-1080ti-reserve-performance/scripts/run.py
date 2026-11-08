"""Sequential performance search; --run required. Immutable unique attempts, no blind retries."""
import argparse
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import threading
import time

import mechanics as m
ROOT, REPO, bench = m.ROOT, m.REPO, m.bench
STATE = m.STATE
LEVELS = [256, 384, 512, 640, 768, 896, 1024]
REFERENCE = (1400, 2304)


def checkpoint(state):
    state['updated_utc'] = datetime.now(timezone.utc).isoformat()
    bench.save(STATE, state)
    lines = ['# Reserve performance — every attempt', '',
             '| Run | P100 MiB | Ti MiB | Status | Decode | Prefill |',
             '|---|---:|---:|---|---:|---:|']
    for label, item in state.get('definitions', {}).items():
        r = state['runs'].get(label, {})
        metric = r.get('metrics', {})
        out = state.get('outcomes', {}).get(label, {})
        d, p = metric.get('decode'), metric.get('prefill')
        lines.append(f"| {label} | {item['p100']} | {item['ti']} | {out.get('classification', r.get('phase', 'pending'))} | {d:.2f} | {p:.2f} |" if d and p else f"| {label} | {item['p100']} | {item['ti']} | {out.get('classification', r.get('phase', 'pending'))} | — | — |")
    lines += ['', 'Phase: **' + state['phase'] + '**. All raw samples, token counts and errors remain in results/. Quick screens are not significance claims.', '', '[Plan](PLAN.md) · [Report](REPORT.md)']
    (ROOT / 'RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    manifest = m.read(ROOT / 'manifest.json')
    manifest.update(status=state['phase'], completed_benchmarks=sum(r.get('phase') == 'complete' for r in state['runs'].values()), rejected_configurations=sum(not r['accepted'] for r in state.get('outcomes', {}).values()))
    bench.save(ROOT / 'manifest.json', manifest)


def watch(state, label, stop, guard):
    """Inherited progress/error guard plus hard per-phase deadlines (logging cannot hide a stall)."""
    nested_stop = threading.Event()
    nested = threading.Thread(target=m.original_watch, args=(state, label, nested_stop, guard), daemon=True)
    nested.start()
    phase, started = None, time.monotonic()
    try:
        while not stop.wait(3):
            current = state['runs'].get(label, {}).get('phase')
            if current != phase:
                phase, started = current, time.monotonic()
            limit = {'loading': 1200, 'benchmark-running': 2400, 'sanity-running': 3600}.get(phase)
            if limit and time.monotonic() - started > limit:
                guard['reason'] = 'hard-phase-timeout-' + phase
                m.kill_owned_benchmark(state, label)
                bench.stop_server(state['runs'][label].get('server_pid'))
                return
    finally:
        nested_stop.set()
        nested.join(timeout=15)


def run(state, active, p, t, label, sanity=False):
    print(f'{datetime.now().isoformat(timespec="seconds")} {label}: {p}/{t} MiB sanity={sanity}', flush=True)
    return m.execute(state, active, p, t, label, sanity=sanity)


def metrics_for(state, labels):
    valid = [state['runs'][k]['metrics'] for k in labels if state.get('outcomes', {}).get(k, {}).get('accepted')]
    if len(valid) != len(labels):
        return None
    return {k: statistics.mean(r[k] for r in valid) for k in ('decode', 'prefill')}


def rank(state, groups, reference):
    """Prefill within 2% of reference; then 60/40 geometric speed score. Tie prefers headroom."""
    ranked = []
    for pair, labels in groups.items():
        metric = metrics_for(state, labels)
        if metric and metric['prefill'] >= reference['prefill'] * .98:
            score = (metric['decode'] / reference['decode']) ** .6 * (metric['prefill'] / reference['prefill']) ** .4
            ranked.append(dict(pair=list(pair), labels=labels, metrics=metric, score=score))
    ranked.sort(key=lambda r: (r['score'], sum(r['pair'])), reverse=True)
    if not ranked:
        raise RuntimeError('No acceptable candidate; fresh reference/conditions need review')
    # Below 0.5% score separation is not persuasive in quick mode: prefer reserve headroom.
    near = [r for r in ranked if r['score'] >= ranked[0]['score'] * .995]
    winner = max(near, key=lambda r: sum(r['pair']))
    return [winner] + [r for r in ranked if r is not winner]


def report(state, final=False):
    lines = ['# VRAM reserve performance tuning', '',
             '**Status: ' + state['phase'] + '**', '',
             'Fixed engine/Control 0.1.57, IQ3_S, 262144 context, full experts, int8 KV/resident32768, MTP, trimmed 36/12 split. No speed projection. Startup and installed profiles unchanged.', '',
             '[All attempts](RESULTS.md) · [Plan and selection rule](PLAN.md) · [Work log](NOTES.md)', '']
    for key in ('p100_ranking', 'ti_ranking', 'joint_ranking'):
        if key in state:
            lines += ['## ' + key.replace('_', ' '), '', '| P100/Ti MiB | Mean decode | Mean prefill | Score | Runs |', '|---|---:|---:|---:|---|']
            for r in state[key]:
                lines.append(f"| {r['pair'][0]}/{r['pair'][1]} | {r['metrics']['decode']:.2f} | {r['metrics']['prefill']:.2f} | {r['score']:.4f} | {', '.join(r['labels'])} |")
            lines.append('')
    if 'final_pair' in state:
        lines += [f"## Selected confirmation pair: {state['final_pair'][0]}/{state['final_pair'][1]} MiB", '', '| Run | Decode | Prefill | Smoke |', '|---|---:|---:|---|']
        for label in state.get('confirmation_labels', []):
            r = state['runs'].get(label, {})
            metric = r.get('metrics')
            if metric:
                lines.append(f"| {label} | {metric['decode']:.2f} | {metric['prefill']:.2f} | {r.get('sanity', 'not scheduled')} |")
        if state.get('confirmation_summary'):
            s = state['confirmation_summary']
            lines += ['', f"Candidate mean: **{s['candidate']['decode']:.2f} decode / {s['candidate']['prefill']:.2f} prefill tok/s**. Nearby reference: **{s['reference']['decode']:.2f} / {s['reference']['prefill']:.2f}**. Changes: **{s['decode_pct']:+.2f}% decode / {s['prefill_pct']:+.2f}% prefill**.", '', 'Confirmation accepted: **' + str(s['accepted']) + '**.']
    if state.get('selection_note'):
        lines += ['', '**Selection caveat:** ' + state['selection_note']]
    if final:
        lines += ['', '**Recommended tested profile:** `configs/shareable/recommended.json` (private credential-bearing counterpart used locally). Validate with `python tools/launch.py ' + ROOT.name + ' --check`.', '', 'Owned test processes stopped. No automatic Startup change.']
    if state.get('error'):
        lines += ['', '## Execution stopped safely', '', state['error'], '', 'No blind retry. Preserve artifacts and inspect live ownership before explicit recovery. No new recommendation issued.']
    lines += ['', '## Limits', '', 'Quick screens and repeated medians are not statistical significance or an exhaustive mathematical optimum. Independent screening uses two starts per value; joint screening is provisional until confirmation. Prefill no-loss gate allows 2% screening noise. The 60/40 decode/prefill score and 0.5% headroom tie rule are declared before testing. Small gains may be noise.', '', 'Seven-check smoke sets include functional/tool behavior, ~119K and ~230K actual prompt tokens; they are not comprehensive intelligence equivalence. Generated code is never executed. Explicit reserve is not total unused VRAM. WDDM/display allocations and future workloads can change headroom. Actual token counts, every benchmark sample, cache-slot counts and per-card minimum free memory are retained in raw results/state. No precision, expert routing, context, reasoning, cooling or software changes.']
    (ROOT / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def finish(state, pair):
    from tools.publish_configs import redact
    cfg = m.config(*pair, 'recommended')
    bench.save(ROOT / 'configs/private/recommended.json', cfg)
    bench.save(ROOT / 'configs/shareable/recommended.json', redact(cfg))
    manifest = m.read(ROOT / 'manifest.json')
    manifest.update(recommended_profile='recommended.json', completed_phase='complete')
    bench.save(ROOT / 'manifest.json', manifest)
    subprocess.run([sys.executable, str(REPO / 'tools/launch.py'), ROOT.name, '--check'], check=True)
    m.idle()
    state.update(phase='complete', current=None, recommended_pair=list(pair))
    checkpoint(state)
    report(state, final=True)
    (ROOT / 'README.md').write_text('# VRAM reserve performance optimum\n\n**Complete.** Tested recommendation: **' + str(pair[0]) + '/' + str(pair[1]) + ' MiB**.\n\n[Final report](REPORT.md) · [Every run](RESULTS.md) · [Plan](PLAN.md) · [Manifest](manifest.json) · [Work log](NOTES.md)\n\nStartup unchanged. Completed runner refuses new work.\n', encoding='utf-8')
    dashboard = REPO / 'README.md'
    text = dashboard.read_text(encoding='utf-8')
    marker = '| [Reserve performance around 512 MiB]'
    s = state['confirmation_summary']
    selected = s['candidate'] if s['accepted'] else s['reference']
    text = '\n'.join((f"| [Reserve performance around 512 MiB](campaigns/{ROOT.name}/) | P100 CPU x16 / 1080 Ti chipset x4; fixed 36/12 | 0.1.57 / 0.1.57 | **Complete** | {selected['decode']:.2f} | {selected['prefill']:.2f} | Selected {pair[0]}/{pair[1]} MiB; see report for nearby reference and caveats; Startup unchanged |" if line.startswith(marker) else line) for line in text.splitlines()) + '\n'
    dashboard.write_text(text, encoding='utf-8')
    with (ROOT / 'NOTES.md').open('a', encoding='utf-8') as f:
        f.write('\n## Complete\n\nFinal pair ' + str(pair) + '. Confirmation and all attempts in report/state. Owned processes stopped; Startup unchanged.\n')
    subprocess.run([sys.executable, str(REPO / 'tools/publish_configs.py'), '--campaign', ROOT.name], check=True)
    subprocess.run([sys.executable, str(REPO / 'tools/validate_repository.py')], check=True)


def campaign(state, active):
    # Initial reference also checks functionality/long context before the search.
    if not run(state, active, *REFERENCE, 'control-original-reserves', sanity=True):
        raise RuntimeError('Fresh reference failed')
    refs = ['control-original-reserves']
    groups = {}
    for repeat, order in enumerate((LEVELS, list(reversed(LEVELS))), 1):
        for p in order:
            label = f'p100-{p}-r{repeat}'
            run(state, active, p, REFERENCE[1], label)
            groups.setdefault((p, REFERENCE[1]), []).append(label)
    run(state, active, *REFERENCE, 'reference-after-p100')
    refs.append('reference-after-p100')
    reference = metrics_for(state, refs)
    if not reference:
        raise RuntimeError('Reference changed/failed')
    groups[REFERENCE] = refs.copy()
    state['p100_ranking'] = rank(state, groups, reference)
    checkpoint(state); report(state)
    groups = {}
    for repeat, order in enumerate((list(reversed(LEVELS)), LEVELS), 1):
        for t in order:
            label = f'ti-{t}-r{repeat}'
            run(state, active, REFERENCE[0], t, label)
            groups.setdefault((REFERENCE[0], t), []).append(label)
    run(state, active, *REFERENCE, 'reference-after-ti')
    refs.append('reference-after-ti')
    reference = metrics_for(state, refs)
    if not reference:
        raise RuntimeError('Reference changed/failed')
    groups[REFERENCE] = refs.copy()
    state['ti_ranking'] = rank(state, groups, reference)
    checkpoint(state); report(state)
    p = state['p100_ranking'][0]['pair'][0]
    t = state['ti_ranking'][0]['pair'][1]
    # Independent winner, user hypothesis, nearest neighbors, and second-place intersection.
    pairs = [(p, t), (512, 512), (max(256, p - 128), t), (min(1400, p + 128), t), (p, max(256, t - 128)), (p, min(2304, t + 128)), (state['p100_ranking'][1]['pair'][0], state['ti_ranking'][1]['pair'][1])]
    groups = {REFERENCE: refs.copy()}
    for p, t in dict.fromkeys(pairs):
        label = f'joint-p{p}-t{t}'
        run(state, active, p, t, label)
        groups.setdefault((p, t), []).append(label)
    # Repeat the top two combinations before choosing the confirmation candidate.
    provisional = rank(state, groups, reference)
    for r in provisional[:2]:
        p, t = r['pair']
        label = f'joint-repeat-p{p}-t{t}'
        run(state, active, p, t, label)
        groups[(p, t)].append(label)
    state['joint_ranking'] = rank(state, groups, reference)
    pair = tuple(state['joint_ranking'][0]['pair'])
    state['final_pair'] = list(pair)
    checkpoint(state); report(state)
    confirmations = []
    for i in range(1, 4):
        label = f'confirm-candidate-{i}'
        if not run(state, active, *pair, label, sanity=i in (1, 3)):
            raise RuntimeError('Candidate confirmation failed; do not recommend')
        confirmations.append(label)
        label = f'confirm-reference-{i}'
        if not run(state, active, *REFERENCE, label, sanity=i == 1):
            raise RuntimeError('Nearby reference failed; do not recommend')
        confirmations.append(label)
        state['confirmation_labels'] = confirmations.copy()
        checkpoint(state); report(state)
    candidate = metrics_for(state, confirmations[::2])
    reference = metrics_for(state, confirmations[1::2])
    accepted = candidate['prefill'] >= reference['prefill'] * .98 and candidate['decode'] >= reference['decode'] * .98
    state['confirmation_summary'] = dict(candidate=candidate, reference=reference, decode_pct=100*(candidate['decode']/reference['decode']-1), prefill_pct=100*(candidate['prefill']/reference['prefill']-1), accepted=accepted)
    # If quick selection failed to reproduce, deliver a conservative validated reference, not a false win.
    if not accepted:
        pair = REFERENCE
        state['selection_note'] = 'Provisional winner failed nearby no-loss confirmation; recommend validated control instead.'
    checkpoint(state); report(state)
    finish(state, pair)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    state = m.read(STATE)
    if state['phase'] == 'complete':
        print('Complete; no work started.'); return
    m.check()
    if not args.run:
        print('Frozen inputs/topology verified; --run required.'); return
    if state['phase'] == 'error' or any(r['phase'] != 'complete' and not r.get('reviewed_skip') for r in state['runs'].values()):
        raise SystemExit('Ambiguous incomplete/error attempt requires explicit review; no retry')
    m.idle()
    with m.LOCK.open('x') as f:
        f.write(str(os.getpid()))
    baseline = m.read(ROOT / 'configs/private/baseline.json')
    bench.configure(ROOT, baseline['cwd'])
    bench.checkpoint = m.checkpoint = checkpoint
    m.original_watch = m.watch
    m.watch = watch
    old_load, old_process = bench.load, bench.subprocess
    active = {}
    bench.load = lambda path: copy.deepcopy(active['config']) if Path(path) == ROOT / 'configs/private/baseline.json' else old_load(path)
    bench.subprocess = m.ProcessTools(state)
    try:
        state['runner_pid'] = os.getpid()
        campaign(state, active)
    except BaseException as error:
        if isinstance(error, SystemExit) and state.get('phase') == 'paused':
            return
        if state.get('current'):
            m.kill_owned_benchmark(state, state['current'])
        state.update(phase='error', error=str(error) or type(error).__name__)
        checkpoint(state); report(state)
        raise
    finally:
        bench.load, bench.subprocess = old_load, old_process
        m.LOCK.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
