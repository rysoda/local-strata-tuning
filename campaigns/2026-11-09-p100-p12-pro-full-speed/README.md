# P100 cooling — ARCTIC P12 Pro at 100%

**Complete: 3 × 10-minute surveys at 100% / ~2900 RPM**, compared with the earlier 70% / ~2230 RPM surveys. Extractor fan included in both setups; RPM/settings are user reported, not logged tachometer readings.

## 100% versus 70%

| P12 Pro + extractor | Runs | Mean temp °C | Max temp °C | Mean core MHz | Max core MHz | Mean board W |
| --- | --- | --- | --- | --- | --- | --- |
| ARCTIC P12 Pro · 70% (~2230 RPM) + extractor | 3 | 73.78 | 75 | 1319.21 | 1328 | 196.54 |
| ARCTIC P12 Pro · 100% (~2900 RPM) + extractor | 3 | 65.69 | 67 | 1324.09 | 1328 | 193.32 |

**100% minus 70%:** mean temperature **-8.09°C**; mean core clock **+4.89 MHz (+0.37%)**; mean board power **-3.22 W**.

## Each 100% run

| Run | Mean temp °C | Max temp °C | Mean core MHz | Max core MHz | Mean board W |
| --- | --- | --- | --- | --- | --- |
| [1](../2026-11-09-p100-p12-pro-full-speed/results/20261109T113256.898720Z-p12-pro-100pct-1.csv) | 65.13 | 66 | 1324.25 | 1328 | 191.37 |
| [2](../2026-11-09-p100-p12-pro-full-speed/results/20261109T114258.997259Z-p12-pro-100pct-2.csv) | 65.92 | 67 | 1324.34 | 1328 | 193.67 |
| [3](../2026-11-09-p100-p12-pro-full-speed/results/20261109T115301.398021Z-p12-pro-100pct-3.csv) | 66.02 | 67 | 1323.70 | 1328 | 194.91 |

## Findings and limits

- **No thermal-throttle flags were observed** in the 100% surveys.
- Both P12 groups used the same running P100-only IQ3_S Strata 0.1.57 server, 131072 context, int8 KV, full experts and credential-free inference-config SHA-256. The agent did not alter the workload, software, model, power limit or clocks.
- Results describe cooling under the existing stress workload, not an inference-speed benchmark. Near-maximum clocks can limit how much extra cooling raises clock speed. Board power excludes external fan power; noise, fan watts and throughput were not measured.
- Sequential 70% then 100% groups are not randomized independent trials. Exact stress command/settings, ambient and time spent heat soaking after the speed change are unknown. All initial/transient samples are included. No other physical change was reported; extractor operation is not independently instrumented.
- Means are time-weighted sample-and-hold; maxima are sampled peaks. Core clock means NVIDIA SM clock. Query overhead makes actual sample gaps longer than the requested one second; actual counts/gaps are in the report.

## Within-run temperature drift

| Run | First 2 min mean °C | Last 2 min mean °C | Last − first °C |
| --- | --- | --- | --- |
| p12-pro-100pct-1 | 64.53 | 65.81 | +1.28 |
| p12-pro-100pct-2 | 65.89 | 65.96 | +0.07 |
| p12-pro-100pct-3 | 66.00 | 65.99 | -0.01 |

## Evidence

[All six setups and all 17 runs](../2026-11-09-p100-new-fan/README.md) · [Detailed full-speed telemetry](REPORT.md) · [Derived findings](results/findings.json) · [Checkpoint](state/queue-state.json) · [Work log](NOTES.md) · [Plan](PLAN.md) · [Manifest](manifest.json)

Raw CSV/JSON is preserved in results/. Original 70% measurements/checkpoint and previous historical evidence remain unchanged. No stress/server processes were started or stopped by this survey. The telemetry supervisor finished; the user-managed workload/server was left running.
