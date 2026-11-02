# PCIe x8/x8 GPU experiments

Engine/control 0.1.55; GPU 0 P100 16GB TCC, GPU 1 GTX 1080 Ti 11GB WDDM. Both measured PCIe 3 x8. Earlier [x16/x4 results](../2026-11-01-p100-1080ti-x16-x4/RESULTS.md) are historical, not references.

Same IQ3_S model, 131072 context, int8 KV, 32768 KV residency, full routing; requested BetterBench quick code decode and 16K-target prefill, no concurrency. Five decode/eight prefill samples per run; medians tok/s. Thermal throttling can confound comparisons.

| Run | Placement | State | Decode | Prefill |
|---|---|---|---:|---:|
| x8-p100-only | P100 only | complete | 31.95 | 295.52 |
| x8-1080-only | 1080 Ti only | complete | 20.70 | 201.49 |
| x8-dual-p100 | Auto split; P100 Main | complete | 36.18 | 304.59 |
| x8-dual-1080 | Auto split; 1080 Ti Main | complete | 34.80 | 300.45 |
| x8-pipeline-p100 | P100 Main; pipeline windows 2 | complete | 37.92 | 287.20 |
| x8-pipeline-1080 | 1080 Ti Main; pipeline windows 2 | failed | — | — |
| x8-trim-32 | P100 layers 0-31; 1080 Ti 32-47; trim | complete | 38.72 | 321.33 |
| x8-trim-24 | Equal layers; 1080 Ti Main; trim | complete | 36.77 | 316.90 |
| x8-safe-p100 | P100 Main; later reserve 1600 MiB | complete | 34.17 | 286.71 |
| x8-stage0-p100 | P100 Main; pipeline 2; draft on first; reserve 1600 | complete | 35.94 | 274.73 |
| x8-stage0-1080 | 1080 Main; pipeline 2; draft on first; reserve 1600 | complete | 30.42 | 287.00 |
| x8-peer-p100 | P100 primary; 1080 expert peer; peer reserve 1600 | failed | — | — |
| x8-prefill-pipe | P100 Main; balanced prompt chunks; reserve 1600 | complete | 34.93 | 303.60 |
| x8-trim-32-safe | P100 32 / 1080 16; trim; later reserve 1600 | complete | 40.56 | 316.56 |
| x8-trim-p100-safe | 1080 16 / P100 32; trim; later reserve 1600 | complete | 37.40 | 286.10 |
| x8-final-1 | Selected safe trim32; confirmation + recall | complete | 40.62 | 317.70 |
| x8-p100-reference | P100 only; nearby reference + recall | complete | 32.36 | 264.12 |
| x8-final-2 | Selected safe trim32; second confirmation | complete | 37.30 | 319.54 |

Checkpoint: gpu-tuning-complete; current None; 2026-11-02 11:10:22

## Rationale

Test single cards and both Main orders first. Pipeline windows overlaps speculative work without dropping target experts. Two explicit splits plus dense-weight trimming test compute balance versus expert-cache capacity. Follow-ups test safer VRAM reserve, explicit stage-0 draft placement (not default on installed CUDA), an expert peer instead of layer splitting, and balanced prompt chunks. No model/precision/context reduction. Current online docs describe newer versions: installed --help and startup logs determine actual support. See [NOTES.md](NOTES.md) for reviewed failures and recovery decisions.

Research: [layer split](https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md), [expert helper alternative](https://github.com/Niko1221/Strata/blob/main/docs/SECOND_GPU.md). Layer splits transfer stage activations via pinned host RAM and do not require NVLink/P2P. Helper caches add per-layer round trips and are not the first choice for two capable GPUs.

Raw artifacts: results/x8-*. Private configs contain credentials; do not publish. Detailed telemetry in results/gpu-x8-telemetry.csv includes GPU IDs, clocks, thermal throttle flags, link widths. From repository root: `python campaigns/2026-11-02-p100-1080ti-x8-x8/scripts/run.py`; pause: create this campaign's `state/STOP-GPU-X8`. Original tuning queue/install profiles untouched.
