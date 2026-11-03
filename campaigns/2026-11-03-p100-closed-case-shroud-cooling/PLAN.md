# Closed-case shroud cooling — measurement and review plan

## Boundary

Retrospective organization of measurements already collected on 2026-11-03, not a preregistered experiment or a new workload launch. Closed case and fan shroud distinguish this comparison from the open-case unducted campaign. The auxiliary fan at the shroud edge draws outside air inward. Compare it off versus commanded 25%, 50%, 75% and 100%; retain the primary fan throughout.

## Method

User-managed P100-only Strata prefill stress load; passive NVIDIA telemetry, 600 seconds per run, approximately one-second sampling. Exact workload invocation/software, fan RPM/geometry and ambient temperature were not captured. Do not infer versions from another campaign. No BetterBench substitution or inference settings changes.

Preserve all 11 completed runs and verify CSV-derived sample-and-hold means against JSON, GPU identity, duration, errors, load and power limit. Report actual order, not an assumed ascending sweep. Mark the first off run as suspected warm-up based on the user's account; use 1bis and 2 as a balanced two-run reference and show the all-three sensitivity result. Inspect final-five-minute power to check opening transients.

## Interpretation and follow-up

Use power with clocks, temperature and utilization, not temperature alone. Limit conclusions to this arrangement and load; no efficiency, throughput, significance or model-quality claims. Future confirmation should record ambient/inlet temperature, RPM, throttle reasons and actual throughput, allow stabilization, and alternate off against an enabled setting. Preserve unique raw runs and partial failures. No queue, server or workload is launched by this review.
