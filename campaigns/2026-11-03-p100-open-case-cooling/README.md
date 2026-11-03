# P100 open case cooling

[Campaign index](../../README.md) · [Manifest](manifest.json) · [Plan](PLAN.md) · [Work log](NOTES.md)

**Conclusion: one fan is the better-supported choice for this particular open-case, unducted arrangement.** Across the latest four completed ten-minute runs, it sustained **171.78 W versus 152.13 W** with two fans (**+19.64 W / +12.9%**), and **1231 versus 1167 MHz** average SM clock (**+5.5%**), at essentially the same **79°C** GPU temperature. Both repeats agree closely. This supports better effective cooling with one fan under the tested load—not a general claim that fewer fans cool better.

## Scope and selected runs

Physical setup is user-confirmed: **open case, no ducting**, alternating **one fan → two fans → one fan → two fans**. Fan models, speeds, positions/directions and inlet/room temperature were not recorded. GPU: Tesla P100-PCIE-16GB, UUID `GPU-bab5c751-1e02-b6a7-cf6f-b6256c3a5999`.

The table uses the **last four runs marked `complete`**, chronologically, on 2026-11-03. All lasted 600 seconds. Earlier runs and monitor validation are outside this comparison. The 15:33:03 two-fan attempt was interrupted after 39.25 seconds; it is preserved but excluded. The completed 15:33:48 run is a separate fresh measurement, not a continuation.

| Start (UTC) / setup | Mean board power | Mean GPU temp | Max temp | Mean SM clock | Mean GPU utilization | Evidence |
|---|---:|---:|---:|---:|---:|---|
| 15:00:15 / 1 fan, repeat 1 | 172.01 W | 78.96°C | 80°C | 1229.3 MHz | 99.62% | [JSON](results/20261103T150015.811323Z-open-1fan-1-json.json) · [CSV](results/20261103T150015.811323Z-open-1fan-1-json.csv) |
| 15:11:23 / 2 fans, repeat 1 | 151.65 W | 78.99°C | 80°C | 1166.7 MHz | 99.82% | [JSON](results/20261103T151123.578398Z-open-2fan-1-json.json) · [CSV](results/20261103T151123.578398Z-open-2fan-1-json.csv) |
| 15:22:07 / 1 fan, repeat 2 | 171.54 W | 78.89°C | 80°C | 1233.1 MHz | 98.80% | [JSON](results/20261103T152207.850774Z-open-1fan-2-json.json) · [CSV](results/20261103T152207.850774Z-open-1fan-2-json.csv) |
| 15:33:48 / 2 fans, repeat 2 | 152.61 W | 79.00°C | 80°C | 1167.3 MHz | 99.78% | [JSON](results/20261103T153348.318203Z-open-2fan-2-json.json) · [CSV](results/20261103T153348.318203Z-open-2fan-2-json.csv) |
| **1 fan: two-run mean** | **171.78 W** | **78.92°C** | **80°C** | **1231.2 MHz** | **99.21%** | |
| **2 fans: two-run mean** | **152.13 W** | **78.99°C** | **80°C** | **1167.0 MHz** | **99.80%** | |

Power, temperature, utilization and clock means are time-weighted sample-and-hold values, recomputed from each CSV and checked against its JSON. Equal run durations make the two-run means also time-weighted across the selected measurements. The 0.07°C difference between setup averages is not meaningful given integer-degree temperature readings.

## Why one fan looks better

- **The difference repeats:** one-fan power differs by only 0.47 W between repeats, and two-fan power by 0.96 W. The one-fan advantage is 20.36 W in the first pair and 18.93 W in the second. Alternating setups makes a simple monotonic warm-up or ambient drift explanation less persuasive, though it does not eliminate confounding.
- **Higher power comes with higher clocks, not higher temperature.** At a similar temperature under a comparable, thermally constrained workload, sustaining more board power and higher clocks is consistent with removing heat more effectively. Equal temperature alone does not imply equal cooling: thermal clock control can keep temperature near a ceiling while reducing power/performance. Throttle reasons were not logged, so thermal limitation is an interpretation, not directly verified telemetry.
- **Load and power-limit checks support the comparison:** every selected CSV reports the same 250 W power limit throughout; mean power is well below that ceiling. Average utilization is 98.80–99.82%, with brief dips. One fan actually has slightly lower average utilization, so its higher power is not explained by a higher average busy percentage. Utilization alone cannot prove identical work.
- **Not just an opening transient:** in the final five minutes, the one-fan runs average 172.64 / 171.16 W versus 151.69 / 152.39 W with two fans. The separation remains after discarding each run's first half. First and last two-minute mean temperatures are all approximately 79°C.
- **Sampling is consistent:** 565–566 samples per run; largest sample gaps are 1.079–1.094 seconds. No selected run reports an error or missing summary metric.

A possible explanation is that the second fan disrupts useful flow through the passive heatsink, promotes recirculation or diverts air around it in the unducted setup. **These measurements do not establish the airflow mechanism.** Fan placement/direction or proper ducting could reverse the result.

## Recommendation and limits

**For this exact arrangement, prefer one fan provisionally.** The repeatable power-and-clock advantage is more convincing than temperature alone. This is not an efficiency result: one fan lets the GPU consume more electrical power under load; fan electrical consumption and delivered work were not measured.

There are only two repeats per setup, always in the same pair order. Ambient/inlet temperature, exact fan geometry/RPM, software versions, stress-test invocation and proof that workload/settings stayed fixed are absent from the saved telemetry. The intended workload is the user's P100-only Strata prefill stress test; it was not launched or controlled by this monitor. No throughput, thermal-throttle flags or calibrated heat-flow measurement was captured. Consequently this is **suggestive cooling evidence, not statistical significance, a measured inference-speed gain or proof of model-quality equivalence**.

For stronger confirmation, record those missing conditions, repeat in reverse order (2 → 1 → 2 → 1) after stabilization, and capture throttle reasons plus actual workload throughput. Treat ducted or repositioned fans as a new physical comparison; do not extrapolate this result to them.

## Passive monitor / further measurements

No workload, GPU setting or inference profile is changed by the monitor. Keep the existing stress test running, install the intended setup safely, and let temperatures/power stabilize before starting. From the repository root, run one measurement at a time with a descriptive label:

```sh
python campaigns/2026-11-03-p100-open-case-cooling/scripts/monitor_power.py --label open-1fan-confirmation
```

Default: unique P100, 600 seconds, approximately one sample per second. Use `--gpu INDEX` or UUID for explicit selection. Requires Python 3 and `nvidia-smi` on PATH; no Python packages. Optional: `--seconds 60 --interval 1` or `--output-dir PATH`; short validation runs are not comparable ten-minute cooling results.

Timestamped CSV/JSON files go into `results/` without overwriting previous runs. Ctrl+C saves a partial run; query failures mark a run failed. Preserve incomplete attempts and start a new run rather than resuming one. The monitor supplies no thermal protection. `state/queue-state.json` is the original planning checkpoint, **not** a measurement inventory or automatic resume queue; result JSON statuses identify completed measurements.
