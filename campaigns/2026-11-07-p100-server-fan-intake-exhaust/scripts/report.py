"""Build cooling tables from preserved raw CSVs; never alter evidence."""
import csv
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
METRICS = [('temperature_c', 'Temp °C'), ('sm_clock_mhz', 'SM clock MHz'),
           ('power_w', 'Board W'), ('utilization_percent', 'GPU %')]


def metrics(rows, duration):
    times = [float(r['elapsed_seconds']) for r in rows]
    if not times or duration <= 0 or times[0] != 0 or any(b < a for a, b in zip(times, times[1:])) or times[-1] > duration:
        raise ValueError('Invalid sampling timeline')
    weights = [b - a for a, b in zip(times, times[1:] + [duration])]
    out = {'duration_seconds': duration, 'samples': len(rows), 'max_gap_s': max(weights)}
    for key, _ in METRICS:
        values = [float(r[key]) for r in rows]
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Missing/nonfinite telemetry: ' + key)
        mean = sum(v * w for v, w in zip(values, weights)) / duration
        out[key] = {'mean': mean, 'min': min(values), 'max': max(values),
                    'sd': math.sqrt(sum(w * (v - mean) ** 2 for v, w in zip(values, weights)) / duration)}
    out['energy_wh'] = out['power_w']['mean'] * duration / 3600
    return out


def fmt(v):
    return '—' if v is None else f'{v:.2f}'


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(str(c) for c in row) + ' |' for row in rows])


def main():
    state = json.loads((ROOT / 'state/queue-state.json').read_text())
    runs = []
    for label, entry in state['runs'].items():
        if entry.get('status') != 'complete':
            continue
        path = ROOT / entry['result']
        meta = json.loads(path.read_text())
        if meta['status'] != 'complete':
            raise ValueError('State/evidence mismatch: ' + label)
        with (path.parent / meta['csv_file']).open(newline='') as f:
            stats = metrics(list(csv.DictReader(f)), meta['duration_seconds'])
        runs.append(dict(label=label, group=entry['group'], result=path.relative_to(ROOT).as_posix(), **stats))
    text = ['# Server intake fan: cooling comparison', '',
            f'Completed captures: **{len(runs)}/6**.' + (' Both groups complete; see [final comparison and historical references](COMPARISON.md).' if len(runs) == 6 else ' No comparative conclusion until both groups have three valid runs.'), '',
            'A = 120×38 mm nominal 4000 RPM intake only. B = same intake plus exhaust. Intake curve reaches 100% at 75°C (user-reported; actual RPM not measured).', '',
            'Means/within-run SD are time-weighted sample-and-hold. Max/min are observed samples, not continuous extrema. Board power excludes external fan power. All temperatures are absolute GPU temperatures; ambient-adjusted comparisons require ambient measurements.', '']
    headers = ['Run']
    for _, name in METRICS:
        headers += [name + ' mean', 'min', 'max', 'SD']
    text += ['## Per-run telemetry', '', table(headers, [[r['label']] + [fmt(r[k][s]) for k, _ in METRICS for s in ('mean', 'min', 'max', 'sd')] for r in runs]), '',
             '## Sampling and energy', '', table(['Run', 'Seconds', 'Samples', 'Max gap s', 'Board Wh', 'Raw summary'],
             [[r['label'], fmt(r['duration_seconds']), r['samples'], fmt(r['max_gap_s']), fmt(r['energy_wh']), f"[{r['result']}]({r['result']})"] for r in runs]), '']
    grouped = {g: [r for r in runs if r['group'] == g] for g in ('intake', 'intake-exhaust')}
    text += ['## Group summaries', '', 'Across-run SD/range describe repeatability of run means, not independent sample uncertainty.', '']
    group_rows = []
    for g, members in grouped.items():
        for key, name in METRICS:
            values = [r[key]['mean'] for r in members]
            if values:
                group_rows.append([g, len(members), name, fmt(statistics.mean(values)),
                                   fmt(statistics.stdev(values) if len(values) > 1 else None),
                                   fmt(max(values) - min(values)), fmt(max(r[key]['max'] for r in members))])
    text += [table(['Setup', 'n', 'Metric', 'Mean of run means', 'Across-run SD', 'Run-mean range', 'Highest observed'], group_rows), '',
             '## Differences between consecutive runs within each setup', '', 'Signed difference = later run minus previous run.', '']
    differences = []
    for members in grouped.values():
        for a, b in zip(members, members[1:]):
            for key, name in METRICS:
                av, bv = a[key]['mean'], b[key]['mean']
                differences.append([f"{b['label']} − {a['label']}", name, fmt(bv-av), fmt(100*(bv-av)/av if av else None)])
    text += [table(['Comparison', 'Mean metric', 'Difference', '% of previous'], differences), '', '## Exhaust effect (B − A)', '']
    if all(len(m) == 3 for m in grouped.values()):
        comparisons = []
        for key, name in METRICS:
            a, b = [statistics.mean(r[key]['mean'] for r in grouped[g]) for g in grouped]
            max_a, max_b = [max(r[key]['max'] for r in grouped[g]) for g in grouped]
            comparisons.append([name, fmt(a), fmt(b), fmt(b-a), fmt(100*(b-a)/a if a else None), fmt(max_b-max_a)])
        text += [table(['Metric', 'A mean', 'B mean', 'Mean Δ', 'Mean Δ %', 'Observed max Δ'], comparisons)]
    else:
        text += ['Pending three completed runs per setup.']
    text += ['', 'Temperature percentage deltas use °C numerically and are not thermodynamic ratios; use absolute °C differences for interpretation. Runs are sequential and not paired independent trials. Fan-curve feedback, ambient drift, workload variation and warm-up can confound results. Cooling telemetry is not an inference-speed benchmark or quality test.', '',
             'Setup/workload/ambient declarations and commands are preserved in [queue state](state/queue-state.json). Incomplete attempts remain in state/results and are excluded, not silently retried.']
    (ROOT / 'REPORT.md').write_text('\n'.join(text) + '\n', encoding='utf-8')
    (ROOT / 'results/analysis.json').write_text(json.dumps(runs, indent=2) + '\n')
    print(f'Report updated: {len(runs)}/6 captures')


if __name__ == '__main__':
    main()
