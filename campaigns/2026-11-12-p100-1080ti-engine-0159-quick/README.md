# Strata 0.1.59 — three quick speed checks

[Manifest](manifest.json) · [Plan](PLAN.md) · [Work log](NOTES.md) · [State](state/queue-state.json)

Three sequential BetterBench quick code decode + 16K-target prefill benchmarks against the existing user server. Engine0.1.59 / Control0.1.57, P100 x16 + 1080Ti x4, IQ3_S, 256K, int8, MTP, full experts, 36/12 trimmed split, reserves640/896. Existing projection retained as a diagnostic baseline, not validated or recommended.

Historical 0.1.57 evidence differs in projection or topology/cooling; numerical comparisons cannot isolate engine-update effects. All raw samples/errors, actual tokens, telemetry and API metrics go to results/. No user server restart, profile modification or generated code execution.

Run/resume: `python campaigns/2026-11-12-p100-1080ti-engine-0159-quick/scripts/run.py`. Only planned/paused state is resumable; incomplete/failed state needs explicit review. Complete refuses repeats. `state/STOP` pauses between runs. **Complete: 3/3 valid benchmarks.** Mean decode **38.431 tok/s**, prefill **329.728 tok/s**. [Final report](REPORT.md). No clear speed improvement established; historical references are confounded.
