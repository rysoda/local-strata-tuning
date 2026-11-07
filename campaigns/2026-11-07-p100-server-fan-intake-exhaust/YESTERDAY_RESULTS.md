# Yesterday’s cooling reference — 2026-11-06

[New campaign](README.md) · [Original campaign](../2026-11-06-p100-rear-exhaust-cooling/README.md)

**Historical reference only; no new measurements taken.** Three completed 600-second rear-pull-fan captures, using P100-only Strata at 131072 context, engine/Control 0.1.55. Original CSV/JSON are unchanged. Yesterday’s exact workload, fan speeds/model, case/shroud and ambient temperature were not independently captured. Today’s open-case/prefill-only declaration does not retroactively establish yesterday’s conditions. Do not treat differences against the new 120×38 mm intake setup as a controlled exhaust effect.

Means and within-run population SD are time-weighted sample-and-hold, including the last interval. Max/min are sampled values. Board power excludes fan power. SM clock is not inference throughput.

## Main comparison table

| Run | Temp mean °C | Temp max °C | SM mean MHz | SM max MHz | Power mean W | Power max W | GPU mean % | GPU max % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 76.12 | 77.00 | 1318.16 | 1328.00 | 197.95 | 258.50 | 99.58 | 100.00 |
| 2 | 76.49 | 77.00 | 1318.55 | 1328.00 | 196.49 | 256.97 | 99.38 | 100.00 |
| 3 | 76.52 | 77.00 | 1317.93 | 1328.00 | 198.18 | 261.65 | 99.43 | 100.00 |

## Minimums and within-run variation

| Run | Temp min °C | Temp SD °C | SM min MHz | SM SD MHz | Power min W | Power SD W | GPU min % | GPU SD % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 72.00 | 0.62 | 1303.00 | 10.11 | 53.42 | 26.22 | 11.00 | 5.19 |
| 2 | 72.00 | 0.66 | 1303.00 | 10.39 | 52.96 | 27.00 | 3.00 | 7.22 |
| 3 | 72.00 | 0.66 | 1278.00 | 10.60 | 52.92 | 27.25 | 4.00 | 6.04 |

## Sampling, energy and raw evidence

| Run | Start UTC | Seconds | Samples | Max gap s | Board Wh | Raw CSV / JSON |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-11-06T17:25:51.928683+00:00 | 600.00 | 566 | 1.09 | 32.99 | [CSV](../2026-11-06-p100-rear-exhaust-cooling/results/20261106T172551.928683Z-rear-pull-reference-1.csv) / [JSON](../2026-11-06-p100-rear-exhaust-cooling/results/20261106T172551.928683Z-rear-pull-reference-1.json) |
| 2 | 2026-11-06T17:35:52.530002+00:00 | 600.00 | 567 | 1.09 | 32.75 | [CSV](../2026-11-06-p100-rear-exhaust-cooling/results/20261106T173552.530002Z-rear-pull-reference-2.csv) / [JSON](../2026-11-06-p100-rear-exhaust-cooling/results/20261106T173552.530002Z-rear-pull-reference-2.json) |
| 3 | 2026-11-06T17:45:53.143168+00:00 | 600.00 | 566 | 1.09 | 33.03 | [CSV](../2026-11-06-p100-rear-exhaust-cooling/results/20261106T174553.143168Z-rear-pull-reference-3.csv) / [JSON](../2026-11-06-p100-rear-exhaust-cooling/results/20261106T174553.143168Z-rear-pull-reference-3.json) |

## Across-run summary

Each run has equal duration. Across-run SD is sample SD of the three run means; range is highest minus lowest run mean.

| Metric | Overall mean | Across-run SD | Run-mean range | Lowest sample | Highest sample |
| --- | --- | --- | --- | --- | --- |
| Temp °C | 76.38 | 0.23 | 0.41 | 72.00 | 77.00 |
| SM clock MHz | 1318.21 | 0.31 | 0.61 | 1278.00 | 1328.00 |
| Board W | 197.54 | 0.91 | 1.68 | 52.92 | 261.65 |
| GPU % | 99.46 | 0.10 | 0.19 | 3.00 | 100.00 |

Total capture: **1800 s**; total board energy: **98.77 Wh**; total samples: **1699**.

## Run-to-run differences

Signed deltas use run means; later minus earlier. Percentages use the earlier run as denominator. Celsius percentages are not thermodynamic ratios: prefer absolute °C deltas.

| Runs | Metric | Mean Δ | Mean Δ % | Observed max Δ |
| --- | --- | --- | --- | --- |
| 2 − 1 | Temp °C | 0.37 | 0.49 | 0.00 |
| 2 − 1 | SM clock MHz | 0.38 | 0.03 | 0.00 |
| 2 − 1 | Board W | -1.45 | -0.73 | -1.53 |
| 2 − 1 | GPU % | -0.19 | -0.19 | 0.00 |
| 3 − 2 | Temp °C | 0.03 | 0.04 | 0.00 |
| 3 − 2 | SM clock MHz | -0.61 | -0.05 | 0.00 |
| 3 − 2 | Board W | 1.68 | 0.86 | 4.68 |
| 3 − 2 | GPU % | 0.05 | 0.05 | 0.00 |
| 3 − 1 | Temp °C | 0.41 | 0.53 | 0.00 |
| 3 − 1 | SM clock MHz | -0.23 | -0.02 | 0.00 |
| 3 − 1 | Board W | 0.23 | 0.12 | 3.15 |
| 3 − 1 | GPU % | -0.14 | -0.14 | 0.00 |

Three sequential captures describe repeatability, not statistical significance. No ambient-adjusted temperature delta, actual fan RPM or inference-speed difference can be recovered from this evidence. Source-file SHA-256 hashes and unrounded derived values are retained in results/yesterday-analysis.json.
