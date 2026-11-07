# P100 x16 + 1080 Ti chipset x4 — 256K report

**Completed:** targeted screens and nearby confirmation. Full quality, 262144 context; no speed projection. No significance or intelligence-equivalence claim.

[Every measured arm](RESULTS.md) · [Plan and limitations](PLAN.md) · [Work log](NOTES.md)

| Confirmation | Decode tok/s | Prefill tok/s | Smoke checks |
|---|---:|---:|---|
| f01-candidate | 37.47 | 325.60 | {'passed': 7, 'total': 7} |
| f02-p100-reference | 33.27 | 333.98 | {'passed': 7, 'total': 7} |
| f03-candidate-repeat | 35.32 | 326.31 | not repeated |

Candidate repeat mean: **36.40 decode / 325.96 prefill tok/s**. Against the intervening P100 reference: **+9.38% decode / -2.40% prefill**. Preference score ratio: 1.0391 (55% decode / 45% prefill).

Selected profile derives from `f03-candidate-repeat`. Candidate configuration: `{"id": "r09-trim36-safe", "gpu": [0, 1], "split": "36", "trim": true, "p100_reserve": 1400, "ti_reserve": 2304, "reason": "Neighbor split: 36 P100 / 12 display Main"}`. A near-tie needs further confirmation; the score is a stated preference, not a confidence interval.

Candidate and P100 reference each ran six standard functional/tool/32K/~119K checks plus a separate above-128K (~230K actual content tokens) recall check. Raw responses, actual API usage and prompt hashes are retained in the sanity artifacts. These do not validate all 256K workloads or comprehensive model quality. Generated code was never executed.

Cooling fixed: open case, intake + exhaust, 75°C target, intake capped at 45%. Per-run UUID-labeled hardware samples and reviews are preserved; memory headroom is only for the observed desktop workload. No fan, power, clock, page-file or installed-profile changes. Original low-reserve baselines remain evidence, not deployment recommendations.

Initial auto/1080-Main used automatic trim at K=35, so no claim of a clean no-trim control for that arm. mmap I/O results can depend on OS file-cache state. Pipeline and expert-peer arms were deliberately deferred given earlier instability/OOM and no evidence justifying risk on this constrained chipset arrangement. All performance results are for this topology/software, not future two-P100 x8+x8.

Ready profile: `configs/private/recommended-256k.json` (credential-bearing, ignored) and redacted shareable copy. Launch with repository `tools/launch.py` using this campaign ID. Test servers are stopped by owned-run cleanup.
