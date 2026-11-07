# Cooling comparison plan

## Question and fixed boundary

Does adding an exhaust fan improve P100 cooling/maintained SM clocks with a 120×38 mm nominal 4000 RPM server intake fan, whose curve reaches 100% at 75°C?

This is user-requested physical cooling work, not a software parameter search. Reuse the existing read-only NVIDIA monitor after inspecting its implementation: timestamped CSV, sample-and-hold time-weighted means, final interval included, partial/error status retained. Its CSV provides observed maxima and all requested raw data without changing the historical monitor. No external performance assertion or projected optimization is needed.

Keep P100 GPU UUID, installed engine/Control 0.1.55, IQ3_S target weights, full expert routing, int8 KV, context 131072/resident 32768, clocks/power limits, case/shroud, workload and intake curve fixed. Existing server remains normally network-accessible; no test API clients/benchmarks are launched here. Snapshot live health, inference configuration fingerprint excluding credentials, process commands and GPU telemetry before captures.

## Six-run schedule

| Order | Setup | Captures | Duration each | Sampling |
| --- | --- | --- | --- | --- |
| 1–3 | Intake + exhaust (B), already installed | intake-exhaust-1, intake-exhaust-2, intake-exhaust-3 | 600 s | ~1 s |
| Manual change + warm-up | Remove exhaust; do not change intake | None | ≥5 min; prefer stable plateau | No automated capture |
| 4–6 | Intake only (A) | intake-1, intake-2, intake-3 | 600 s | ~1 s |

Order revised at measurement authorization to match both fans already installed; user reports 15 minutes of heat soak before B. Warm up A after the physical change too. Groups are sequential; run numbers are not independent paired trials. If room temperature drifts or load becomes inconsistent, mark the result limited rather than attributing every change to the exhaust. A later reversed-order confirmation would be separate additional work, not silently added runs.

## Required declarations before measurement

- User confirms physical B is installed and prefill-only stress is active; exact command/settings remain uncaptured, a comparison limitation. Keep the workload unchanged for A.
- Confirm case open/closed, shroud arrangement, fan placement/orientation; lower-temperature intake curve and any controller hysteresis.
- Record exhaust model, position and speed for B. Do not assume historical rear-pull fan configuration is unchanged.
- Record observed warm-up time and preferably ambient temperature per setup. Equilibrium is user-observed, not automatically proven.
- The 4000 RPM label is nominal; no tachometer measurement is implied. At lower temperatures the fan may run below 100%, making this a comparison of complete airflow/controller setups, not necessarily fixed intake airflow.

## Tables and decision rule

Per run: mean/min/max/population time-weighted SD of GPU temperature, SM clock, board power, utilization; board Wh, seconds, sample count, maximum gap, raw links. Mean SM clock is not equivalent to inference throughput.

Per group: number of runs, mean of run means, sample SD across run means, range across run means, highest observed sample. Report signed differences between consecutive runs and B minus A absolute/percent mean differences plus observed maximum differences. Prefer absolute °C deltas; Celsius percentages are not thermodynamic ratios. Retain failed/incomplete attempts, exclude them explicitly and require review before recovery. No automatic replacements.

Interpret lower GPU temperatures and/or higher sustained clocks at comparable utilization/workload as descriptive cooling evidence. Power and energy help explain operating point but exclude fan power and are not standalone efficiency conclusions. No significance, intelligence-equivalence, inference-speed or general cooling recommendation until the six captures are reviewed. Update final report, manifest, state and index durably; leave the pre-existing user-managed server/workload untouched.
