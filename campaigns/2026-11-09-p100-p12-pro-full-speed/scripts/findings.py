"""Finish reporting only after three full-speed surveys; does not alter measurements."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / '2026-11-09-p100-new-fan'


def main():
    state = json.loads((ROOT / 'state/queue-state.json').read_text())
    if state['phase'] != 'complete' or len(state['runs']) != 3 or any(r['status'] != 'complete' for r in state['runs'].values()):
        raise RuntimeError('All three full-speed surveys must be complete')
    original_hashes = json.loads((ROOT / 'results/reference-hashes.json').read_text())
    for relative, digest in original_hashes.items():
        if hashlib.sha256((ROOT.parent / relative).read_bytes()).hexdigest() != digest:
            raise RuntimeError('Original reference evidence changed: ' + relative)
    subprocess.run([sys.executable, str(OLD / 'scripts/comparison.py')], check=True)
    comparison = json.loads((OLD / 'results/six-fan-comparison.json').read_text())
    groups = comparison[:2]
    summaries = []
    for group in groups:
        summary = dict(setup=group['setup'], runs=len(group['runs']), metrics={})
        for key in ('temperature_c', 'sm_clock_mhz', 'power_w', 'utilization_percent'):
            means = [r[key]['mean'] for r in group['runs']]
            summary['metrics'][key] = dict(mean=statistics.mean(means), max=max(r[key]['max'] for r in group['runs']),
                                           across_run_sd=statistics.stdev(means), run_mean_range=max(means)-min(means))
        summaries.append(summary)
    # Independently verify throttle percentages and expose settling/drift in each 100% run.
    details = []
    for entry in state['runs'].values():
        path = ROOT / entry['result']
        meta = json.loads(path.read_text())
        with (path.parent / meta['csv_file']).open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        times = [float(r['elapsed_seconds']) for r in rows]
        weights = [b-a for a, b in zip(times, times[1:]+[meta['duration_seconds']])]
        throttle = {}
        for flag, expected in meta['throttle_active_percent'].items():
            value = sum(w for r, w in zip(rows, weights) if r[flag] == 'Active') / meta['duration_seconds'] * 100
            if abs(value-expected) > 1e-6:
                raise RuntimeError('Throttle mean mismatch: ' + flag)
            throttle[flag] = value
        def window_mean(start, end):
            window_weights = [max(0, min(t+w, end)-max(t, start)) for t, w in zip(times, weights)]
            return sum(float(r['temperature_c'])*w for r, w in zip(rows, window_weights)) / (end-start)
        details.append(dict(label=meta['label'], throttle_active_percent=throttle,
                            first_2min_mean_c=window_mean(0,120), last_2min_mean_c=window_mean(480,600)))
    delta = {k: summaries[1]['metrics'][k]['mean']-summaries[0]['metrics'][k]['mean'] for k in summaries[0]['metrics']}
    summary = dict(groups=summaries, delta_100_minus_70=delta, full_speed_runs=details,
                   inference_config_sha256=state['inference_config_sha256'],
                   limitations='Sequential user-managed stress; no measured ambient, post-change heat-soak duration, fan electrical power/noise or throughput. Extractor continued, no other physical change reported.')
    (ROOT / 'results/findings.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    lines = ['# P100 cooling — ARCTIC P12 Pro at 100%', '',
             '**Complete: 3 × 10-minute surveys at 100% / ~2900 RPM**, compared with the earlier 70% / ~2230 RPM surveys. Extractor fan included in both setups; RPM/settings are user reported, not logged tachometer readings.', '',
             '## 100% versus 70%', '',
             '| P12 Pro + extractor | Runs | Mean temp °C | Max temp °C | Mean core MHz | Max core MHz | Mean board W |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for g in summaries:
        m = g['metrics']
        lines.append(f"| {g['setup']} | {g['runs']} | {m['temperature_c']['mean']:.2f} | {m['temperature_c']['max']:.0f} | {m['sm_clock_mhz']['mean']:.2f} | {m['sm_clock_mhz']['max']:.0f} | {m['power_w']['mean']:.2f} |")
    clock_pct = 100*delta['sm_clock_mhz']/summaries[0]['metrics']['sm_clock_mhz']['mean']
    lines += ['', f"**100% minus 70%:** mean temperature **{delta['temperature_c']:+.2f}°C**; mean core clock **{delta['sm_clock_mhz']:+.2f} MHz ({clock_pct:+.2f}%)**; mean board power **{delta['power_w']:+.2f} W**.", '',
              '## Each 100% run', '',
              '| Run | Mean temp °C | Max temp °C | Mean core MHz | Max core MHz | Mean board W |',
              '| --- | --- | --- | --- | --- | --- |']
    for i, r in enumerate(groups[1]['runs'], 1):
        lines.append(f"| [{i}](../{r['csv_file']}) | {r['temperature_c']['mean']:.2f} | {r['temperature_c']['max']:.0f} | {r['sm_clock_mhz']['mean']:.2f} | {r['sm_clock_mhz']['max']:.0f} | {r['power_w']['mean']:.2f} |")
    thermal = any(r['throttle_active_percent'][k] > 0 for r in details for k in ('sw_thermal_slowdown','hw_thermal_slowdown'))
    lines += ['', '## Findings and limits', '',
              '- ' + ('Thermal slowdown indicators were observed; see the detailed report.' if thermal else '**No thermal-throttle flags were observed** in the 100% surveys.'),
              '- Both P12 groups used the same running P100-only IQ3_S Strata 0.1.57 server, 131072 context, int8 KV, full experts and credential-free inference-config SHA-256. The agent did not alter the workload, software, model, power limit or clocks.',
              '- Results describe cooling under the existing stress workload, not an inference-speed benchmark. Near-maximum clocks can limit how much extra cooling raises clock speed. Board power excludes external fan power; noise, fan watts and throughput were not measured.',
              '- Sequential 70% then 100% groups are not randomized independent trials. Exact stress command/settings, ambient and time spent heat soaking after the speed change are unknown. All initial/transient samples are included. No other physical change was reported; extractor operation is not independently instrumented.',
              '- Means are time-weighted sample-and-hold; maxima are sampled peaks. Core clock means NVIDIA SM clock. Query overhead makes actual sample gaps longer than the requested one second; actual counts/gaps are in the report.', '',
              '## Within-run temperature drift', '',
              '| Run | First 2 min mean °C | Last 2 min mean °C | Last − first °C |',
              '| --- | --- | --- | --- |']
    for r in details:
        lines.append(f"| {r['label']} | {r['first_2min_mean_c']:.2f} | {r['last_2min_mean_c']:.2f} | {r['last_2min_mean_c']-r['first_2min_mean_c']:+.2f} |")
    lines += ['', '## Evidence', '',
              '[All six setups and all 17 runs](../2026-11-09-p100-new-fan/README.md) · [Detailed full-speed telemetry](REPORT.md) · [Derived findings](results/findings.json) · [Checkpoint](state/queue-state.json) · [Work log](NOTES.md) · [Plan](PLAN.md) · [Manifest](manifest.json)', '',
              'Raw CSV/JSON is preserved in results/. Original 70% measurements/checkpoint and previous historical evidence remain unchanged. No stress/server processes were started or stopped by this survey. The telemetry supervisor finished; the user-managed workload/server was left running.']
    (ROOT / 'README.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    spec = importlib.util.spec_from_file_location('full_speed_capture_report', ROOT / 'scripts/capture.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.report(state)
    with (ROOT / 'REPORT.md').open('a', encoding='utf-8') as stream:
        stream.write('\n## Comparison and interpretation\n\nSee [findings and 70% comparison](README.md). Independent CSV throttle checks passed; original reference hashes unchanged.\n')
    print('Full-speed findings and both comparison READMEs updated.')


if __name__ == '__main__':
    main()
