# Three-run diagnostic plan

User requested three quick benchmarks after engine 0.1.57 → 0.1.59. Measure the already running user server without modifying settings, managing its lifecycle, downgrading or tuning. New software boundary gets a new campaign. Preserve current 262144 context rather than reverting to the older 128K default.

Three sequential identical BetterBench runs: `--quick --decode --categories code --prefill --no-concurrency --config workloads/betterbench-16k.json`. Shared tools/benchmark.py parses all results. Require 5 decode / 8 prefill samples per run; retain all raw data/errors and GPU telemetry. Compare means of per-run medians, not selected maxima.

The current experimental projection is retained ONLY as the as-found diagnostic baseline. No quality or projection recommendation. Historical projection-free same-topology results and projected x8/x8 results are both confounded; report numeric changes descriptively, not as engine-caused gains/regressions. Cooling changed since those campaigns. No tuning candidates, research-driven parameter changes, projections of performance, or quality reductions will be tested. No generated code execution; no smoke/long-context checks in this speed-only request.

Preflight checks idle API, engine version, installed profile hash, current processes and topology. Never start/stop the user server. Lock supervisor, pause between runs with state/STOP, skip completed runs, refuse ambiguous incomplete or failed state. Preserve failures for review. Completion is durable and prevents repeating work.
