# Dual P100: three quick benchmarks

Complete. Existing user server was not restarted, modified or stopped.

| Run | Decode tok/s | Prefill tok/s |
|---|---:|---:|
| quick-1 | 31.827 | 345.244 |
| quick-2 | 33.091 | 344.676 |
| quick-3 | 31.085 | 343.908 |
| **Mean of medians** | **32.001** | **344.609** |

Each run: 5/5 decode and 8/8 prefill samples. Exact quick code/16K-target workload; all actual token counts, samples and errors retained in results/*.json. Generated code not executed. No functional or long-context quality tests requested or performed.

Actual measured prefill prompts were 11970–12190 model tokens; 16384 is the corpus target. GPU temperatures sampled at 15-second intervals peaked at 74°C on GPU 0 and 52°C on GPU 1; these are not continuous maxima or proof of no throttling. BetterBench flags p99 statistics as under-sampled; no p99 claim is made.

## Historical context (not a controlled hardware comparison)

The previous installed-server P100 + 1080 Ti 0.1.59 quick campaign averaged 38.431 decode / 329.728 prefill tok/s. Current dual-P100 measurements are **16.73% lower decode**, **4.51% higher prefill**. Hardware/topology, driver modes and conditions changed; this does not establish a cause. The inherited 36/12 split and reserves were not retuned for dual P100. No overall speed improvement is demonstrated for this decode-prioritized workload.

## Conditions and limitations

Two Tesla P100 16GB GPUs; actual link details retained in nvidia-smi.txt. Engine 0.1.59 / Control 0.1.57, IQ3_S, 262144 context, int8 KV, resident32768, MTP, full experts, 36/12 split, reserves640/896. Existing experimental projection retained as diagnostic baseline, not validated here. No settings, installation or startup launcher changed by the benchmark runner.

Three sequential quick runs are screening, not statistical significance or quality equivalence. User-server cache history and other activity are uncontrolled. Prior P100/1080 Ti results are different hardware and not a controlled comparison. Server left running at user request.
