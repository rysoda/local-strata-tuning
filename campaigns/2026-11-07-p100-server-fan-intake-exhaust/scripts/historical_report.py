"""Read yesterday's original evidence and produce a separate historical reference."""
import csv
import hashlib
import json
from pathlib import Path
import statistics

from report import METRICS, fmt, metrics, table

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / '2026-11-06-p100-rear-exhaust-cooling'


def main():
    runs = []
    for path in sorted((SOURCE / 'results').glob('*-rear-pull-reference-*.json')):
        meta = json.loads(path.read_text())
        if meta['status'] != 'complete' or meta['duration_seconds'] != 600:
            raise ValueError('Unexpected incomplete historical result: ' + str(path))
        raw = path.parent / meta['csv_file']
        with raw.open(newline='') as f:
            stats = metrics(list(csv.DictReader(f)), meta['duration_seconds'])
        for key, stored in [('temperature_c', 'average_temperature_c'), ('sm_clock_mhz', 'average_sm_clock_mhz'), ('power_w', 'average_power_w'), ('utilization_percent', 'average_utilization_percent')]:
            if abs(stats[key]['mean'] - meta[stored]) > 1e-8:
                raise ValueError('Recomputed mean differs from original: ' + key)
        runs.append(dict(label=meta['label'], started_utc=meta['started_utc'],
                         source_json=path.relative_to(ROOT.parent).as_posix(),
                         source_csv=raw.relative_to(ROOT.parent).as_posix(),
                         json_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         csv_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(), **stats))
    if len(runs) != 3:
        raise ValueError('Expected exactly three historical runs')
    text = ['# Yesterday’s cooling reference — 2026-11-06', '',
            '[New campaign](README.md) · [Original campaign](../2026-11-06-p100-rear-exhaust-cooling/README.md)', '',
            '**Historical reference only; no new measurements taken.** Three completed 600-second rear-pull-fan captures, using P100-only Strata at 131072 context, engine/Control 0.1.55. Original CSV/JSON are unchanged. Yesterday’s exact workload, fan speeds/model, case/shroud and ambient temperature were not independently captured. Today’s open-case/prefill-only declaration does not retroactively establish yesterday’s conditions. Do not treat differences against the new 120×38 mm intake setup as a controlled exhaust effect.', '',
            'Means and within-run population SD are time-weighted sample-and-hold, including the last interval. Max/min are sampled values. Board power excludes fan power. SM clock is not inference throughput.', '']
    rows = []
    for i, r in enumerate(runs, 1):
        rows.append([i] + [fmt(r[k][s]) for k in ('temperature_c', 'sm_clock_mhz', 'power_w', 'utilization_percent') for s in ('mean', 'max')])
    text += ['## Main comparison table', '', table(['Run', 'Temp mean °C', 'Temp max °C', 'SM mean MHz', 'SM max MHz', 'Power mean W', 'Power max W', 'GPU mean %', 'GPU max %'], rows), '',
             '## Minimums and within-run variation', '', table(['Run', 'Temp min °C', 'Temp SD °C', 'SM min MHz', 'SM SD MHz', 'Power min W', 'Power SD W', 'GPU min %', 'GPU SD %'],
             [[i] + [fmt(r[k][s]) for k, _ in METRICS for s in ('min', 'sd')] for i, r in enumerate(runs, 1)]), '',
             '## Sampling, energy and raw evidence', '', table(['Run', 'Start UTC', 'Seconds', 'Samples', 'Max gap s', 'Board Wh', 'Raw CSV / JSON'],
             [[i, r['started_utc'], fmt(r['duration_seconds']), r['samples'], fmt(r['max_gap_s']), fmt(r['energy_wh']),
               f"[CSV](../{r['source_csv']}) / [JSON](../{r['source_json']})"] for i, r in enumerate(runs, 1)]), '',
             '## Across-run summary', '', 'Each run has equal duration. Across-run SD is sample SD of the three run means; range is highest minus lowest run mean.', '']
    summary = []
    for key, name in METRICS:
        values = [r[key]['mean'] for r in runs]
        summary.append([name, fmt(statistics.mean(values)), fmt(statistics.stdev(values)), fmt(max(values)-min(values)), fmt(min(r[key]['min'] for r in runs)), fmt(max(r[key]['max'] for r in runs))])
    text += [table(['Metric', 'Overall mean', 'Across-run SD', 'Run-mean range', 'Lowest sample', 'Highest sample'], summary), '',
             f"Total capture: **1800 s**; total board energy: **{sum(r['energy_wh'] for r in runs):.2f} Wh**; total samples: **{sum(r['samples'] for r in runs)}**.", '',
             '## Run-to-run differences', '', 'Signed deltas use run means; later minus earlier. Percentages use the earlier run as denominator. Celsius percentages are not thermodynamic ratios: prefer absolute °C deltas.', '']
    deltas = []
    for ia, ib in [(0, 1), (1, 2), (0, 2)]:
        for key, name in METRICS:
            a, b = runs[ia][key]['mean'], runs[ib][key]['mean']
            deltas.append([f'{ib+1} − {ia+1}', name, fmt(b-a), fmt(100*(b-a)/a if a else None), fmt(runs[ib][key]['max']-runs[ia][key]['max'])])
    text += [table(['Runs', 'Metric', 'Mean Δ', 'Mean Δ %', 'Observed max Δ'], deltas), '',
             'Three sequential captures describe repeatability, not statistical significance. No ambient-adjusted temperature delta, actual fan RPM or inference-speed difference can be recovered from this evidence. Source-file SHA-256 hashes and unrounded derived values are retained in results/yesterday-analysis.json.']
    (ROOT / 'YESTERDAY_RESULTS.md').write_text('\n'.join(text) + '\n', encoding='utf-8')
    (ROOT / 'results/yesterday-analysis.json').write_text(json.dumps(runs, indent=2) + '\n')
    print('Historical tables saved: YESTERDAY_RESULTS.md (3 completed runs; no new measurements)')


if __name__ == '__main__':
    main()
