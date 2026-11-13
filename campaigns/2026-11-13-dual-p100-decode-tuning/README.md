# Dual P100 decode tuning — complete

[Campaign index](../../README.md) · [Full report](REPORT.md) · [Manifest](manifest.json) · [Research/plan](PLAN.md) · [Work log](NOTES.md) · [Every attempt](RESULTS.md)

**Selected: balanced 24/24 split + pipeline windows 2, MTP on the last card.** Two P100 16GB TCC, PCIe 3 x8/x8, installed engine 0.1.59 / Control 0.1.57. IQ3_S, **262144 context**, int8 KV, full experts and reasoning retained. Reserves remain 640/896 MiB; no projection in the recommendation. No software upgrade or weight conversion.

| Nearby confirmations | Decode tok/s | Prefill tok/s |
|---|---:|---:|
| Original 36/12, projection-free reference | 31.70 | 345.89 |
| Candidate A | 44.66 | 347.26 |
| Candidate B | 47.63 | 347.57 |
| **Candidate mean of medians** | **46.15 (+45.6%)** | **347.41 (+0.44%)** |

Ten valid benchmark runs plus two reviewed/excluded override-metadata attempts, all evidence preserved. Exact quick code decode + 16K-target prefill, no concurrency. Reference/candidate each passed **7/7** functional/tool/recall smoke checks, including **230146 actual prompt tokens**. Generated code never executed. Repeated quick screens are not statistical significance or comprehensive intelligence equivalence; prefill is essentially unchanged and decode varied between repeats.

## Run the ready profile

Double-click [Run-Dual-P100-Tuned.cmd](../../launchers/Run-Dual-P100-Tuned.cmd), or validate without launching:

`python tools/launch.py 2026-11-13-dual-p100-decode-tuning --check`

Launcher binds localhost:8080 and refuses an occupied port. It resolves credentials privately and disables presets. Original installed profile and boot launcher remain unchanged; **Startup still uses the old settings**. See NOTES.md for separately running deployment status.

## Restart and privacy

- `results/`: raw samples, actual counts, errors, startup logs, research snapshots and GPU telemetry.
- `configs/private/`: ignored original/isolated profiles, credentials and runtime snapshots; never publish directly. Redacted copies generated in `configs/shareable/`.
- `state/queue-state.json`: complete. `scripts/run.py` exits without running anything when complete; never clear state to retest. New work needs a new campaign or explicitly reviewed distinct comparison.
- `scripts/capture.py`, `review_overrides.py`, `finish.py`: provenance and recorded one-time preparation/recovery/finalization, not instructions to rerun them.
- No benchmark/test processes remain; a separately launched ready profile is a user deployment, not a test queue.
