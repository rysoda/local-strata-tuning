# Minimum reliable VRAM reserve — P100 x16 + 1080 Ti x4, 256K

[Campaign index](../../README.md) · [Plan](PLAN.md) · [Manifest](manifest.json) · [Work log](NOTES.md) · [Report](REPORT.md) · [Live results](RESULTS.md)

**Complete: 19 benchmarks.** Smallest tested passing explicit reserves: **P100 0 MiB / 1080 Ti 0 MiB**. Nearby repeat mean: **40.19 decode / 259.36 prefill tok/s**, versus control **37.01 / 324.54** (**+8.60% decode, −20.08% prefill**). Zero is the tested allocation floor, **not an unqualified fastest-overall recommendation**. Combined minimum/control/repeat each passed 7/7 smoke checks, including 230146 actual prompt tokens; the separate projection-enabled compatibility check also passed. Very little spare VRAM remained; no universal reliability claim. Startup is unchanged; test servers are stopped.

Previous completed tuning queues were not reopened. User explicitly requested the smallest reserves on both cards, not an arbitrary amount of unused memory.

## Fixed comparison

- P100 GPU 0, TCC, CPU PCIe 3 x16; 1080 Ti GPU 1, WDDM/display, chipset PCIe 3 x4. No card moves.
- **36 P100 layers / 12 1080 Ti Main layers**, dense-stage trim. No split changes during reserve comparison.
- IQ3_S, **262144 context**, int8 KV / 32768 resident cells, full experts, MTP spec4/min-p0.5 and existing reasoning unchanged.
- Explicit engine/Control 0.1.57 CUDA12, BetterBench 0.6.1; frozen source/model/input inventory. No upgrades.
- Open case, intake + exhaust, 75°C target, intake capped at 45% for noise; keep fixed. No other GPU apps/background graphics workload added.
- Scientific reserve search has **no speed projection**. A separately labeled final compatibility check keeps the user's existing projection. Do not pool those performance results or imply quality equivalence.

## Search and validation

Fresh control **1400/2304 MiB** with the exact BetterBench workload and seven functional/tool/recall smokes. Then vary each card independently, testing **700 → 512 → 256 → 128 → 64 → 0 MiB** while keeping the other at its control reserve. At a failing boundary, refine integer MiB by bisection. No negative reserves; zero is explicitly supported by the reference parser and must be checked in actual startup logs.

Each candidate runs exact BetterBench quick code decode plus 16K-target prefill, no concurrency. No arbitrary 1 GiB free-memory acceptance rule. Expected allocation/stall boundary attempts are preserved and explicitly classified; unexpected errors, fallback/changed quality, numerical failures or thermal anomalies pause. Severe throughput loss (over 25% below fresh control in either metric) is a predeclared usability rejection, not proof of paging.

Validate the independently found P100 floor with the display card reserved, then validate the combined pair. If extended checks expose an allocation boundary, refine upward against the known passing control. Final minimum/control/minimum repeats each include seven checks, including ~230K actual-token recall. The projection-enabled compatibility arm is separate. Smallest *tested passing* values under current conditions are not a universal reliability guarantee; bisection assumes a local monotonic boundary and results can vary with driver/desktop/cache state.

**A zero explicit flag does not mean zero internal safety budgeting.** Reference source separately accounts for CUDA late allocations (~256 MiB), later-stage windows and MTP/head. Capture effective reserve, expert counts and observed per-card free memory rather than equating the knob with actual free VRAM.

## Operation

```sh
python campaigns/2026-11-07-p100-x16-1080ti-x4-reserve-floor/scripts/run.py
# Default validates only. Explicit start/resume after checking actual processes:
python -u campaigns/2026-11-07-p100-x16-1080ti-x4-reserve-floor/scripts/run.py --run
```

Do not start a second copy. Exclusive `state/reserve.lock`; `state/STOP` pauses between runs. Incomplete/unreviewed attempts require explicit review, not deletion or silent retry. Keep all raw files. Saved PIDs are not ownership proof. Supervisors stop only verified owned children. No planned idle checkpoint between screening, refinement, confirmation and reporting; unexpected errors pause.

Isolated test server: **127.0.0.1:8080**, presets disabled. **Startup and installed presets remain unchanged.** The existing normal Strata launch was stopped only after verifying its live command tree to avoid competing inference. Private baseline/original snapshots and downloaded full source remain ignored in `configs/private/`. Redact public profiles with `python tools/publish_configs.py --campaign 2026-11-07-p100-x16-1080ti-x4-reserve-floor`.

Progress: `state/queue-state.json`; supervisor log: `state/reserve-supervisor.log`; results: immutable per-attempt JSON/HTML/logs/UUID-labeled GPU CSV, standard and extended smoke artifacts. Failed attempts remain evidence. See PLAN/NOTES for research, acceptance rules, provenance and limitations.
