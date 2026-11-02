# GTX 1080 Ti single-card tuning

[Campaign index](../../README.md) · [Manifest](manifest.json) · **[Final report](FINAL_REPORT.md)**

**Complete, 2026-10-29:** 54 complete BetterBench runs and one rejected startup. GTX 1080 Ti 11 GB/WDDM, i5-11400F, 64 GB RAM; engine 0.1.52 CUDA12, Control 0.1.51, BetterBench 0.6.1. IQ3_S, 131072 context, int8 KV / 32768 residency.

Final confirmation: about **31.26 decode / 427.45 prefill tok/s**, versus full-expert reference **30.30 / 424.61**. This is **not** a gain over the faster approximate original baseline. Read the report's quality/reference caveats. Candidate and reference each passed 6/6 functional/recall smoke checks.

## Navigate

- [Plan and research rationale](TUNING_PLAN.md)
- [All single-parameter/follow-up results](RESULTS.md)
- [Combined results](COMBINED_RESULTS.md) and [stage-one interpretation](STAGE1_REVIEW.md)
- [Redacted recommendation](configs/shareable/recommended.json); private equivalent under ignored `configs/private/`
- [Raw evidence](results/), [research captures](research/), [queue checkpoint](state/queue-state.json)
- [Historical agent instructions/checkpoints](AGENT_HISTORY.md): preserved history, not current paths

## Launch / reproduce

Root-relative launcher: [launchers/Run-1080Ti.cmd](../../launchers/Run-1080Ti.cmd).

**Historical installation limitation:** Control **0.1.51 is no longer installed locally** (the 0.1.52 engine remains). The launcher checks the exact configured installation and fails clearly instead of silently changing software. Restore/adapt deliberately for reproduction; a newer Control is not the same validated setup.

## Resume safety

From repository root:

```sh
python campaigns/2026-10-28-1080ti-tuning/scripts/tune.py
python campaigns/2026-10-28-1080ti-tuning/scripts/run_combined.py
```

Both currently report completion and start nothing. State lives under `state/`; pause flag is `state/STOP`. Baseline supervisor metadata is `state/baseline.status.json` and `state/baseline.process.json`. Do not clear completed state; new hardware/software comparisons need a new campaign.

## Relocation notes

The original root reports/configs/results now live here. Published configs moved to `configs/shareable/`, private profiles to `configs/private/`, and queue metadata to `state/`. The shared workload is [workloads/betterbench-16k.json](../../workloads/betterbench-16k.json); sanity checks live in [tools/sanity.py](../../tools/sanity.py). Upstream source remains [research/strata-source](../../research/strata-source).

Original raw evidence and checkpoint contents are unchanged, including historical paths/PIDs. Quoted original commands and historical agent notes may refer to the old layout. Use this README for current launch/resume instructions.
