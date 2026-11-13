# Strata 0.1.59: three quick benchmarks

Complete. Existing user server was not restarted, modified or stopped.

| Run | Decode tok/s | Prefill tok/s |
|---|---:|---:|
| quick-1 | 38.401 | 327.887 |
| quick-2 | 38.833 | 328.822 |
| quick-3 | 38.060 | 332.473 |
| **Mean of medians** | **38.431** | **329.728** |

Each run: 5/5 decode and 8/8 prefill samples. Exact quick code/16K-target workload; all actual token counts, samples and errors retained in results/*.json. Generated code not executed. No functional or long-context quality tests requested or performed.

## Historical comparison (not engine-only)

Current P100 x16 / 1080 Ti x4, engine 0.1.59 / Control 0.1.57, IQ3_S, 262144 context, int8 KV, resident32768, MTP, full experts, 36/12 split, reserves640/896. Existing experimental projection retained as diagnostic baseline; not recommended or validated here.

The same-topology 0.1.57 reserve campaign confirmations averaged 38.86 decode / 331.35 prefill **without projection**. Cooling has since changed. The Nov 6 installed-server 0.1.57 quick result was 37.591 / 342.376 **with projection**, but used x8/x8 and different settings/cooling. Neither isolates the engine update.

- Versus 0.1.57 same-topology, projection-free: decode -1.10%; prefill -0.49% (descriptive only).
- Versus 0.1.57 historical projected x8/x8: decode +2.23%; prefill -3.69% (descriptive only).

Three sequential quick runs are screening, not statistical significance or quality equivalence. User-server cache history and other activity are uncontrolled. A causal version comparison requires matching 0.1.57 runs with identical settings and hardware. No engine downgrade or upgrade was performed.
