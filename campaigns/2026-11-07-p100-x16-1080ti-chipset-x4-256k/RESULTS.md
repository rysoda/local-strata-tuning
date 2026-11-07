# 256K topology tuning — live results

Full-quality IQ3_S, int8 KV, full experts; fixed noise-limited two-fan cooling. Quick screens are not significance claims.

| Run | Phase | Decode tok/s | Prefill tok/s |
|---|---|---:|---:|
| r01-quality-reference-layout | complete | 40.40 | 316.33 |
| r02-p100-only | complete | 34.00 | 333.90 |
| r03-1080-only | complete | 23.71 | 250.64 |
| r04-auto-1080-main | complete | 38.58 | 329.85 |
| r05-auto-p100-main | complete | 35.41 | 312.45 |
| r06-trim32-p100-headroom | complete | 37.01 | 321.49 |
| r07-trim32-both-headroom | complete | 37.56 | 313.54 |
| r08-trim28-safe | complete | 32.83 | 299.41 |
| r09-trim36-safe | complete | 38.77 | 325.86 |
| r10-reverse14-explicit | complete | 31.90 | 306.85 |
| r11-reverse14-trim | complete | 37.03 | 306.83 |
| r12-trim32-mmap | complete | 36.93 | 315.05 |
| r13-trim32-prefill-pipe | complete | 36.38 | 324.84 |
| r14-p100-safe-reference | complete | 32.88 | 333.66 |
| f01-candidate | complete | 37.47 | 325.60 |
| f02-p100-reference | complete | 33.27 | 333.98 |
| f03-candidate-repeat | complete | 35.32 | 326.31 |

Initial auto/1080-Main silently enabled dense stage trimming at K=35; it is not an untrimmed control. No model layers/experts were removed. Confirmation includes functional/tool/~119K and separate ~230K actual-token recall smokes.

State: `complete`.
