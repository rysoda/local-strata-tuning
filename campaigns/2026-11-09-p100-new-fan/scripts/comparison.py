"""Generate cooling comparisons from preserved complete CSV evidence (no measurements)."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGNS = ROOT.parent
OLD = CAMPAIGNS / '2026-11-07-p100-server-fan-intake-exhaust'
spec = importlib.util.spec_from_file_location('cooling_metrics', OLD / 'scripts/report.py')
metrics_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics_module)


def main():
    old = json.loads((OLD / 'results/comparison-analysis.json').read_text())['groups']
    state = json.loads((ROOT / 'state/capture-state.json').read_text())
    if state['phase'] != 'complete':
        raise RuntimeError('Three current captures must be complete')
    groups = [('ARCTIC P12 Pro · 70% (~2230 RPM) + extractor', []),
              ('ARCTIC S12038-4K · auto (75°C target)', old['New intake only']),
              ('ARCTIC S12038-4K · auto (75°C target) + extractor', old['New intake + exhaust']),
              ('ARCTIC P9 PWM PST · alone', old['Nov 3 old one fan']),
              ('ARCTIC P9 PWM PST · + extractor', old['Nov 6 rear pull'])]
    for label, entry in state['runs'].items():
        if entry['status'] != 'complete':
            raise RuntimeError('Incomplete run: ' + label)
        path = ROOT / entry['result']
        meta = json.loads(path.read_text())
        groups[0][1].append(dict(label=label, json_file=str(path.relative_to(CAMPAIGNS)),
                                 csv_file=str((path.parent / meta['csv_file']).relative_to(CAMPAIGNS))))
    full_root = CAMPAIGNS / '2026-11-09-p100-p12-pro-full-speed'
    full_state_path = full_root / 'state/queue-state.json'
    if full_state_path.exists():
        full_state = json.loads(full_state_path.read_text())
        if full_state['phase'] != 'complete' or len(full_state['runs']) != 3:
            raise RuntimeError('Full-speed surveys must finish before publishing the expanded comparison')
        if full_state['inference_config_sha256'] != state['inference_config_sha256']:
            raise RuntimeError('P12 inference settings changed between fan speeds')
        members = []
        for label, entry in full_state['runs'].items():
            if entry['status'] != 'complete':
                raise RuntimeError('Incomplete full-speed run: ' + label)
            path = full_root / entry['result']
            meta = json.loads(path.read_text())
            members.append(dict(label=label, json_file=str(path.relative_to(CAMPAIGNS)),
                                csv_file=str((path.parent / meta['csv_file']).relative_to(CAMPAIGNS))))
        groups.insert(1, ('ARCTIC P12 Pro · 100% (~2900 RPM) + extractor', members))
    derived = []
    for name, members in groups:
        runs = []
        for member in members:
            jp = CAMPAIGNS / member['json_file']
            cp = CAMPAIGNS / member['csv_file']
            meta = json.loads(jp.read_text())
            if meta['status'] != 'complete' or meta['duration_seconds'] != 600:
                raise RuntimeError('Not a complete ten-minute run: ' + str(jp))
            with cp.open(newline='', encoding='utf-8') as stream:
                stats = metrics_module.metrics(list(csv.DictReader(stream)), meta['duration_seconds'])
            expected = meta.get('metrics', member)
            for key in ('temperature_c', 'sm_clock_mhz', 'power_w'):
                if abs(stats[key]['mean'] - expected[key]['mean']) > 1e-6:
                    raise RuntimeError('Mean mismatch: ' + str(jp))
            runs.append(dict(label=member['label'], date=meta['started_utc'][:10],
                             csv_file=cp.relative_to(CAMPAIGNS).as_posix(),
                             json_file=jp.relative_to(CAMPAIGNS).as_posix(),
                             csv_sha256=hashlib.sha256(cp.read_bytes()).hexdigest(),
                             json_sha256=hashlib.sha256(jp.read_bytes()).hexdigest(), **stats))
        derived.append(dict(setup=name, runs=runs))
    analysis_name = 'six-fan-comparison.json' if len(derived) == 6 else 'five-fan-comparison.json'
    lines = [f'# P100 cooling — {len(derived)} fan setups', '',
             '**All captures are complete; every run is 10 minutes.** Fan names and extractor presence are identified by the user, including the latest P12 Pro + extractor setup.', '',
             '## At a glance', '',
             '| Setup | Runs | Mean temp °C | Max temp °C | Mean core MHz | Max core MHz | Mean board W |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for group in derived:
        runs = group['runs']
        lines.append(f"| {group['setup']} | {len(runs)} | {statistics.mean(r['temperature_c']['mean'] for r in runs):.2f} | {max(r['temperature_c']['max'] for r in runs):.0f} | {statistics.mean(r['sm_clock_mhz']['mean'] for r in runs):.2f} | {max(r['sm_clock_mhz']['max'] for r in runs):.0f} | {statistics.mean(r['power_w']['mean'] for r in runs):.2f} |")
    lines += ['', '## Every run', '',
              '| Setup / run | Date | Mean temp °C | Max temp °C | Mean core MHz | Max core MHz | Mean board W |',
              '| --- | --- | --- | --- | --- | --- | --- |']
    for group in derived:
        for i, r in enumerate(group['runs'], 1):
            link = '../' + r['csv_file']
            lines.append(f"| {group['setup']} / [{i}]({link}) | {r['date']} | {r['temperature_c']['mean']:.2f} | {r['temperature_c']['max']:.0f} | {r['sm_clock_mhz']['mean']:.2f} | {r['sm_clock_mhz']['max']:.0f} | {r['power_w']['mean']:.2f} |")
    lines += ['', '## Reading the results', '']
    if len(derived) == 6:
        a, b = derived[0]['runs'], derived[1]['runs']
        avg = lambda runs, key: statistics.mean(r[key]['mean'] for r in runs)
        dt = avg(b, 'temperature_c') - avg(a, 'temperature_c')
        dc = avg(b, 'sm_clock_mhz') - avg(a, 'sm_clock_mhz')
        dp = avg(b, 'power_w') - avg(a, 'power_w')
        lines += [f'- **P12 Pro 100% versus 70%:** mean temperature **{dt:+.2f}°C**, mean core clock **{dc:+.2f} MHz ({100*dc/avg(a, "sm_clock_mhz"):+.2f}%)**, mean board power **{dp:+.2f} W**. This measures thermal behavior, not inference throughput.',
                  '- Both P12 groups used the same credential-free inference-config SHA-256. The 100% group follows the 70% group; heat-soak duration after changing speed and ambient were not recorded. Initial settling samples are included. Extractor setup continued; no other physical change reported.',
                  '- See the [100% findings and throttle analysis](../2026-11-09-p100-p12-pro-full-speed/README.md).']
    else:
        lines += ['- **P12 Pro at 70% + extractor:** 73.78°C mean, 75°C sampled maximum, sustaining ~1319 MHz. No thermal-throttle flags were observed in these three runs.']
    coolest = min(derived, key=lambda g: statistics.mean(r['temperature_c']['mean'] for r in g['runs']))
    lines += [f'- **Lowest recorded group-mean temperature:** {coolest["setup"]}, **{statistics.mean(r["temperature_c"]["mean"] for r in coolest["runs"]):.2f}°C**. Historical conditions are not matched.',
              '- **S12038-4K + extractor drift caveat:** its third run warmed to 70.12°C mean / 77°C maximum; all three runs remain included. Historical notes could not establish when the extractor was removed relative to that run.',
              '- **Your remembered P9 power levels are confirmed:** alone **171.78 W**; with extractor **197.54 W** (closer to 198 W than 190 W). The extractor-era P9 runs also sustained much higher clocks than the older standalone runs.', '',
              'Means are time-weighted sample-and-hold; summary means average equal-duration run means. Maxima are the highest observed samples, not continuous peaks. “Core clock” is NVIDIA SM clock. Board power excludes external fan power.', '',
              '**Historical comparison, not a controlled fan ranking:** ambient, exact stress settings and some case/shroud details were not recorded. P12 captures used Strata 0.1.57; the S12038 and P9+extractor captures used 0.1.55. Older P9-only workload/software provenance is less complete. Fan model/extractor labels follow the user’s clarification; older logs used generic fan labels. Higher clock or power is not proof of greater inference throughput.', '',
              '## Evidence and server', '',
              '[Latest detailed survey](REPORT.md) · [Previous cooling comparison](../2026-11-07-p100-server-fan-intake-exhaust/COMPARISON.md) · [Work log](NOTES.md) · [Manifest](manifest.json) · [Capture checkpoint](state/capture-state.json)', '',
              f'Each run number above links to its raw CSV. Recomputed statistics, source paths and SHA-256 hashes: [comparison analysis](results/{analysis_name}). Rebuild with `python campaigns/2026-11-09-p100-new-fan/scripts/comparison.py`; original evidence is not changed.', '',
              f'Telemetry collection finished after {6 if len(derived) == 6 else 3} P12 surveys; the user-managed workload/server was left running. No new measurement or restart is needed for this comparison. P100-only IQ3_S, 131072 context, int8 KV, full experts; isolated runtime `configs/private/p100.runtime.json`. API uses the usual key at `http://<this-PC-IP>:8080/v1`. Installed profiles/Startup are unchanged. Before any server recovery, verify live command lines and port ownership; archived PIDs are not ownership proof.']
    (ROOT / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (ROOT / 'results' / analysis_name).write_text(json.dumps(derived, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {len(derived)}-setup README; verified {sum(len(g["runs"]) for g in derived)} complete CSVs against saved means.')


if __name__ == '__main__':
    main()
