# Minimum reliable reserve — results

**Smallest validated pair found: P100 0 MiB / GTX 1080 Ti 0 MiB.** Fixed 36/12 trimmed placement, 262144 context, IQ3_S, full experts, int8 KV, MTP unchanged.

These are explicit reserve flags, NOT total unused VRAM: the installed engine separately budgets late CUDA allocations, later-stage windows and MTP/head. Search refines integer MiB under a local monotonic assumption; display activity, sampling/OS variance and future requests can move the boundary. This is an observed tested floor, not a universal guarantee.

[Every attempt, including boundaries](RESULTS.md) · [Plan](PLAN.md) · [Work log](NOTES.md)

| Nearby confirmation | Decode tok/s | Prefill tok/s | Smoke checks |
|---|---:|---:|---|
| validated-joint-minimum | 39.21 | 251.27 | {'passed': 7, 'total': 7} |
| nearby-original-reserves | 37.01 | 324.54 | {'passed': 7, 'total': 7} |
| minimum-repeat | 41.17 | 267.46 | {'passed': 7, 'total': 7} |

**Performance tradeoff:** the two projection-free minimum-reserve confirmations averaged **40.19 decode / 259.36 prefill tok/s**, versus the intervening control **37.01 / 324.54**: **+8.60% decode / −20.08% prefill**. The smallest passing reserve is therefore not automatically the best overall performance setting. These quick repeats do not establish significance or prove the cause of the prefill regression.

Independent benchmark screening floors: {"p100_mib": 0, "ti_mib": 0}. Extended checks at minimal candidate/control/repeat each include six standard functional/tool/~119K tests and one ~230K actual-content-token recall test. Actual API token counts and raw responses retained. No generated code executed.

Projection-enabled compatibility check: **passed**. This arm is separately labeled, not pooled with projection-free speeds. Smoke success is not quality equivalence.

Acceptance does not require an arbitrary 1 GiB free VRAM. Allocation failures, predeclared no-progress boundary, severe throughput loss, retries, non-finite output and functional failures are preserved; unexpected failures pause. Smaller tested values and per-device observed minima are in state/results. No statistical-significance claim. No application/fan/power/clock/page-file/target precision/context changes.

**Startup remains unchanged.** Ready scientific profile is configs/private/recommended-minimum.json with a redacted shareable copy. Projection-compatible copy exists only if that separate check passed. Test processes are stopped; original installed profiles and previous completed campaigns remain untouched.
