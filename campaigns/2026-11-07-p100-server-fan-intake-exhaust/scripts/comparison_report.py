"""Final cooling comparison; read raw evidence only, no GPU/workload actions."""
import csv
import hashlib
import json
from pathlib import Path
import statistics

from report import METRICS, fmt, metrics, table

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGNS = ROOT.parent


def load(path, group):
    meta = json.loads(path.read_text())
    if meta['status'] != 'complete' or meta['duration_seconds'] != 600:
        raise ValueError('Expected a completed 600-second result: ' + str(path))
    raw = path.parent / meta['csv_file']
    with raw.open(newline='') as f:
        rows = list(csv.DictReader(f))
    stats = metrics(rows, meta['duration_seconds'])
    for key, stored in [('temperature_c', 'average_temperature_c'), ('sm_clock_mhz', 'average_sm_clock_mhz'), ('power_w', 'average_power_w'), ('utilization_percent', 'average_utilization_percent')]:
        if abs(stats[key]['mean'] - meta[stored]) > 1e-6:
            raise ValueError('Original summary mismatch: ' + str(path))
    return dict(group=group, label=meta['label'], started_utc=meta['started_utc'],
                json_file=path.relative_to(CAMPAIGNS).as_posix(), csv_file=raw.relative_to(CAMPAIGNS).as_posix(),
                json_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), csv_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(), **stats)


def main():
    state = json.loads((ROOT / 'state/queue-state.json').read_text())
    if state['phase'] != 'complete' or len(state['runs']) != 6:
        raise ValueError('New six-run campaign must be complete')
    groups = {'New intake only': [], 'New intake + exhaust': [], 'Nov 6 rear pull': [], 'Nov 3 old one fan': []}
    for label, entry in state['runs'].items():
        if entry['status'] != 'complete':
            raise ValueError('Incomplete state entry: ' + label)
        group = 'New intake only' if entry['group'] == 'intake' else 'New intake + exhaust'
        groups[group].append(load(ROOT / entry['result'], group))
    for path in sorted((CAMPAIGNS / '2026-11-06-p100-rear-exhaust-cooling/results').glob('*-rear-pull-reference-*.json')):
        groups['Nov 6 rear pull'].append(load(path, 'Nov 6 rear pull'))
    for name in ['20261103T150015.811323Z-open-1fan-1-json.json', '20261103T152207.850774Z-open-1fan-2-json.json']:
        groups['Nov 3 old one fan'].append(load(CAMPAIGNS / '2026-11-03-p100-open-case-cooling/results' / name, 'Nov 3 old one fan'))
    if [len(r) for r in groups.values()] != [3, 3, 3, 2]:
        raise ValueError('Unexpected selected run inventory')
    summaries = {}
    for group, runs in groups.items():
        summary = {'runs': len(runs), 'energy_wh': sum(r['energy_wh'] for r in runs), 'sample_count': sum(r['samples'] for r in runs)}
        for key, _ in METRICS:
            means = [r[key]['mean'] for r in runs]
            summary[key] = dict(mean=statistics.mean(means), max=max(r[key]['max'] for r in runs),
                                min=min(r[key]['min'] for r in runs), run_sd=statistics.stdev(means),
                                run_mean_range=max(means)-min(means))
        summaries[group] = summary
    text = ['# P100 cooling: final comparison', '',
            '**Completed: 6/6 new captures.** Three intake-only and three intake + exhaust runs, each 600 seconds. Case open; prefill-only user-managed stress; 120×38 mm nominal 4000 RPM intake curve reaches 100% at 75°C. P100-only Strata 0.1.55, Qwen3.8-Flash-Next IQ3_S, 131072 context, int8 KV, full expert routing. Actual fan RPM, ambient, lower-temperature curve and exact stress invocation were not recorded.', '',
            '[New six-run detailed tables](REPORT.md) · [Yesterday’s detailed tables](YESTERDAY_RESULTS.md) · [Old open-case source report](../2026-11-03-p100-open-case-cooling/README.md)', '',
            '## Main comparison', '',
            'Each cell shows **time-weighted mean / highest sampled value**. Equal-duration runs give equal-weight group means. Board power excludes external fan power; higher/lower board power alone is not cooling efficiency or throughput.', '']
    text += [table(['Setup', 'Runs × min', 'Temp °C mean / max', 'SM MHz mean / max', 'Board W mean / max', 'GPU % mean'],
             [[g, f"{s['runs']} × 10"] + [f"{s[k]['mean']:.2f} / {s[k]['max']:.2f}" for k in ('temperature_c', 'sm_clock_mhz', 'power_w')] + [fmt(s['utilization_percent']['mean'])] for g, s in summaries.items()]), '',
             '**The remembered ~170 W result is confirmed:** the selected November 3 one-fan runs averaged 171.78 W (172.01 W and 171.54 W). They were open-case and unducted. Their fan geometry/direction was not recorded, so calling them definitively “without the pulling fan” would go beyond the saved evidence; they are labeled “old one fan.”', '',
             '## Differences in group means', '', 'Signed change = named setup minus reference; percentages use reference means. Only the new intake-versus-intake+exhaust comparison is within this campaign. Historical differences are descriptive, not isolated causal gains.', '']
    pairs = [('New intake + exhaust', 'New intake only'), ('New intake only', 'Nov 6 rear pull'),
             ('New intake + exhaust', 'Nov 6 rear pull'), ('New intake only', 'Nov 3 old one fan'),
             ('New intake + exhaust', 'Nov 3 old one fan'), ('Nov 6 rear pull', 'Nov 3 old one fan')]
    deltas = []
    for group, ref in pairs:
        a, b = summaries[ref], summaries[group]
        tc = b['temperature_c']['mean'] - a['temperature_c']['mean']
        cl = b['sm_clock_mhz']['mean'] - a['sm_clock_mhz']['mean']
        pw = b['power_w']['mean'] - a['power_w']['mean']
        deltas.append([f'{group} − {ref}', fmt(tc), fmt(cl), fmt(100*cl/a['sm_clock_mhz']['mean']), fmt(pw), fmt(100*pw/a['power_w']['mean'])])
    text += [table(['Comparison', 'Temp Δ °C', 'SM Δ MHz', 'SM Δ %', 'Board Δ W', 'Board Δ %'], deltas), '',
             '## Interpretation', '',
             '- **Adding exhaust coincided with a 6.10°C lower mean temperature**, 2.98 MHz higher mean SM clock (+0.23%) and 2.19 W lower mean board power (−1.11%). Peak sampled temperature was 77°C in both groups; peak clock was 1328 MHz in both. The practical observed advantage is temperature headroom, not a demonstrated inference-speed improvement.',
             '- **The new intake alone is a clear descriptive improvement over the old ~170 W operating point:** 5.44°C lower mean GPU temperature and 88.74 MHz higher mean clock (+7.21%), while sustaining 25.17 W more board power (+14.66%). Different dates, uncertain workload/software provenance and changed fan geometry prevent treating these as controlled causal deltas.',
             '- Relative to November 6, the new intake alone was 2.89°C cooler at essentially the same clocks/power; intake + exhaust was 8.99°C cooler. Yesterday’s precise case/workload/fan speeds/ambient were not independently captured, so these are historical references only.',
             '- **Important drift caveat:** both-fan run 3 averaged 70.12°C and reached 77°C, compared with ~66°C means and 67°C maxima in runs 1–2. All three remain included. This could reflect a physical/control/ambient change or another cause; the timing of exhaust removal relative to that run is not established. It weakens a clean fixed-setup interpretation. Intake-only run means were much tighter (73.38–73.69°C).',
             '- Provisionally, use intake + exhaust when temperature headroom is the priority, subject to confirming that the exhaust remained installed/unchanged through all three captures. The new intake alone also maintained near-maximum clocks. Noise, fan electrical consumption, throughput and actual thermal-throttle flags were not measured.', '',
             '## Repeatability of run means', '',
             'Sample SD across run means and their range describe repeatability, not independent-sample confidence intervals.', '']
    text += [table(['Setup', 'Temp SD / range °C', 'SM SD / range MHz', 'Board SD / range W'],
             [[g] + [f"{s[k]['run_sd']:.2f} / {s[k]['run_mean_range']:.2f}" for k in ('temperature_c', 'sm_clock_mhz', 'power_w')] for g, s in summaries.items()]), '',
             '## Every selected run', '', table(['Setup / run', 'Temp mean / max °C', 'SM mean / max MHz', 'Board mean / max W', 'GPU mean %', 'Samples', 'Wh', 'Evidence'],
             [[f"{g} / {i}"] + [f"{r[k]['mean']:.2f} / {r[k]['max']:.2f}" for k in ('temperature_c', 'sm_clock_mhz', 'power_w')] + [fmt(r['utilization_percent']['mean']), r['samples'], fmt(r['energy_wh']), f"[CSV](../{r['csv_file']}) / [JSON](../{r['json_file']})"] for g, runs in groups.items() for i, r in enumerate(runs, 1)]), '',
             '## Measurement and scope limits', '',
             'All 11 selected historical/new CSVs were recomputed using the same sample-and-hold method, including the final sampling interval, and checked against original JSON means within 1e-6. Only complete 600-second captures are included; the old interrupted attempt and earlier exploratory runs remain excluded as in their source report. Original raw CSV/JSON bytes were not changed. Unrounded derived values, within-run min/max/SD, sample gaps, energy and source SHA-256 hashes are preserved in results/comparison-analysis.json.', '',
             'New order was both-fans then intake-only, with user-reported heat soak. Sequential order, unmeasured ambient/RPM, fan-curve feedback, brief utilization dips and unrecorded exact workload prevent significance/efficiency claims. Historical configurations are not pooled as repeats of the new fan setups. This is cooling telemetry, not a BetterBench result, model-quality test or inference-speed benchmark. No new measurement was started for reporting; the user-managed server/workload is left untouched.']
    (ROOT / 'COMPARISON.md').write_text('\n'.join(text) + '\n', encoding='utf-8')
    (ROOT / 'results/comparison-analysis.json').write_text(json.dumps(dict(groups=groups, summaries=summaries), indent=2) + '\n')
    print('Final comparison saved: COMPARISON.md (11 selected runs; no measurements started)')
    for group, s in summaries.items():
        print(group, 'temp',s['temperature_c']['mean'],'clock',s['sm_clock_mhz']['mean'],'power',s['power_w']['mean'])


if __name__ == '__main__':
    main()
