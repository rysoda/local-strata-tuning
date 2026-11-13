# Dual P100 decode tuning — final report

**Selected: 24/24 layer split + `--pipeline-windows 2`, keeping MTP on the last card (`STRATA_MTP_STAGE0=0`).** Retain trimmed stage weights, reserves 640/896 MiB, IQ3_S, 262144 context, int8 KV, resident32768, full expert routing, spec4/min-p0.5 and existing reasoning behavior. No model conversion, software upgrade, precision reduction, pruning or routing approximation.

[Plan and research](PLAN.md) · [Every attempt](RESULTS.md) · [Recovery/work log](NOTES.md)

## Nearby confirmations

Fresh isolated localhost server per run, presets disabled. All main arms have **no experimental projection**. Candidate A / reference / candidate B order; smoke checks happen after each applicable benchmark, not during timing.

| Run | Decode tok/s | Prefill tok/s | Smoke |
|---|---:|---:|---|
| Candidate A | 44.660 | 347.259 | — |
| Nearby 36/12 reference | 31.696 | 345.886 | 7/7 |
| Candidate B | 47.632 | 347.571 | 7/7 |
| **Candidate mean of two per-run medians** | **46.146** | **347.415** | |
| **Change vs nearby reference** | **+45.59%** | **+0.44%** | |

Each benchmark retained 5/5 valid code decode and 8/8 valid prefill measurements. Exact command workload: `--quick --decode --categories code --prefill --no-concurrency --config <repo>/workloads/betterbench-16k.json`. The prefill target is corpus length, not exact model tokens; candidate confirmations used 11969–12254 actual prompt tokens. All raw samples, counts and errors remain in results/*.json. BetterBench 0.6.1 marks p99 statistics under-sampled; no tail-latency claim.

Candidate repeats differ by ~6.7% in decode. Quick mode, output-dependent draft acceptance, restart/cache history and sequential thermal conditions limit precision. This is a substantial repeated screening improvement, **not statistical significance or comprehensive intelligence equivalence**. Prefill's small difference should be read as essentially unchanged.

## What was tried

| Projection-free screen | Decode tok/s | Prefill tok/s | Decision |
|---|---:|---:|---|
| Fresh original 36/12 | 32.042 | 345.869 | Reference |
| Balanced 24/24 | 40.628 | 347.365 | Keep: +26.8% decode in this screen |
| 24/24 + pipeline2, MTP last | 43.599 | 346.859 | Keep; confirmed above |
| 24/24 + GP100 `STRATA_DOWN_WS=1` | 41.077 | 345.334 | ~1.1% decode vs 24/24, too small to carry forward |
| 24/24 + full arena pin (`STRATA_ARENA_PIN_GIB=0`) | 39.583 | 377.672 | Prefill tradeoff (+8.7%); not selected for decode-first use |
| 24/24 + pipeline2, MTP first | 40.328 | 346.229 | Slower than MTP last |
| Previous arm + full arena pin | 41.476 | 378.005 | Still below selected decode; not selected |

The old mixed-card 36/12 assignment put disproportionately many layers on the first of two identical cards. Official docs explain that the normal layer split is serial between stages, not a guarantee of twice the throughput. The larger second-card expert cache alone does not ensure balanced work. Pipeline windows overlap speculative work across windows; target tokens are still verified. Their extra buffers consume cache room and the hardware-dependent MTP placement matters.

The installed engine prints that pipeline2 keeps the drafter on the last card unless explicitly moved, unlike the current online doc's stated first-card default. We tested both instead of assuming the docs matched the binary. The candidate's startup confirms two verifiers per stage, split24, original KV/context and MTP. It keeps 272 MiB of CUDA0 out of the expert cache for extra verifiers/state. Candidate B loaded 6708 first-stage and 5225 second-stage expert slots.

## Research and version compatibility

Official [changelog](https://www.stratat.com/en/changelog), [releases](https://github.com/Niko1221/Strata/releases), v0.2.13 [settings register](https://github.com/Niko1221/Strata/blob/v0.2.13/docs/SETTINGS.md), [older GPU guide](https://github.com/Niko1221/Strata/blob/v0.2.13/docs/OLDER_GPUS.md), [multi-GPU guide](https://github.com/Niko1221/Strata/blob/v0.2.13/docs/MULTI_GPU.md), [all-cards split engine](https://github.com/Niko1221/Strata/blob/v0.2.13/docs/SPLIT_ENGINE.md), and DETAILS sections reviewed. Snapshots are in results/upstream-v0.2.13-*.md; installed --help captured separately.

Latest app/Terminal release is 0.2.13; its engine is 0.1.59, already installed here. Kept installed Control 0.1.57, CUDA12 engine 0.1.59, Windows 11 26300, NVIDIA 582.99, two P100 16GB TCC on PCIe 3 x8/x8, i5-11400F, ~63.9 GiB RAM. Input hashes and model file size/mtime frozen. The seven sm60 scheduling defaults were already active, not newly discovered gains. The newer all-cards split engine is Linux-only, needs full expert residency and <=128K; inappropriate here. Q8 dense conversion and full-resident nibble slots were excluded, as were precision/routing/context/reasoning cuts. No driver modes, clocks, privileges, cooling or pagefile changes.

## Quality and memory checks

Reference and candidate B each passed the same **7/7** checks: three functional tracing tasks, one tool call, recall at **32151**, **119151**, and **230146 actual API prompt tokens**. Raw responses retained in *.sanity*.json. Generated code was **never executed**. These are smoke checks only; last-bit differences from arithmetic grouping, cache placement and pipeline scheduling are not proof of comprehensive quality equivalence.

Candidate A/B sampled minimum free VRAM was **526 MiB on GPU0 / 738 MiB on GPU1**; candidate B telemetry includes long-context checks. Startup reported 795/930 MiB before all verify captures. Candidate B peaked at 76/71°C; no sampled thermal-throttle flags. The nearby reference peaked at 75/61°C. Two-second samples are not continuous guarantees. Headroom is conditional on this TCC setup and workload; future workloads or other GPU clients can exhaust it. No fatal/allocation/non-finite/restart errors in accepted arms.

## Reviewed exclusions and original behavior

Ten accepted benchmark runs; two excluded attempts preserved. Initial `reference36` and `split24` profiles retained launcher `user_args` metadata, which Control merges over edited `args` independently of preset disabling. It reintroduced projection and the old split. Startup-log checking caught it; both are rejected, not speed evidence for the requested arms. Preserved pre-recovery state/baseline/frozen inputs; sanitized isolated copies, re-froze and used unique v2 IDs. Added an effective-command gate before subsequent benchmarks. Never changed the installed profile to work around it.

Original deployed behavior remains separately recorded in ../2026-11-12-dual-p100-deployment/REPORT.md: projected 36/12 averaged 32.001 / 344.609. Do not attribute the recommendation's entire difference from that historical diagnostic to one variable. Main reference/candidate comparison here is projection-free; projection was not used as an optimization and is absent from the ready profile.

## Ready profile and completion

- Ready private profile: `configs/private/recommended.json`; redacted copy in `configs/shareable/` via publication tool.
- Launcher: `../../launchers/Run-Dual-P100-Tuned.cmd` (localhost:8080, refuses occupied port, presets disabled).
- Validate without launching: `python tools/launch.py 2026-11-13-dual-p100-decode-tuning --check`.
- Original installed profile, Startup batch and credentials preserved unchanged. **Boot still uses the old settings until separately updated.**
- Queue complete, no supervisor/test engine left running; completed work cannot repeat. Any separately launched user deployment is recorded in NOTES.md. No universal maximum-speed or quality-equivalence claim.
