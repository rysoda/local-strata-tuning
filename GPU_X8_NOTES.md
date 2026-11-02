# x8/x8 follow-up work log

## 2026-11-02 restart, 08:12 local

- User confirms both GPUs now use CPU PCIe lanes at x8/x8. `nvidia-smi` independently reports width 8 on each. P100 = GPU 0, GTX 1080 Ti = GPU 1. Keep installed engine/control 0.1.55 for all comparisons, not historical 0.1.52 results.
- Found previous x8 queue interrupted during dual/P100-main prefill. No surviving server/benchmark/runner; port 8080 free. No final BetterBench result JSON for interrupted arm. Preserved its logs and old state in `results/interrupted-x8-dual-p100-20261102/`, removed only that incomplete state entry. Completed single-card results preserved.
- Restarted `python -u scripts/gpu_x8.py` detached, PID 4440. Queue uses exclusive Windows file lock, independent from completed original tuning queue. Output `results/gpu-x8-runner.log`; state `results/gpu-x8-state.json`; live table `GPU_X8_RESULTS.md`. Do not launch a second benchmark alongside it.
- Re-read upstream MULTI_GPU.md and SECOND_GPU.md. Installed help confirms pipeline windows, trim, prefill-pipe, peer-device and remote cache options. Upstream main may be newer: require startup evidence before claiming any setting took effect.

## Screening plan (already in scripts/gpu_x8.py)

1. Single P100 and single 1080 Ti on new topology (already complete).
2. Auto split in both Main orders. Last GPU is Main; `gpu_order=as_given` prevents reorder.
3. Both orders with `--pipeline-windows 2`: overlaps speculative verification, retains full target computation.
4. Explicit 32/16 and 24/24 layer placement, P100 first and 1080 Ti Main, `--trim-stage-weights`: avoid duplicate dense weights, increase expert residency. Retains full layers/experts.
5. Review logs, metrics and temperature/clocks. Confirm best placement against P100-only in nearby runs, plus correctness/128K recall smoke checks. If evidence favors changing Main or splitting differently, add only reasoned follow-up arms.
6. Consider prefill-pipe/chunk balancing if dual prefill stalls; peer tier is a separate plausible alternative (P100 primary, 1080 Ti peer) if installed server supports it. Do not brute-force unrelated settings.

Every run uses requested BetterBench `--quick --decode --categories code --prefill --no-concurrency --config 16k.json`. Keep IQ3_S, 131072 context, int8 KV/32768 residency, full expert routing. No pruning/precision reduction. Single-run medians are screening only, not significance claims.

## 08:32 interim findings

- Fresh dual auto runs: P100 Main 36.18 decode / 304.59 prefill; 1080 Ti Main 34.80 / 300.45 tok/s. Both beat earlier single-card screening, but individual code samples vary substantially; confirm later.
- Auto chose 16 layers on 1080 Ti + 32 on P100 (P100 Main), or 35 P100 + 13 1080 Ti (1080 Main).
- Installed 0.1.55 **does not move MTP to stage 0 automatically on CUDA**: pipeline startup explicitly warns to try `STRATA_MTP_STAGE0=1`. Current pipeline arms retain the default placement and are valid controls, not a test of the newer docs' stage-0 behavior. Add a stage-0 arm after reviewing screens.
- Startup free-memory warnings: P100 Main ~400 MiB free, 1080 Main reports 0 MiB free; suggested later-stage reserves ~1068 and ~1468 MiB, respectively. Test 1600 MiB later-stage reserve before recommending a display-card-Main configuration. Do not reduce context as workaround.

## 09:01 reviewed failure and expanded queue

- P100 Main with default-draft pipeline: **37.92 / 287.20** tok/s, valid 5/8 samples, no non-finite/watchdog errors found in server log. Promising decode, lower prefill; not yet correctness-confirmed.
- 1080 Main with default-draft pipeline **rejected**: repeated 300s silences, engine watchdog restarts, non-finite logits. Stopped only the command-line-verified benchmark process tree (PID 11380); supervisor cleaned up its own server and recorded failed. No speed claimed. Set `reviewed_skip=true` with reason in state; runner now skips explicitly reviewed failures, still refuses all unreviewed incomplete runs.
- Added 5 reasoned follow-up arms to `scripts/gpu_x8.py`: P100 Main with later reserve 1600; pipeline with stage-0 MTP + reserve 1600 in each Main order; P100-primary expert peer with 1080 reserve 1600; P100 Main `--prefill-pipe 1` + reserve 1600. Installed server source confirms `--peer-device` suppresses automatic layer split; no direct engine bypass needed.
- Resumed runner PID 9688 after port 8080 was free. It continues explicit trim arms first, then follow-ups; completed arms are not rerun. Still need final selection, nearby repeats and correctness checks after screening.

## 09:23 trim screening and next restart

- Trim 32/16 (P100 first, 1080 Main) leads initial screening: **38.72 decode / 321.33 prefill**. Equal 24/24 trim: **36.77 / 316.90**. No watchdog/non-finite server errors found in either. Startup trim32 leaves only ~46 MiB on display card; not ready to recommend without more headroom.
- Added `x8-trim-32-safe` (same placement with 1600 MiB later reserve) and `x8-trim-p100-safe` (reverse order, 16/32 with P100 Main and same reserve) to source RUNS. **Already running PID 9688 loaded the earlier 13-arm list; it will not see these last two additions. After it exits, run `python scripts/gpu_x8.py` once more to pick up only the new arms.** Do not launch concurrently.
- After all screens: select stable performance/VRAM tradeoff; add fresh P100-only reference and repeated winner with `sanity=True` for functional/32K/119K recall checks. Avoid claiming improvement solely from old midnight singles.

## 09:53 follow-up screening

- Later reserve 1600/P100 Main: 34.17 / 286.71. Stage-0 MTP pipeline + reserve: P100 Main 35.94 / 274.73; 1080 Main 30.42 / 287.00. No benefit over trimmed-layer screening. Stage-0+reserve 1080 run did complete (unlike default-draft/low-reserve pipeline).
- Expert peer startup failed before benchmarking: `peer experts: stream: out of memory`. Recorded failed + reviewed skip, no speed result; do not change precision/context to force it to fit.
- Restarted PID 11384 after failure; this restart reads full 15-arm list including safe trim arms. Remaining: prefill-pipe, safe trim32 and reversed safe trim16/P100 Main. After completion still need nearby references and correctness confirmation.

## 10:22 screening complete, confirmation plan

- All 15 screened configurations reviewed: 13 valid complete benchmarks, 2 rejected failures (default pipeline/1080 Main instability, peer startup OOM).
- Safe trim32 (P100 0-31, 1080 Ti 32-47/Main, later reserve 1600) is best: **40.56 / 316.56**. Startup free VRAM ~779 MiB P100 / 890 MiB 1080; no LOW warning or server watchdog/non-finite errors. Reverse safe trim split: 37.40 / 286.10. Balanced prefill chunks: 34.93 / 303.60; not selected.
- Telemetry: trim runs peaked ~79-80 C on P100 and ~61 C on 1080; sampled hardware/software thermal slowdown flags never active. Clocks/load still vary; no formal significance claim.
- Added 3 final arms in source and restarted queue: `x8-final-1` selected safe trim32 + 6 functional/recall checks; `x8-p100-reference` fresh single P100 + same checks; `x8-final-2` selected safe trim32 repeat. Each benchmark precedes correctness checks; sanity is not included in speed metric. This brackets the new single-card reference with winner confirmations.
- After confirmation: verify both 6/6 checks and 119K prompt usage, inspect errors, write final report and separate ready local profile/launcher. Do not overwrite original single-1080 recommendation or original app profile.

## 11:10 FINAL CHECKPOINT — complete

- **16 complete benchmarks, 2 rejected configurations**, archived interrupted attempt preserved. State phase `gpu-tuning-complete`; runner refuses to restart completed work unless deliberately extended. Final table regenerated with all 18 arms.
- Selected safe trim32: final candidate 1 **40.62 / 317.70**, intervening P100-only reference **32.36 / 264.12**, final candidate 2 **37.30 / 319.54**. Candidate 1 and reference each **6/6** correctness/recall, longest actual prompt **119151 tokens**. Decoder varies; no formal significance claim. Prefill comparison depends strongly on reference (older P100 screening was 295.52).
- Final report **GPU_X8_REPORT.md**; separate private ready profile **configs/recommended-x8.json** and launcher **Run-Tuned-X8.cmd**. Original profile/recommendation unchanged. `python scripts/run_gpu_tuned.py --check` passed; Python compile checks passed. All completed server logs checked for non-finite/watchdog/unexpected stops; none found.
- Port 8080 verified free, no benchmark server intentionally left running. Final candidate P100 peak 80 C and 1080 62-63 C, sampled thermal slowdown flags inactive. Maintain P100 forced airflow.
- No further work queued. To extend, inspect final report/state and add new unique IDs deliberately; do not restart original/historical queues.

## Restart / pause

- Check processes and state before any start. `python scripts/gpu_x8.py` skips completed arms, refuses incomplete/failed ones and occupied port 8080. Lock prevents duplicate runners.
- Create `STOP-GPU-X8` to pause **between** experiments; remove to resume.
- If interrupted, inspect recorded PIDs/command lines and port. Preserve incomplete artifacts/state before explicitly removing the incomplete run entry and rerunning. Never silently turn a partial run into a completed one.
- `GPU_X8_RESULTS.md` is regenerated by queue; keep manual interpretation in this file or a final separate report.
- Old queues `scripts/tune.py` and `scripts/gpu_compare.py` are not the new experiment queue. Original install and recommended profile are untouched. Configs contain credentials; do not print/publish them.
