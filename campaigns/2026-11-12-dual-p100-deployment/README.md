# Dual P100 deployment and three quick benchmarks

[Campaign index](../../README.md) · [Report](REPORT.md) · [Manifest](manifest.json) · [Work log](NOTES.md) · [Plan](PLAN.md)

**Complete: 3/3 requested diagnostic benchmarks**, 2026-11-13. Existing installed server retained unchanged during measurement and left running afterward.

Two Tesla P100 16GB GPUs; engine 0.1.59 / Control 0.1.57. IQ3_S, 262144 context, int8 KV, resident32768, MTP, full experts, 36/12 split, reserves 640/896 MiB. Existing experimental projection retained, not validated by these speed checks. No tuning performed.

| Run | Decode tok/s | Prefill tok/s |
|---|---:|---:|
| 1 | 31.827 | 345.244 |
| 2 | 33.091 | 344.676 |
| 3 | 31.085 | 343.908 |
| **Mean of per-run medians** | **32.001** | **344.609** |

Exact BetterBench quick code decode + 16K-target prefill, no concurrency. All 15 decode and 24 prefill measured samples valid. Actual prefill lengths 11970–12190 model tokens. Quick screening is not statistical significance or quality equivalence. See report for historical comparison caveats.

## Evidence and restart safety

- `results/`: raw samples/errors, before/after metrics, commands and GPU telemetry.
- `configs/private/installed.json`: ignored credential-bearing snapshot; never publish directly.
- `state/queue-state.json`: complete; `scripts/quick.py` refuses to repeat completed work.
- `state/STOP`: pause between runs only. Failed/incomplete attempts require review; never clear state to retry.
- `NOTES.md`: startup stale-PID recovery and measurement checkpoint. The benchmark runner never stops or modifies the user server.
