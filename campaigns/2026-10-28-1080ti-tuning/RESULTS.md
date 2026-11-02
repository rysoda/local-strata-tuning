# Tuning results

Live checkpoint. Speeds are tokens/s, medians. Five sampled decode passes are provisional; not significance or quality proof. All experiment deltas use the quality reference, NOT the approximate original baseline.

| Run | State | Code decode | 16K prefill | Decode delta | Prefill delta | Usage |
|---|---|---:|---:|---:|---:|---|
| baseline | complete | 36.08 | 381.83 | +24.6% | -0.9% | approximate original baseline only |
| quality-reference | complete | 28.95 | 385.46 | +0.0% | +0.0% | reference |
| ple-mmap | complete | 24.14 | 371.15 | -16.6% | -3.7% | not selected after combined review |
| reserve-1400 | complete | 28.28 | 345.77 | -2.3% | -10.3% | not selected after combined review |
| kv-resident-20480 | complete | 30.36 | 428.84 | +4.9% | +11.3% | not selected after combined review |
| host-last | complete | 30.49 | 421.14 | +5.3% | +9.3% | not selected after combined review |
| host-sibling | complete | 25.13 | 424.71 | -13.2% | +10.2% | not selected after combined review |
| workers-4 | complete | 27.59 | 426.87 | -4.7% | +10.7% | not selected after combined review |
| workers-3 | complete | 25.59 | 427.34 | -11.6% | +10.9% | not selected after combined review |
| tasks-36 | complete | 30.73 | 429.24 | +6.1% | +11.4% | USE (combined-confirmed) |
| tasks-72 | complete | 30.53 | 430.54 | +5.4% | +11.7% | not selected after combined review |
| pcie-0.15 | complete | 27.79 | 426.06 | -4.0% | +10.5% | not selected after combined review |
| pcie-0.4 | complete | 27.73 | 430.30 | -4.2% | +11.6% | not selected after combined review |
| pcie-balance | complete | 30.81 | 425.94 | +6.4% | +10.5% | USE (combined-confirmed) |
| spec-3 | complete | 29.51 | 429.61 | +1.9% | +11.5% | not selected after combined review |
| spec-5 | complete | 27.63 | 428.69 | -4.6% | +11.2% | not selected after combined review |
| confidence-0.3 | complete | 27.21 | 431.04 | -6.0% | +11.8% | not selected after combined review |
| confidence-0.7 | complete | 29.44 | 426.82 | +1.7% | +10.7% | not selected after combined review |
| lookup-chain-2 | complete | 30.56 | 428.49 | +5.6% | +11.2% | not selected after combined review |
| suffix-off | complete | 30.63 | 428.59 | +5.8% | +11.2% | not selected after combined review |
| draft-english | complete | 29.97 | 426.82 | +3.5% | +10.7% | not selected after combined review |
| draft-q4 | complete | 30.51 | 414.86 | +5.4% | +7.6% | not selected after combined review |
| adapt-every-1 | complete | 31.53 | 429.80 | +8.9% | +11.5% | USE (combined-confirmed) |
| adapt-every-8 | complete | 30.24 | 429.24 | +4.4% | +11.4% | not selected after combined review |
| adapt-swaps-48 | complete | 29.48 | 429.38 | +1.8% | +11.4% | not selected after combined review |
| adapt-swaps-160 | complete | 30.03 | 429.67 | +3.7% | +11.5% | not selected after combined review |
| adapt-decay-09 | complete | 30.53 | 428.35 | +5.4% | +11.1% | not selected after combined review |
| adapt-async | complete | 29.80 | 426.83 | +2.9% | +10.7% | not selected after combined review |
| adapt-overlap | complete | 29.78 | 430.31 | +2.8% | +11.6% | not selected after combined review |
| prefill-4096 | complete | 28.56 | 384.62 | -1.4% | -0.2% | not selected after combined review |
| prefill-2048 | complete | 29.95 | 297.79 | +3.4% | -22.7% | not selected after combined review |
| head-alias | failed | — | — | — | — | incompatible; see log |
| quality-reference-repeat | complete | 28.75 | 429.32 | -0.7% | +11.4% | reference |
| short-read-0 | complete | 30.02 | 424.02 | +3.7% | +10.0% | not selected after combined review |
| head-alias-compatible | complete | 29.70 | 290.88 | +2.6% | -24.5% | not selected after combined review |
| combined-resource | complete | 28.83 | 373.29 | -0.4% | -3.2% | not selected after combined review |
| combined-adaptive | complete | 31.99 | 377.00 | +10.5% | -2.2% | not selected after combined review |
| combined-lookup | complete | 31.48 | 375.35 | +8.7% | -2.6% | not selected after combined review |
| combined-draft | complete | 32.63 | 374.48 | +12.7% | -2.8% | not selected after combined review |
| quality-reference-postcombined | complete | 30.17 | 426.85 | +4.2% | +10.7% | reference |
| prefill-cap-5376 | complete | 30.31 | 428.47 | +4.7% | +11.2% | not selected after combined review |
| combined-draft-capped | complete | 29.82 | 377.52 | +3.0% | -2.1% | not selected after combined review |
| combined-simple-capped | complete | 32.51 | 422.19 | +12.3% | +9.5% | not selected after combined review |
| quality-reference-final | complete | 29.56 | 427.11 | +2.1% | +10.8% | reference |
| best-confirm-1 | complete | 30.80 | 422.15 | +6.4% | +9.5% | not selected after combined review |
| reference-confirm | complete | 29.71 | 429.25 | +2.6% | +11.4% | reference |
| best-confirm-2 | complete | 30.34 | 419.79 | +4.8% | +8.9% | not selected after combined review |
| ablate-no-host | complete | 31.97 | 428.29 | +10.4% | +11.1% | recommended combination |
| ablate-no-tasks | complete | 31.26 | 421.94 | +7.9% | +9.5% | not selected after combined review |
| ablate-no-balance | complete | 31.77 | 422.61 | +9.7% | +9.6% | not selected after combined review |
| adapt-only-confirm | complete | 30.78 | 430.12 | +6.3% | +11.6% | not selected after combined review |
| reference-after-ablations | complete | 29.75 | 428.68 | +2.7% | +11.2% | reference |
| final-candidate-1 | complete | 31.25 | 428.51 | +7.9% | +11.2% | recommended combination |
| reference-final-bracket | complete | 30.30 | 424.61 | +4.6% | +10.2% | reference |
| final-candidate-2 | complete | 31.27 | 426.38 | +8.0% | +10.6% | recommended combination |

## Checkpoint

Updated: 2026-10-29 06:20:46
Queue phase: tuning-complete; current: None

Each run has `results/<id>.json`, `.html`, `.engine.log`, `.server.log`, `.bench.log`, and `configs/private/<id>.json`. See `TUNING_PLAN.md` for interpretation and exclusions.

## Combined stage

See `STAGE1_REVIEW.md` and `COMBINED_RESULTS.md` for late-reference comparisons, combination rationale and status. Initial-reference deltas above are screening only; auto-sized cache/chunk drift confounds them.

## Final decision

Completed. See `FINAL_REPORT.md` for the final nearby-reference comparison and `configs/private/recommended.json` / repository `launchers/Run-1080Ti.cmd` for the ready-to-run profile. Initial-reference deltas in this table are NOT the final claimed gain. Only tasks 36, adaptation interval 1 and PCIe balance are retained as speed changes; approximate routing is disabled.
