# Server intake fan: cooling comparison

Completed captures: **0/6**. No comparative conclusion until both groups have three valid runs.

A = 120×38 mm nominal 4000 RPM intake only. B = same intake plus exhaust. Intake curve reaches 100% at 75°C (user-reported; actual RPM not measured).

Means/within-run SD are time-weighted sample-and-hold. Max/min are observed samples, not continuous extrema. Board power excludes external fan power. All temperatures are absolute GPU temperatures; ambient-adjusted comparisons require ambient measurements.

## Per-run telemetry

| Run | Temp °C mean | min | max | SD | SM clock MHz mean | min | max | SD | Board W mean | min | max | SD | GPU % mean | min | max | SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Sampling and energy

| Run | Seconds | Samples | Max gap s | Board Wh | Raw summary |
| --- | --- | --- | --- | --- | --- |

## Group summaries

Across-run SD/range describe repeatability of run means, not independent sample uncertainty.

| Setup | n | Metric | Mean of run means | Across-run SD | Run-mean range | Highest observed |
| --- | --- | --- | --- | --- | --- | --- |

## Differences between consecutive runs within each setup

Signed difference = later run minus previous run.

| Comparison | Mean metric | Difference | % of previous |
| --- | --- | --- | --- |

## Exhaust effect (B − A)

Pending three completed runs per setup.

Temperature percentage deltas use °C numerically and are not thermodynamic ratios; use absolute °C differences for interpretation. Runs are sequential and not paired independent trials. Fan-curve feedback, ambient drift, workload variation and warm-up can confound results. Cooling telemetry is not an inference-speed benchmark or quality test.

Setup/workload/ambient declarations and commands are preserved in [queue state](state/queue-state.json). Incomplete attempts remain in state/results and are excluded, not silently retried.
