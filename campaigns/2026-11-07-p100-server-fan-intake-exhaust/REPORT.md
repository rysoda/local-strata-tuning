# Server intake fan: cooling comparison

Completed captures: **6/6**. Both groups complete; see [final comparison and historical references](COMPARISON.md).

A = 120×38 mm nominal 4000 RPM intake only. B = same intake plus exhaust. Intake curve reaches 100% at 75°C (user-reported; actual RPM not measured).

Means/within-run SD are time-weighted sample-and-hold. Max/min are observed samples, not continuous extrema. Board power excludes external fan power. All temperatures are absolute GPU temperatures; ambient-adjusted comparisons require ambient measurements.

## Per-run telemetry

| Run | Temp °C mean | min | max | SD | SM clock MHz mean | min | max | SD | Board W mean | min | max | SD | GPU % mean | min | max | SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| intake-exhaust-1 | 66.00 | 62.00 | 67.00 | 0.45 | 1323.56 | 1303.00 | 1328.00 | 5.84 | 194.03 | 47.48 | 253.08 | 27.75 | 99.43 | 6.00 | 100.00 | 6.22 |
| intake-exhaust-2 | 66.04 | 63.00 | 67.00 | 0.38 | 1323.78 | 1303.00 | 1328.00 | 5.88 | 195.12 | 53.41 | 253.81 | 25.62 | 99.96 | 78.00 | 100.00 | 0.93 |
| intake-exhaust-3 | 70.12 | 64.00 | 77.00 | 3.96 | 1321.43 | 1278.00 | 1328.00 | 8.36 | 195.15 | 50.98 | 255.10 | 23.83 | 99.73 | 35.00 | 100.00 | 3.50 |
| intake-1 | 73.39 | 69.00 | 77.00 | 1.84 | 1319.94 | 1303.00 | 1328.00 | 9.42 | 198.28 | 51.97 | 255.49 | 25.40 | 99.87 | 27.00 | 100.00 | 3.07 |
| intake-2 | 73.69 | 67.00 | 77.00 | 1.57 | 1320.05 | 1290.00 | 1328.00 | 9.48 | 195.86 | 50.72 | 254.90 | 26.96 | 99.44 | 2.00 | 100.00 | 6.23 |
| intake-3 | 73.38 | 69.00 | 77.00 | 1.80 | 1319.82 | 1303.00 | 1328.00 | 9.42 | 196.71 | 54.39 | 258.50 | 24.96 | 99.87 | 66.00 | 100.00 | 1.92 |

## Sampling and energy

| Run | Seconds | Samples | Max gap s | Board Wh | Raw summary |
| --- | --- | --- | --- | --- | --- |
| intake-exhaust-1 | 600.00 | 566 | 1.41 | 32.34 | [results/20261107T115851.337003Z-intake-exhaust-1.json](results/20261107T115851.337003Z-intake-exhaust-1.json) |
| intake-exhaust-2 | 600.00 | 566 | 1.08 | 32.52 | [results/20261107T120852.836431Z-intake-exhaust-2.json](results/20261107T120852.836431Z-intake-exhaust-2.json) |
| intake-exhaust-3 | 600.00 | 566 | 1.08 | 32.53 | [results/20261107T121854.305605Z-intake-exhaust-3.json](results/20261107T121854.305605Z-intake-exhaust-3.json) |
| intake-1 | 600.00 | 565 | 1.09 | 33.05 | [results/20261107T125314.991061Z-intake-1.json](results/20261107T125314.991061Z-intake-1.json) |
| intake-2 | 600.00 | 565 | 1.09 | 32.64 | [results/20261107T130316.492069Z-intake-2.json](results/20261107T130316.492069Z-intake-2.json) |
| intake-3 | 600.00 | 566 | 1.11 | 32.79 | [results/20261107T131317.971244Z-intake-3.json](results/20261107T131317.971244Z-intake-3.json) |

## Group summaries

Across-run SD/range describe repeatability of run means, not independent sample uncertainty.

| Setup | n | Metric | Mean of run means | Across-run SD | Run-mean range | Highest observed |
| --- | --- | --- | --- | --- | --- | --- |
| intake | 3 | Temp °C | 73.49 | 0.18 | 0.31 | 77.00 |
| intake | 3 | SM clock MHz | 1319.94 | 0.11 | 0.23 | 1328.00 |
| intake | 3 | Board W | 196.95 | 1.22 | 2.41 | 258.50 |
| intake | 3 | GPU % | 99.73 | 0.25 | 0.43 | 100.00 |
| intake-exhaust | 3 | Temp °C | 67.39 | 2.36 | 4.11 | 77.00 |
| intake-exhaust | 3 | SM clock MHz | 1322.92 | 1.30 | 2.35 | 1328.00 |
| intake-exhaust | 3 | Board W | 194.76 | 0.64 | 1.13 | 255.10 |
| intake-exhaust | 3 | GPU % | 99.71 | 0.26 | 0.52 | 100.00 |

## Differences between consecutive runs within each setup

Signed difference = later run minus previous run.

| Comparison | Mean metric | Difference | % of previous |
| --- | --- | --- | --- |
| intake-2 − intake-1 | Temp °C | 0.31 | 0.42 |
| intake-2 − intake-1 | SM clock MHz | 0.12 | 0.01 |
| intake-2 − intake-1 | Board W | -2.41 | -1.22 |
| intake-2 − intake-1 | GPU % | -0.43 | -0.43 |
| intake-3 − intake-2 | Temp °C | -0.31 | -0.43 |
| intake-3 − intake-2 | SM clock MHz | -0.23 | -0.02 |
| intake-3 − intake-2 | Board W | 0.85 | 0.43 |
| intake-3 − intake-2 | GPU % | 0.43 | 0.44 |
| intake-exhaust-2 − intake-exhaust-1 | Temp °C | 0.04 | 0.05 |
| intake-exhaust-2 − intake-exhaust-1 | SM clock MHz | 0.21 | 0.02 |
| intake-exhaust-2 − intake-exhaust-1 | Board W | 1.09 | 0.56 |
| intake-exhaust-2 − intake-exhaust-1 | GPU % | 0.52 | 0.53 |
| intake-exhaust-3 − intake-exhaust-2 | Temp °C | 4.08 | 6.17 |
| intake-exhaust-3 − intake-exhaust-2 | SM clock MHz | -2.35 | -0.18 |
| intake-exhaust-3 − intake-exhaust-2 | Board W | 0.04 | 0.02 |
| intake-exhaust-3 − intake-exhaust-2 | GPU % | -0.23 | -0.23 |

## Exhaust effect (B − A)

| Metric | A mean | B mean | Mean Δ | Mean Δ % | Observed max Δ |
| --- | --- | --- | --- | --- | --- |
| Temp °C | 73.49 | 67.39 | -6.10 | -8.30 | 0.00 |
| SM clock MHz | 1319.94 | 1322.92 | 2.98 | 0.23 | 0.00 |
| Board W | 196.95 | 194.76 | -2.19 | -1.11 | -3.40 |
| GPU % | 99.73 | 99.71 | -0.02 | -0.02 | 0.00 |

Temperature percentage deltas use °C numerically and are not thermodynamic ratios; use absolute °C differences for interpretation. Runs are sequential and not paired independent trials. Fan-curve feedback, ambient drift, workload variation and warm-up can confound results. Cooling telemetry is not an inference-speed benchmark or quality test.

Setup/workload/ambient declarations and commands are preserved in [queue state](state/queue-state.json). Incomplete attempts remain in state/results and are excluded, not silently retried.
