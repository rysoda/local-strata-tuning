# Reserve-floor experiment plan

## Motivation and bounds

The P100 is a dedicated TCC compute card, not a display card. No browser/game/other graphics workload is expected on the 1080 Ti beyond the Windows desktop. The earlier 1400/2304 policy was conservative; its free-memory threshold was not a measured minimum. Find the smallest usable explicit reserve flags without changing model quality, context, split, cooling, clocks or software. No guarantee of future allocation success from a single free-memory sample.

Scope is the selected 36/12 trimmed placement at **262144 context**. Original first-run 32/16 performance is not directly compared as a reserve-only change. IQ3_S target weights, full experts, int8 KV/resident32768, CPU/PCIe policy and MTP/reasoning retained. No precision reductions, expert pruning, reasoning/context reduction or speed projections as scientific optimizations. Existing user-requested projected deployment is checked separately only after a projection-free floor is validated. Startup is not changed by the runner.

## Research and installed compatibility

- [Issue 493](https://github.com/Niko1221/Strata/issues/493): maintainer documents reserve N as cache room withheld, default700. Motivation only; current installed startup behavior wins.
- [Issue 3140](https://github.com/Niko1221/Strata/issues/3140): graph capture allocations happen after the startup free-memory printout; a low free-memory warning alone did not prove a slowdown on that tester's hardware. Therefore no blanket 1 GiB threshold here, but exercise multiple graph sizes and long requests.
- [Issue 3215](https://github.com/Niko1221/Strata/issues/3215): newer launchers once overwrote requested reserve including zero. Not assumed present on 0.1.57; avoid normal app rewrites via isolated configs, presets disabled, explicit flags and effective-log verification.
- Installed engine BUILD.json: version0.1.57, commit **0bdcef4682c5**, CUDA12.9, sm60/61 included. Downloaded generate.cpp at that commit read-only; full copy ignored/private, hash/URL in results/source-provenance.json. Public line-numbered excerpts and stage-reserve header retained. This is stronger reference than the old pinned 0.1.52 submodule, but still verify actual binary startup.
- Reference parser uses atoi and marks explicit `--vram-reserve-mib` as given; later flag accepts zero via >=0. CUDA is excluded from the Windows-HIP automatic large-reserve floor. Reference sizing separately prices late allocations, later-stage windows and MTP/head, so zero user reserve is not zero total internal budgeting. Never disable those safeguards to force lower numbers.
- Installed Control vram_fit.fit_start returns unchanged on explicit layer splits. The earlier active live server was projection-enabled normal terminal launch; preserve its original profile privately, stop only its verified tree before benchmarking. Do not overwrite its preset or Startup file.

## Sequential adaptive experiment

1. Fresh 1400/2304 control: exact BetterBench plus all seven functional/tool/recall checks. If control fails, pause rather than search.
2. P100 reserve 700,512,256,128,64,0; display fixed2304. Stop descending at first rejected boundary and bisect the failed/passing interval down to integer MiB. Keep every result and the explicit local-monotonicity assumption.
3. Display reserve same descending levels; P100 fixed1400. Refine similarly. These are independent **benchmark-screen floors**, not yet deployment-safe minima.
4. Extended-validate P100 floor at display2304. If a real allocation/stall boundary appears, refine upward against the extended-passing control; pure answer/tool/quality failures pause for review, not classified as memory failures.
5. Extended-validate display floor with the resulting P100 floor. Refine allocation boundary upward against the validated display2304 pair if needed. This detects interactions that independent screens miss.
6. Minimum / original-reserve control / minimum nearby confirmations, each with the exact workload and seven smoke checks. Reproduction failure pauses; do not silently move the target or declare completion.
7. Separate projection-enabled compatibility arm using the *existing* scale1/layers4–44/project/per-layer settings, exact workload and seven checks. It is not part of same-quality speed comparison. If it cannot allocate, label it incompatible rather than deploying the scientific floor with projection.
8. Report observed smallest validated pair, failed neighbors, effective cache/reserve values, per-card free-memory minima, all samples/errors, startup time versus inference time and speed tradeoffs. Create separate private/redacted profile, leave Startup unchanged, stop owned test processes and mark completion durably.

No factorial reserve sweep. At most logarithmic refinement around observed boundaries; completed pairs are reused as evidence, never rerun under the same run ID. Final independent repeats have new IDs. Do not call the result the absolute mathematical minimum across all workload/desktop states; integer boundary estimates can move with allocator/OS variance.

## Workload, acceptance and recovery

Every performance arm uses BetterBench exactly:

```text
--quick --decode --categories code --prefill --no-concurrency --config <repo>/workloads/betterbench-16k.json
```

Retain original JSON/HTML, all five code/eight prefill samples and actual token usage. The 16384 corpus target is not exactly that many model tokens. Quick mode is not significance. Never execute generated code.

Standard six functional/tool/32K/~119K checks plus above-128K recall use deterministic prompts and actual installed tokenizer/API usage (~230K prompt tokens). These are allocation/functional smoke evidence, not intelligence equivalence or comprehensive validation of every 256K use. Candidate/control/repeat must pass all seven before recommending.

Positive acceptance: loaded fixed model/context, effective resident window32768, actual 36/12 layers, MTP retained, no automatic restart/drafter fallback or projection contamination, all exact benchmark samples, valid telemetry, no non-finite/watchdog restart, no thermal anomaly. Observed free-memory amount alone is not a rejection. Over25% throughput loss against the fresh control in either metric is a usability rejection; record the threshold and uncertainty rather than calling it proven paging.

Predeclared negative experiment outcomes: explicit CUDA/allocator/no-room error; or no engine/benchmark progress for360s during benchmark (1800s during long smoke). Stop only a verified owned benchmark/smoke process tree, let owned server cleanup finish, preserve raw failed phase and logs, and record reviewed_skip plus boundary classification before considering a larger reserve. These are intentionally sought allocation/latency boundaries, not silently ignored errors. Numerical/restart errors, unexpected exits, missing artifacts, pure functional failures, changed software/topology, >85°C or sampled thermal slowdown flags pause for explicit review. No unreviewed recovery or retry.

No fan, voltage, clock, power-limit, page-file or other application changes to make a reserve pass. Frozen inputs checked before every run; normal network-facing server remains stopped during isolated testing. Root/cache/model versions stay fixed. Original campaign state is never cleared.
