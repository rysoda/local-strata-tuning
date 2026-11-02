# P100 + GTX 1080 Ti topology comparison

Current engine/control 0.1.55 throughout. Same IQ3_S weights, 131072 context, int8 KV, 32768 residency, full expert routing and previously selected speed settings. GPU 0 = P100 PCIe 3 x16 (TCC); GPU 1 = 1080 Ti PCIe 3 x4 (WDDM display).

Requested BetterBench quick code decode + 16K-target prefill, no concurrency. Medians in tokens/s; 5 code / 8 prefill samples. Screening, not significance or comprehensive quality proof. Old results are not directly comparable across engine/hardware changes.

| Run | Placement | State | Decode | Prefill |
|---|---|---|---:|---:|
| gpu-p100-only | P100 alone (x16) | complete | 33.99 | 293.05 |
| gpu-1080-only | 1080 Ti alone (x4) | complete | 22.96 | 192.71 |
| gpu-dual-p100-main | Both; P100 main; auto split | complete | 37.96 | 291.37 |
| gpu-dual-1080-main | Both; 1080 Ti main; auto split | complete | 38.60 | 296.44 |
| gpu-dual-p100-confirm | Both; P100 main; repeat | complete | 35.08 | 287.42 |
| gpu-dual-1080-confirm | Both; 1080 Ti main; repeat | complete | 35.93 | 283.96 |

Checkpoint: screening-complete-review-required; current None; 2026-11-01 23:10:16

Artifacts: `results/gpu-*.{json,engine.log,server.log,bench.log,gpu.csv}`. Private profiles in `configs/private/gpu-*.json` contain credentials. From repository root: `python campaigns/2026-11-01-p100-1080ti-x16-x4/scripts/run.py`. This completed historical queue exits without inference. Campaign `state/STOP-GPU` pauses between runs if deliberately extended.

Research: https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md . Main is the last stage and holds head/MTP; test both orders because P100 has more VRAM/HBM bandwidth/native FP16, while 1080 Ti has different compute and a slower host link. No approximate routing, lower precision, or unrelated parameter sweep.
