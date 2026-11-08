# Reserve minimization — live results

Fixed 36/12 split, 256K, IQ3_S, full experts, int8 KV. No arbitrary minimum free-memory criterion. Expected allocation boundaries are preserved, never retried.

| Run | P100 MiB | 1080 MiB | Result | Decode | Prefill |
|---|---:|---:|---|---:|---:|
| control-original-reserves | 1400 | 2304 | passed-extended | 34.22 | 323.18 |
| reserve-p700-t2304 | 700 | 2304 | passed-screen | 38.83 | 324.92 |
| reserve-p512-t2304 | 512 | 2304 | passed-screen | 38.92 | 325.13 |
| reserve-p256-t2304 | 256 | 2304 | passed-screen | 37.85 | 325.17 |
| reserve-p128-t2304 | 128 | 2304 | passed-screen | 40.37 | 315.44 |
| reserve-p64-t2304 | 64 | 2304 | passed-screen | 37.94 | 299.33 |
| reserve-p0-t2304 | 0 | 2304 | passed-screen | 39.25 | 284.50 |
| reserve-p1400-t700 | 1400 | 700 | passed-screen | 38.86 | 332.48 |
| reserve-p1400-t512 | 1400 | 512 | passed-screen | 40.29 | 323.23 |
| reserve-p1400-t256 | 1400 | 256 | passed-screen | 38.12 | 323.78 |
| reserve-p1400-t128 | 1400 | 128 | passed-screen | 36.00 | 311.01 |
| reserve-p1400-t64 | 1400 | 64 | passed-screen | 37.78 | 313.01 |
| reserve-p1400-t0 | 1400 | 0 | passed-screen | 38.37 | 306.90 |
| extended-p0-t2304 | 0 | 2304 | passed-extended | 37.07 | 282.68 |
| extended-p0-t0 | 0 | 0 | passed-extended | 39.03 | 267.95 |
| validated-joint-minimum | 0 | 0 | passed-extended | 39.21 | 251.27 |
| nearby-original-reserves | 1400 | 2304 | passed-extended | 37.01 | 324.54 |
| minimum-repeat | 0 | 0 | passed-extended | 41.17 | 267.46 |
| deployment-projection-check | 0 | 0 | passed-extended | 39.64 | 267.85 |

Progress: `complete`. Floors are conditional on this hardware/software/desktop and the exercised requests, not a universal guarantee.

The projection-enabled deployment check is separate and is not pooled into projection-free performance comparisons.
