# Reserve performance — every attempt

| Run | P100 MiB | Ti MiB | Status | Decode | Prefill |
|---|---:|---:|---|---:|---:|
| control-original-reserves | 1400 | 2304 | passed-extended | 37.66 | 326.87 |
| p100-256-r1 | 256 | 2304 | passed-screen | 38.07 | 325.03 |
| p100-384-r1 | 384 | 2304 | passed-screen | 39.36 | 325.49 |
| p100-512-r1 | 512 | 2304 | passed-screen | 39.62 | 325.48 |
| p100-640-r1 | 640 | 2304 | passed-screen | 38.63 | 325.13 |
| p100-768-r1 | 768 | 2304 | passed-screen | 38.43 | 325.03 |
| p100-896-r1 | 896 | 2304 | passed-screen | 38.30 | 325.60 |
| p100-1024-r1 | 1024 | 2304 | passed-screen | 37.51 | 327.13 |
| p100-1024-r2 | 1024 | 2304 | passed-screen | 37.98 | 324.77 |
| p100-896-r2 | 896 | 2304 | passed-screen | 39.09 | 326.13 |
| p100-768-r2 | 768 | 2304 | passed-screen | 39.98 | 325.92 |
| p100-640-r2 | 640 | 2304 | passed-screen | 37.62 | 326.76 |
| p100-512-r2 | 512 | 2304 | passed-screen | 39.24 | 324.65 |
| p100-384-r2 | 384 | 2304 | passed-screen | 37.05 | 326.55 |
| p100-256-r2 | 256 | 2304 | passed-screen | 39.64 | 325.97 |
| reference-after-p100 | 1400 | 2304 | passed-screen | 37.23 | 323.71 |
| ti-1024-r1 | 1400 | 1024 | passed-screen | 38.12 | 329.99 |
| ti-896-r1 | 1400 | 896 | passed-screen | 40.54 | 328.19 |
| ti-768-r1 | 1400 | 768 | passed-screen | 38.27 | 328.55 |
| ti-640-r1 | 1400 | 640 | passed-screen | 38.32 | 329.01 |
| ti-512-r1 | 1400 | 512 | passed-screen | 37.62 | 329.90 |
| ti-384-r1 | 1400 | 384 | passed-screen | 38.82 | 330.61 |
| ti-256-r1 | 1400 | 256 | passed-screen | 38.49 | 329.59 |
| ti-256-r2 | 1400 | 256 | passed-screen | 39.25 | 330.98 |
| ti-384-r2 | 1400 | 384 | passed-screen | 38.42 | 330.59 |
| ti-512-r2 | 1400 | 512 | passed-screen | 39.32 | 330.94 |
| ti-640-r2 | 1400 | 640 | passed-screen | 38.04 | 328.57 |
| ti-768-r2 | 1400 | 768 | passed-screen | 38.59 | 329.23 |
| ti-896-r2 | 1400 | 896 | passed-screen | 38.72 | 328.47 |
| ti-1024-r2 | 1400 | 1024 | passed-screen | 39.16 | 327.23 |
| reference-after-ti | 1400 | 2304 | passed-screen | 38.11 | 327.22 |
| joint-p768-t896 | 768 | 896 | passed-screen | 38.04 | 328.41 |
| joint-p512-t512 | 512 | 512 | passed-screen | 39.49 | 332.50 |
| joint-p640-t896 | 640 | 896 | passed-screen | 41.47 | 329.52 |
| joint-p896-t896 | 896 | 896 | passed-screen | 37.56 | 329.07 |
| joint-p768-t768 | 768 | 768 | passed-screen | 37.81 | 333.51 |
| joint-p768-t1024 | 768 | 1024 | passed-screen | 40.05 | 330.25 |
| joint-p512-t256 | 512 | 256 | passed-screen | 40.27 | 328.06 |
| joint-repeat-p640-t896 | 640 | 896 | passed-screen | 40.04 | 330.20 |
| joint-repeat-p512-t256 | 512 | 256 | passed-screen | 39.20 | 325.00 |
| confirm-candidate-1 | 640 | 896 | passed-extended | 38.17 | 330.62 |
| confirm-reference-1 | 1400 | 2304 | passed-extended | 37.50 | 325.71 |
| confirm-candidate-2 | 640 | 896 | passed-screen | 40.11 | 333.26 |
| confirm-reference-2 | 1400 | 2304 | passed-screen | 37.71 | 324.13 |
| confirm-candidate-3 | 640 | 896 | passed-extended | 38.30 | 330.16 |
| confirm-reference-3 | 1400 | 2304 | passed-screen | 37.25 | 328.09 |

Phase: **complete**. All raw samples, token counts and errors remain in results/. Quick screens are not significance claims.

[Plan](PLAN.md) · [Report](REPORT.md)
