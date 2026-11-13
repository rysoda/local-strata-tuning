# Dual P100 decode tuning — reasoned plan

## Fixed boundary and baseline

Two P100 16GB TCC, PCIe 3 x8/x8, i5-11400F (6C/12T), ~63.9 GiB RAM, Windows 11 26300, NVIDIA 582.99. Installed CUDA12 engine 0.1.59 / Control 0.1.57 / BetterBench 0.6.1. No upgrade. Target IQ3_S, 262144 context, int8 KV, resident32768, MTP spec4/min-p0.5, full experts, same weights and reasoning throughout.

Original installed profile and Startup saved privately, hardware/software/startup logs and original health/metrics captured. Existing deployed 36/12 split with experimental projection has three completed quick benchmarks in ../2026-11-12-dual-p100-deployment/REPORT.md (32.001 decode / 344.609 prefill). Those are original behavior, not the quality reference. All tuning arms remove the projection: it is not a speed optimization. Create a fresh projection-free 36/12 full-expert reference, then change one setting at a time. Preserve installed originals and boot launcher. Temporarily stop the verified user server to run localhost/presets-disabled isolated profiles; return a ready launcher/profile, not silently overwrite Startup.

## Research (2026-11-13)

Read official https://www.stratat.com/en/changelog and https://github.com/Niko1221/Strata/releases. Latest app/Terminal 0.2.13, engine 0.1.59 (already installed); Windows Terminal Control can remain older. Read official v0.2.13 docs SETTINGS.md (full switch register), OLDER_GPUS.md, MULTI_GPU.md, SPLIT_ENGINE.md and relevant DETAILS.md sections; original snapshots in results/upstream-v0.2.13-*.md. Installed binary --help captured afresh; option strings found for DOWN_WS, ARENA_PIN_GIB, PATTN_SM60 and MMQ_WS. Do not treat the old repository source submodule as current engine evidence.

## Small reasoned candidate set

| Arm | Sole change from indicated reference | Reason / source |
|---|---|---|
| reference36 | Original 36/12, no projection | Full-expert same-quality speed reference; 640/896 reserves unchanged |
| split24 | Split 24/24 vs reference36 | MULTI_GPU: per-layer caches, contiguous stages. Identical x8 cards no longer justify mixed-card 36/12; head/MTP on later stage. Check actual placement/slots. |
| split24-pipeline | --pipeline-windows 2 vs split24 | MULTI_GPU: overlapped speculative windows; target verified, CPU rounding caveat. Installed help supports it. Budget extra windows and MTP on stage0. |
| split24-downws | STRATA_DOWN_WS=1 vs split24 | OLDER_GPUS: GP100 bit-exact mode0/8 down kernels for IQ4_NL/Q2_0. No weight or routing change; microbench evidence only, verify real startup/request behavior. |
| split24-pin0 | STRATA_ARENA_PIN_GIB=0 vs split24 | MULTI_GPU: Windows split caps registered arena at 8 GiB; both current cards TCC, but original startup still reports WDDM cap. Test full arena registration to reduce staging; keep pin-reserve guard and pause if allocation fails. |

### Reviewed follow-up after first screens

Split24: 40.628 decode vs fresh reference 32.042 (+26.8%). Pipeline2: 43.599 (+7.3% over split24); DOWN_WS 41.077 (+1.1%, too small to carry forward without evidence); full arena pin 39.583 (-2.6%) / 377.672 prefill (+8.7%). Review pin0 as a prefill tradeoff, not a decode win. Installed startup explicitly says pipeline2 leaves MTP on last card unless STRATA_MTP_STAGE0=1, unlike the current doc's stated default. Therefore add `split24-pipeline-stage0` (only MTP placement vs pipeline2), then `split24-pipeline-stage0-pin0` (only full arena registration vs stage0). This tests the documented overlap placement and whether the worthwhile prefill pinning gain survives with pipeline. No DOWN_WS combination: marginal screen gain.

Only proceed with split24-based arms after reviewing split24 baseline. If 24/24 loses materially, test the more even but head-biased 28/20 split instead and document before adding runs, not an arbitrary sweep. Combine only worthwhile individual settings. Choose decode first, but flag prefill regression and headroom; confirm selected combination / nearby reference / repeat. STOP pauses between runs, errors require review, completed runs are never silently repeated.

### Confirmation selection

First-card MTP screen lost: 40.328 decode; adding full pinning yielded 41.476 / 378.005, still below last-card MTP pipeline's 43.599 decode. For the requested decode-first goal select 24/24 + pipeline2, keep last-card MTP explicitly (`STRATA_MTP_STAGE0=0`), keep original 8 GiB arena pin cap and reserves640/896. Candidate-a / reference36 / candidate-b nearby confirmations; reference and candidate-b each get the same 7 smoke checks including ~230K-token retrieval. No further option sweep. Full pinning remains a measured prefill tradeoff, not the decode recommendation.

## Exclusions

No IQ changes, pruning, tail skipping, routing priors, projections, shortened reasoning/context, KV precision changes or dense Q8 conversion (would change weights). New all-cards split engine requires Linux, supported newer cards, full expert residency and <=128K: not suitable for this Windows Pascal 256K machine. EXPERT_NIBBLE needs full expert residency and more VRAM, unavailable here. Q8_SM60 needs converted dense weights, excluded. ADAPT_FETCH and ADAPT_OVERLAP are single-GPU modes, not these layer splits. SPLIT_OVERLAP official NVIDIA numbers are within noise; not a first candidate. PATTN_SM60/MMQ_WS target prefill rather than primary decode and MMQ_WS needs full-resident layers. Seven P100 scheduling defaults already activate on two sm60 GPUs; do not claim them as new optimizations. Do not alter clocks, GPU modes, privileges, fans or pagefile.

## Measurement and acceptance

Every screen uses exact `--quick --decode --categories code --prefill --no-concurrency --config <repo>/workloads/betterbench-16k.json`. Capture all original samples/errors/token counts plus per-device temperature, clock, free VRAM, power, thermal flags at 2-second intervals, startup and before/after metrics. Freeze engine/server/BetterBench/workload/expert-profile hashes; model artifact size+mtime. Fresh isolated server per arm, localhost binding, STRATA_NO_PRESET=1. Do not execute generated code. Quick mode is screening, not statistical significance or intelligence equivalence.

Inspect MTP/context/KV/placement, no automatic retry, no non-finite/fatal/allocation errors. Pause on thermal flags or >=85C. Functional/tool/32K/~119K and above-128K (~230K tokens) recall smoke on selected profile before recommending. If a candidate fails, preserve evidence and explicitly review; no automatic retries. Stop owned test processes; user deployment after testing is separately recorded.
