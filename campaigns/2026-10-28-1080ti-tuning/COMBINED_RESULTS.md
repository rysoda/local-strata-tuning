# Combined-stage results

Same requested BetterBench workload and target model as stage 1. Median tokens/s. The deltas below retain the historical late-reference comparison; **use `FINAL_REPORT.md` and the final interleaved reference for the headline gain**, not these discovery deltas. The IDs containing `capped` name an attempted cap that source/log review proved was a no-op (`auto:5376` maps to ordinary auto).

| Run | State | Decode | Prefill | Decode vs late reference | Prefill vs late reference |
|---|---|---:|---:|---:|---:|
| quality-reference | complete | 28.95 | 385.46 | +0.7% | -10.2% |
| quality-reference-repeat | complete | 28.75 | 429.32 | +0.0% | +0.0% |
| short-read-0 | complete | 30.02 | 424.02 | +4.4% | -1.2% |
| head-alias-compatible | complete | 29.70 | 290.88 | +3.3% | -32.2% |
| combined-resource | complete | 28.83 | 373.29 | +0.3% | -13.1% |
| combined-adaptive | complete | 31.99 | 377.00 | +11.3% | -12.2% |
| combined-lookup | complete | 31.48 | 375.35 | +9.5% | -12.6% |
| combined-draft | complete | 32.63 | 374.48 | +13.5% | -12.8% |
| quality-reference-postcombined | complete | 30.17 | 426.85 | +4.9% | -0.6% |
| prefill-cap-5376 | complete | 30.31 | 428.47 | +5.4% | -0.2% |
| combined-draft-capped | complete | 29.82 | 377.52 | +3.7% | -12.1% |
| combined-simple-capped | complete | 32.51 | 422.19 | +13.1% | -1.7% |
| quality-reference-final | complete | 29.56 | 427.11 | +2.8% | -0.5% |
| best-confirm-1 | complete | 30.80 | 422.15 | +7.1% | -1.7% |
| reference-confirm | complete | 29.71 | 429.25 | +3.3% | -0.0% |
| best-confirm-2 | complete | 30.34 | 419.79 | +5.5% | -2.2% |
| ablate-no-host | complete | 31.97 | 428.29 | +11.2% | -0.2% |
| ablate-no-tasks | complete | 31.26 | 421.94 | +8.7% | -1.7% |
| ablate-no-balance | complete | 31.77 | 422.61 | +10.5% | -1.6% |
| adapt-only-confirm | complete | 30.78 | 430.12 | +7.0% | +0.2% |
| reference-after-ablations | complete | 29.75 | 428.68 | +3.5% | -0.1% |
| final-candidate-1 | complete | 31.25 | 428.51 | +8.7% | -0.2% |
| reference-final-bracket | complete | 30.30 | 424.61 | +5.4% | -1.1% |
| final-candidate-2 | complete | 31.27 | 426.38 | +8.7% | -0.7% |

## Rationale

- `short-read-0` isolates the prerequisite; `head-alias-compatible` adds head lending. The failed single head-alias startup remains in the original table.
- Resource core: KV residency 20480 + host last + tasks 36.
- Adaptive core adds interval 1 and PCIe balance.
- Lookup arm adds verified prompt lookup; draft arm instead tests verified-only smaller/quantized drafter and suffix-off. Target weights and int8 KV never change.
- Final selection: tasks 36 + adapt interval 1 + PCIe balance, with original host placement, KV residency and drafting. Both final confirmations gave about 31.26 decode; intervening reference 30.30. This is about +3.2% decode and similar prefill, not the larger historical-reference deltas above.
- Final candidate and reference each passed 6/6 functional/recall smoke checks. No formal significance or comprehensive quality-equivalence claim is made.

Completed 2026-10-29 06:19. Ready-to-run profile: `configs/private/recommended.json`; launcher: repository `launchers/Run-1080Ti.cmd`. Original installation unchanged.
