# Rear pull fan — plan

New physical setup, separate from completed open/closed-case cooling comparisons. User requested only starting Strata, P100-only at 131072 context; do not automatically run BetterBench or a stress test.

Reuse archived x8-p100-only settings: unchanged IQ3_S weights, full routing (prior/tail skip zero), int8 KV, 32768 KV residency, engine/Control 0.1.55. Installed Control server source confirms GPU 0 maps to CUDA_VISIBLE_DEVICES=0. Confirm actual startup logs and readiness. No tuning or software upgrade.

Before measuring: confirm case/shroud state, fan placement/direction/speed, ambient conditions and exact user stress workload. Capture a fresh baseline and alternate physical arrangements with the same workload after stabilization. Preserve raw telemetry, errors and partial attempts. Historical measurements are context, not controlled references. No inference-speed or quality claim from cooling telemetry.
