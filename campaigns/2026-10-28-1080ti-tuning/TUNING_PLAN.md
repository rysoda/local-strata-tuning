# Strata tuning plan and checkpoint

> Layout migrated after completion. Use [README.md](README.md) for current navigation/launch/resume instructions. Historical commands below retain original measurement paths; the shared workload is now repository `workloads/betterbench-16k.json`, private profiles `configs/private/`, queue metadata `state/`, and pinned source repository `research/strata-source/` (not campaign-local research).

**Completed 2026-10-29.** See `FINAL_REPORT.md` for the selected combination, confirmed nearby-reference comparison, quality caveats and ready-to-run profile. 54 benchmark runs completed; one incompatible startup retained. No benchmark server remains running. The research/initial execution notes below are preserved as history.

## Scope and invariants
- Read `AGENTS.md` on 2026-10-28. Use the existing installation, **qwen3.8-flash-next-iq3_s**, **131072** context, original target weights and int8 KV throughout.
- Prioritize code decode, then cold 16K prefill. No reduced context, target quantization, expert pruning, reduced reasoning, control vectors, routing bias, or skipped experts as optimizations.
- Never modify the installed profile. Copies in `configs/` contain local credentials: do not publish them.
- Engine 0.1.52, CUDA 12.9 release binary, build commit `a42cc3d7df70d1940de82cd0882f03e1f5dfc741`; Control 0.1.51. Research source pinned to that engine commit in `research/strata-source/`; no upgrade or rebuild of the installed engine.
- BetterBench 0.6.1, local checkout commit `f72bb9011a830fd98e82ab89d01e549efa76e9c5`.
- Hardware: GTX 1080 Ti 11 GiB (Pascal sm_61), driver 582.66, i5-11400F 6C/12T, 63.9 GiB usable RAM. Engine PCIe probe ~12.7 GB/s. Windows/WDDM; desktop display uses this GPU.

## Measurement
Exact requested workload for **every measured run**:
```
betterbench run --endpoint http://127.0.0.1:8080/v1 --model qwen3.8-flash-next-iq3_s --quick --decode --categories code --prefill --no-concurrency --config C:/ai/tuning/16k.json --out <unique-result.json>
```
API key supplied through environment, not command line. `16k.json` contains only `{"prefill_depths":[16384]}`. Preserve BetterBench defaults, sampling and corpus; do not silently add greedy, shorten outputs or reduce prefill repeats. Five decode passes are screening, not statistical proof. Cold prompts have fresh nonces; restart between settings to reset expert adaptation. Record median code decode, median prefill, errors, raw JSON, HTML and logs. The benchmark's approximate 16K synthetic text can tokenize to a different actual length; retain actual counts.

## Baselines and quality caveat
1. **baseline**: untouched existing 128K engine arguments and environment. Only isolate paths, resolve installed executable, bind loopback and turn off browser opening. Started PID 5908; supervisor initially PID 15308; see `results/baseline.*` for current state.
2. **quality-reference**: same configuration, **only** `STRATA_ROUTE_TAIL_SKIP=0` added. Installed `STRATA_ROUTE_PRIOR=0` stays off. Engine startup confirms tail skip 7 is on in the untouched baseline: it omits routed experts. Disabling this is a quality restoration, not a speed win. Single-parameter performance comparisons will use this quality-preserving reference, with original baseline also retained.
3. All subsequent experiments inherit the quality reference, change exactly one setting, and keep all target experts active. Different CPU/GPU grouping and speculative windows can change last-bit rounding; byte-identical output is not promised. Speed tests alone cannot prove model quality. Do not claim a globally quality-neutral winner without correctness review.

## Evidence gathered
- [Engine/server reference](https://github.com/Niko1221/Strata/blob/a42cc3d7df70d1940de82cd0882f03e1f5dfc741/docs/DETAILS.md): scheduling, default approximations, cache memory, CPU affinity, opt-in switches, numerical caveats.
- [Community benchmarks](https://github.com/Niko1221/Strata/blob/main/docs/COMMUNITY_BENCHMARKS.md): compare architecture-specific results, not RTX speeds directly with Pascal.
- [Pascal P40 kernel report](https://github.com/Niko1221/Strata/blob/main/bench/results/2026-10-12-p40-sm61-kernels/README.md): same sm_61 architecture and IQ3_S, default exact Pascal kernels, thermal and GEMM shape traps. Dense FP32 switch is only bitwise validated with cuBLAS 12.4.5.8, NOT installed 12.9.
- [Community tuning issue #3912](https://github.com/Niko1221/Strata/issues/3912): six-core Windows host affinity, cache adaptation, KV residency and WDDM headroom; results confounded by several simultaneous changes, not proof of individual gains.
- [BetterBench README](https://github.com/GGZ14/BetterBench) and local `config.py`, `runner.py`, `cli.py`: quick-mode limitations, actual repeat counts, output schema and cold prefill behavior.
- Searches included GTX 1080 Ti/Pascal, pool workers, expert cache, GitHub and Reddit/forum tuning. No trustworthy directly comparable 1080 Ti result found; use local measurements, not generic GPU advice.
- Installed `--help` captured in `research/engine-help.txt`; parser defaults verified in pinned `src/program/generate.cpp` (several useful flags are absent from help).

## First-stage candidate list (one setting per run)
Defaults: host first; 5 pool workers + host; 18 tasks; auto PCIe share (~0.25 after adaptation); spec 4 / min-p .5; suffix 3; lookup-chain 0; adapt interval 4 / swaps 96 / decay .7; KV resident 32768; prefill auto chose 4864; reserve 700 MiB, **only 560 MiB free at startup**; direct PLE measured slow at 8636 rows/s.

| Family | Values to test independently | Why worthwhile / quality gate |
|---|---|---|
| PLE I/O | `--ple-io mmap` | Baseline warns direct SSD rows are slow. Same table and values; monitor RAM/page pressure. |
| VRAM reserve | `--vram-reserve-mib 1400` | WDDM paging risk at 560 MiB free; fewer cache slots may still be faster. |
| KV residency | `--kv-resident 20480` | Supported minimum; more expert slots, still full 128K available via streaming. 16K test does not measure long-context streaming cost. |
| Host placement | `--host-core last`, `sibling` | Avoid core-0 interrupt contention; scheduling only. |
| Workers | `--pool-workers 4`, `3` | RAM bandwidth and contention can saturate before six cores. No SMT oversubscription. |
| Pool task granularity | `--pool-tasks 36`, `72` | Balance unequal row work vs scheduling overhead. |
| PCIe split | `--pcie-frac 0.15`, `0.40` | Bracket observed auto .25 on PCIe 3-class bandwidth; CPU/GPU compute identical experts, different rounding permitted. |
| Adaptive PCIe split | `STRATA_PCIE_BALANCE=1` | Exact per-layer load balance; uncertain on Pascal, measured elsewhere. |
| Spec window | `--spec 3`, `5` | GPU verify cost vs accepted tokens; all proposed tokens target-verified. |
| Spec confidence | `--spec-min-p 0.3`, `0.7` | Draft acceptance vs window overhead. Never changes target weights. |
| Lookup continuation | `--lookup-chain 2` | Code repeats; target verifies proposals. |
| Suffix lookup | `--suffix-draft 0` | Determine whether lookup overhead exceeds acceptance benefit on Pascal. |
| Draft vocabulary | `--mtp-draft-vocab <installed data/draft_vocab_en.bin>` | Smaller speculative-only head leaves VRAM for real experts; non-English target still unchanged, only drafts narrower. |
| Draft quantization | `--mtp-q4 all` | ONLY draft layer quantized; target remains IQ3_S and verifies every proposal. Do not confuse with target/KV quantization. |
| Adapt frequency | `--adapt-every 1`, `8` | DDR4 cache miss cost vs swap overhead. |
| Adapt budget | `--adapt-swaps 48`, `160` | Same experts computed, placement only. |
| Adapt history | `--adapt-decay 0.9` | Stabilize placement on coding text vs slower reaction. |
| Async adaptation | `--adapt-async 1` | Overlap transfers rather than block; not bit-exact due to placement timing. |
| Adaptive overlap | `STRATA_ADAPT_OVERLAP=1` | Existing RAM arena, single GPU; verify startup actually enables it and does not conflict with auto async. |
| Prompt chunk | `--prefill 4096`, `2048` | Pascal GEMM shape/memory tradeoff; smaller chunks may beat auto 4864, keep all prompt tokens. |
| Head alias | `--prefill-head-alias` | Small VRAM card: lends output head storage during prompt, restores before decoding. |

## Excluded / deferred with reasons
- `STRATA_ROUTE_PRIOR`, resident routing biases, tail skipping: computation changes; OFF, not tuned for speed.
- `--kv q4_0` / `k8v4`, target quant changes, speed projections, no-PLE, expert pruning, reducing thinking/context: quality changes, excluded.
- `STRATA_DENSE_F32=1`: Pascal-relevant and promising, but cuBLAS **12.9** parity unverified. Deferred until `gemm_f32_parity` can validate installed library; do not assume P40/12.4 evidence transfers.
- sm_61 table/wide dequant: already enabled, no reason to disable known exact fast paths. sm_60, sm_70, sm_75, sm_80+, Tensor Core and AMD switches: wrong architecture.
- `STRATA_CPU_IQ_ALL_EXACT1`: requires AVX2 without AVX-512; check actual CPU dispatch before testing. Rocket Lake may expose AVX-512. Not blindly queued.
- PLE RAM: huge table plus ~47 GiB expert arena exhausts 64 GiB; mmap is bounded/reclaimable and more plausible.
- mmap/resident expert modes: full expert arena already fits; avoid SSD faults and introducing unnecessary memory modes.
- `--kv-grow`: requires nonstreamed KV; would need a paired policy change, not a clean single-parameter experiment. Existing streaming already cuts KV allocations.
- aux-cpus: implementation documented Linux only. Hybrid pool affinity, NUMA, multi-GPU, pipeline, peers and concurrency: not this six-core single-GPU sequential workload.
- Large pages: baseline privilege refused; granting requires elevated system policy plus logoff, deferred (no unsolicited privilege/policy edits).
- Cache sizes/profile trained on benchmark: no prompt-cache gaming or corpus-specific overfit. Keep default caches; agents may benefit from them.
- Ring overrides, explicit expert counts, PCIe kernel modes, forced unfused/debug paths: default planners already account for available VRAM; revisit only if profiling points there, not blind brute force.
- Overclock/driver/system fallback-policy changes: outside model parameters, not changed.

## Second stage / selection policy
After first-stage results, mark gains **provisional** (five sampled code runs and temporal drift). Prefer >3% decode with no >10% prefill regression, or >5% prefill with decode within 3%. Re-run quality reference periodically. Select at most one value per family. Test combined winners from the quality reference, then remove conflicting members if needed; final candidate must beat a fresh reference and pass coding/tool/recall sanity checks. Do not call statistical significance from these quick unpaired runs. Keep original baseline comparison separate from quality-reference comparison.

## Baseline outcome / execution notes
- Baseline completed 2026-10-28 23:03: **36.08 code decode tokens/s**, **381.83 prefill tokens/s**, medians of 5 and 8 successful measured samples respectively.
- The requested prefill target 16384 produces about **12K actual model tokens** with BetterBench's synthetic filler and this tokenizer. Keep the exact requested config; do not mislabel this as an exact 16384-token model input. Actual per-request counts remain in the JSON.
- BetterBench saved all measurements, then exited 1 while printing a Unicode character to redirected Windows cp1252 stdout. Re-rendered the saved JSON with `PYTHONIOENCODING=utf-8` to recover HTML; **did not rerun or discard measurements**. All subsequent runs explicitly use UTF-8 stdout. Original traceback is retained in `baseline.bench.log`.
- Sequential supervisor restarted as PID 14780 after that reporting-only issue; baseline server was stopped by verified owned PID, and the quality-reference server started successfully. Historical PIDs are recorded in `state/queue-state.json` (do not rely on these historical PID numbers).
- `python -m py_compile scripts/*.py` and a synthetic result-parser self-test passed. Queue pauses on failed or incomplete measured runs.

## Resume
- `RESULTS.md` is the live results table; raw artifacts under `results/`.
- `state/baseline.status.json` is the preserved baseline supervisor checkpoint.
- Queue/control scripts and durable experiment list will live under `scripts/` and `experiments.json`.
- Do not start a second benchmark while the first is running. Never kill unrelated processes; stop only PIDs created and recorded here.
