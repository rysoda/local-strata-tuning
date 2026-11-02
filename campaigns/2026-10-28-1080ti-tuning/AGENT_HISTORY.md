# Historical agent instructions and checkpoints

> Archived during the 2026-11-02 campaign migration. Commands, root paths, PIDs and checkpoints below are historical. Follow repository `AGENTS.md` and each campaign's README for current paths/status. This file spans original single-card and later GPU work; final GPU conclusions now live in `../2026-11-02-p100-1080ti-x8-x8/REPORT.md`.

# Project description

The scope of this project is to tune the local install of [strata](https://github.com/Niko1221/Strata/releases) with the purpuse of getting the most performance possible for this hardware.

Use the already present local install, model qwen3.8-flash-next-iq3_s with 128k context.


# Data gathering

To test performance you will use [betterbench](https://github.com/GGZ14/BetterBench).

In order to avoid waiting hours for tests to complete, you will use the following parameters

  --quick --decode --categories code \
  --prefill --no-concurrency \
  --config 16k.json

Where 16k.json is
  {
  "prefill_depths": [16384]
  }

Run a base test first to gather data for the not-tuned performances.

I'm looking for decode and prefill speed.


# Job description
Your job is to try every parameter following this two rules rules:

* the parameter must not make the model dumeber
* the parameter itself must make some sense in this scenario, don't just try every single one

# How to proceed

Search the internet, the project repo, forums and all the places people go to share benchmark
data for all the avaiable parameters. Then research each of them to see which one is worth trying in the pursue of performance.
I don't want to brute-force every parameter avaiable: I want to invest time in something that makes sense.

Compile a list of parameters that you're going to try, write it down in a markdown file.

## First stage - Single parameter run

Try each one and save the result in a table inside a table in a markdown file,
so if you were to be stopped for whatever reason you'll know where you left off.

Mark for usage those that have a positive impact.

I'm interested more in agentic work so decode speed is a bit more important than prefill.

## Second stage - Combined parameter test

Now it's time to combine the parameters that do actually improbe performance together.

Gather data like before and offer the best mix of parameters to the user.

# Starting and stopping

This will be a long task. Make sure to write down where you're at so if you were to get stopped you could continue easily.

You can edit this file with any comments you think you'll need in future runs below.

## P100 + 1080 Ti x8/x8 checkpoint (2026-11-02)

- **Completed new-topology work**: 16 complete BetterBench runs, 2 reviewed/rejected configurations, one archived interrupted attempt. Engine/control **0.1.55 CUDA12** throughout new comparisons; both CPU PCIe 3 x8. All test servers/benchmarks stopped.
- Start with **`GPU_X8_REPORT.md`**. Live table `GPU_X8_RESULTS.md`, detailed recovery/work log `GPU_X8_NOTES.md`, durable state `results/gpu-x8-state.json` phase **`gpu-tuning-complete`**. `python scripts/gpu_x8.py` now reports completion and starts nothing; do not restart old queues.
- Recommended new hardware configuration: GPU 0 **P100 layers 0-31**, GPU 1 **1080 Ti layers 32-47 / Main**; `gpu=[0,1]`, `gpu_order=as_given`, `layer_split=32`, **`--trim-stage-weights --vram-reserve-later-mib 1600`**. Keep full routing, IQ3_S, 131072 context, int8 KV/32768 residency and prior speed settings. Pipeline/peer not selected.
- New ready private profile **`configs/recommended-x8.json`**, launcher **`Run-Tuned-X8.cmd`**, script `scripts/run_gpu_tuned.py` (`--check` supported). Contains existing credentials: do not publish. Original installed profile and original single-1080 recommendation/launcher unchanged.
- Final bracket: candidate **40.62 / 317.70**, P100 reference **32.36 / 264.12**, candidate **37.30 / 319.54** decode/prefill tok/s. Decode gains **+15.3 to +25.5%** versus fresh reference, no significance claim. Earlier P100 screen prefill was 295.52, so claimed prefill gains depend materially on reference; see report caveats.
- Candidate and P100 reference each **6/6** functional/recall checks including **119151 actual prompt tokens**. Smoke checks, not comprehensive quality proof.
- Reject default-draft pipeline with 1080 Main: hangs/non-finite logits/watchdog resets. Expert peer failed startup OOM. Both explicitly reviewed/skipped in state, not valid speed results.
- Final P100 peak **80 C**, 1080 **62-63 C**; sampled thermal flags inactive, but ensure adequate P100 airflow. No power/clock tuning performed.

## Final checkpoint (2026-10-29)

- Task completed: **54 complete BetterBench runs**, one documented incompatible startup; all benchmark processes stopped. Installed profile verified unchanged.
- Start with `FINAL_REPORT.md` for conclusions. Final nearby-reference confirmation: tuned **31.25 / 428.51** and **31.27 / 426.38** decode/prefill tok/s, intervening quality reference **30.30 / 424.61**; roughly **+3.2% decode**, essentially unchanged prefill. No formal significance claim.
- Recommended speed changes: `--pool-tasks 36 --adapt-every 1`, `STRATA_PCIE_BALANCE=1`. Keep original host placement, draft settings, int8 KV, 32768 KV residency and 131072 context. Disable approximate routing with `STRATA_ROUTE_PRIOR=0` and `STRATA_ROUTE_TAIL_SKIP=0`.
- Ready local profile: `configs/recommended.json`; launcher: `Run-Tuned.cmd`. Contains existing API credentials: do not publish config copies.
- **Important quality caveat:** original baseline **36.08 / 381.83** used default expert-tail skipping. Restoring all target experts slows decoding; the final gain is against the same-quality/full-expert reference, NOT against that approximate original baseline.
- Final candidate and quality reference each passed 6/6 functional/recall checks, including 119151 actual prompt tokens. These are smoke checks, not comprehensive quality proof.
- Full tables: `RESULTS.md`, `COMBINED_RESULTS.md`; interpretation `STAGE1_REVIEW.md`; raw artifacts `results/`; final state `results/queue-state.json` (`tuning-complete`). Do not restart the completed queues unless intentionally extending experiments.
- Important artifact: `auto:5376` was an attempted prompt cap but is a no-op in engine 0.1.52 (maps to ordinary auto). Final recommendation uses plain `auto`. Early prefill gains were confounded by auto cache/chunk allocation changes.

## Historical agent checkpoint (2026-10-28)

- Research and candidate rationale: `TUNING_PLAN.md`; live results: `RESULTS.md`; durable queue: `experiments.json` and `results/queue-state.json`.
- An isolated baseline and sequential single-parameter supervisor were started. **Check recorded processes/status before starting anything else.** Baseline status is `results/baseline.status.json`; queue log is `results/queue.log`.
- Resume command: `python scripts/tune.py` (single-runner lock; refuses ambiguous interrupted active experiments). Creating a file named `STOP` pauses between experiments; remove it to resume. Failed/invalid experiments pause the queue for inspection, not automatic retries.
- Original installation is untouched. Copies in `configs/` contain local API credentials; do not publish them.
- Critical quality finding: installed profile already has `STRATA_ROUTE_PRIOR=0`, but the engine defaults `STRATA_ROUTE_TAIL_SKIP=7` ON (omits some experts). Preserve this only in the untouched baseline; use `STRATA_ROUTE_TAIL_SKIP=0` as the quality reference for all tuning. No lower KV precision, context reduction, target quant changes, pruning or speed projections.
- Existing engine 0.1.52 (CUDA12, build commit a42cc3d7df70d1940de82cd0882f03e1f5dfc741), Control 0.1.51, GTX 1080 Ti / i5-11400F / 64 GB. Source in `research/strata-source` is pinned for reference only. Do not upgrade the install mid-comparison.
- Every run uses the exact requested BetterBench workload. It is quick screening, not a significance claim. Combined stage intentionally requires review of single-parameter results and correctness before recommendation.