# VRAM reserve performance tuning

**Status: complete**

Fixed engine/Control 0.1.57, IQ3_S, 262144 context, full experts, int8 KV/resident32768, MTP, trimmed 36/12 split. No speed projection. Startup and installed profiles unchanged.

[All attempts](RESULTS.md) · [Plan and selection rule](PLAN.md) · [Work log](NOTES.md)

## p100 ranking

| P100/Ti MiB | Mean decode | Mean prefill | Score | Runs |
|---|---:|---:|---:|---|
| 768/2304 | 39.20 | 325.47 | 1.0281 | p100-768-r1, p100-768-r2 |
| 512/2304 | 39.43 | 325.07 | 1.0312 | p100-512-r1, p100-512-r2 |
| 256/2304 | 38.86 | 325.50 | 1.0227 | p100-256-r1, p100-256-r2 |
| 896/2304 | 38.69 | 325.86 | 1.0206 | p100-896-r1, p100-896-r2 |
| 384/2304 | 38.21 | 326.02 | 1.0131 | p100-384-r1, p100-384-r2 |
| 640/2304 | 38.12 | 325.95 | 1.0117 | p100-640-r1, p100-640-r2 |
| 1024/2304 | 37.74 | 325.95 | 1.0055 | p100-1024-r1, p100-1024-r2 |
| 1400/2304 | 37.45 | 325.29 | 1.0000 | control-original-reserves, reference-after-p100 |

## ti ranking

| P100/Ti MiB | Mean decode | Mean prefill | Score | Runs |
|---|---:|---:|---:|---|
| 1400/896 | 39.63 | 328.33 | 1.0340 | ti-896-r1, ti-896-r2 |
| 1400/256 | 38.87 | 330.29 | 1.0245 | ti-256-r1, ti-256-r2 |
| 1400/384 | 38.62 | 330.60 | 1.0209 | ti-384-r1, ti-384-r2 |
| 1400/1024 | 38.64 | 328.61 | 1.0188 | ti-1024-r1, ti-1024-r2 |
| 1400/512 | 38.47 | 330.42 | 1.0183 | ti-512-r1, ti-512-r2 |
| 1400/768 | 38.43 | 328.89 | 1.0158 | ti-768-r1, ti-768-r2 |
| 1400/640 | 38.18 | 328.79 | 1.0117 | ti-640-r1, ti-640-r2 |
| 1400/2304 | 37.67 | 325.93 | 1.0000 | control-original-reserves, reference-after-p100, reference-after-ti |

## joint ranking

| P100/Ti MiB | Mean decode | Mean prefill | Score | Runs |
|---|---:|---:|---:|---|
| 640/896 | 40.75 | 329.86 | 1.0534 | joint-p640-t896, joint-repeat-p640-t896 |
| 768/1024 | 40.05 | 330.25 | 1.0429 | joint-p768-t1024 |
| 512/512 | 39.49 | 332.50 | 1.0369 | joint-p512-t512 |
| 512/256 | 39.73 | 326.53 | 1.0333 | joint-p512-t256, joint-repeat-p512-t256 |
| 768/768 | 37.81 | 333.51 | 1.0115 | joint-p768-t768 |
| 768/896 | 38.04 | 328.41 | 1.0090 | joint-p768-t896 |
| 896/896 | 37.56 | 329.07 | 1.0021 | joint-p896-t896 |
| 1400/2304 | 37.67 | 325.93 | 1.0000 | control-original-reserves, reference-after-p100, reference-after-ti |

## Selected confirmation pair: 640/896 MiB

| Run | Decode | Prefill | Smoke |
|---|---:|---:|---|
| confirm-candidate-1 | 38.17 | 330.62 | {'passed': 7, 'total': 7} |
| confirm-reference-1 | 37.50 | 325.71 | {'passed': 7, 'total': 7} |
| confirm-candidate-2 | 40.11 | 333.26 | not scheduled |
| confirm-reference-2 | 37.71 | 324.13 | not scheduled |
| confirm-candidate-3 | 38.30 | 330.16 | {'passed': 7, 'total': 7} |
| confirm-reference-3 | 37.25 | 328.09 | not scheduled |

Candidate mean: **38.86 decode / 331.35 prefill tok/s**. Nearby reference: **37.49 / 325.98**. Changes: **+3.65% decode / +1.65% prefill**.

Confirmation accepted: **True**.

**Recommended tested profile:** `configs/shareable/recommended.json` (private credential-bearing counterpart used locally). Validate with `python tools/launch.py 2026-11-08-p100-1080ti-reserve-performance --check`.

Owned test processes stopped. No automatic Startup change.

## Limits

Quick screens and repeated medians are not statistical significance or an exhaustive mathematical optimum. Independent screening uses two starts per value; joint screening is provisional until confirmation. Prefill no-loss gate allows 2% screening noise. The 60/40 decode/prefill score and 0.5% headroom tie rule are declared before testing. Small gains may be noise.

Seven-check smoke sets include functional/tool behavior, ~119K and ~230K actual prompt tokens; they are not comprehensive intelligence equivalence. Generated code is never executed. Explicit reserve is not total unused VRAM. WDDM/display allocations and future workloads can change headroom. Actual token counts, every benchmark sample, cache-slot counts and per-card minimum free memory are retained in raw results/state. No precision, expert routing, context, reasoning, cooling or software changes.
