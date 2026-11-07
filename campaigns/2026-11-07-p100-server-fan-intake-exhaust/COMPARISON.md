# P100 cooling: final comparison

**Completed: 6/6 new captures.** Three intake-only and three intake + exhaust runs, each 600 seconds. Case open; prefill-only user-managed stress; 120×38 mm nominal 4000 RPM intake curve reaches 100% at 75°C. P100-only Strata 0.1.55, Qwen3.8-Flash-Next IQ3_S, 131072 context, int8 KV, full expert routing. Actual fan RPM, ambient, lower-temperature curve and exact stress invocation were not recorded.

[New six-run detailed tables](REPORT.md) · [Yesterday’s detailed tables](YESTERDAY_RESULTS.md) · [Old open-case source report](../2026-11-03-p100-open-case-cooling/README.md)

## Main comparison

Each cell shows **time-weighted mean / highest sampled value**. Equal-duration runs give equal-weight group means. Board power excludes external fan power; higher/lower board power alone is not cooling efficiency or throughput.

| Setup | Runs × min | Temp °C mean / max | SM MHz mean / max | Board W mean / max | GPU % mean |
| --- | --- | --- | --- | --- | --- |
| New intake only | 3 × 10 | 73.49 / 77.00 | 1319.94 / 1328.00 | 196.95 / 258.50 | 99.73 |
| New intake + exhaust | 3 × 10 | 67.39 / 77.00 | 1322.92 / 1328.00 | 194.76 / 255.10 | 99.71 |
| Nov 6 rear pull | 3 × 10 | 76.38 / 77.00 | 1318.21 / 1328.00 | 197.54 / 261.65 | 99.46 |
| Nov 3 old one fan | 2 × 10 | 78.92 / 80.00 | 1231.20 / 1328.00 | 171.78 / 253.32 | 99.21 |

**The remembered ~170 W result is confirmed:** the selected November 3 one-fan runs averaged 171.78 W (172.01 W and 171.54 W). They were open-case and unducted. Their fan geometry/direction was not recorded, so calling them definitively “without the pulling fan” would go beyond the saved evidence; they are labeled “old one fan.”

## Differences in group means

Signed change = named setup minus reference; percentages use reference means. Only the new intake-versus-intake+exhaust comparison is within this campaign. Historical differences are descriptive, not isolated causal gains.

| Comparison | Temp Δ °C | SM Δ MHz | SM Δ % | Board Δ W | Board Δ % |
| --- | --- | --- | --- | --- | --- |
| New intake + exhaust − New intake only | -6.10 | 2.98 | 0.23 | -2.19 | -1.11 |
| New intake only − Nov 6 rear pull | -2.89 | 1.73 | 0.13 | -0.59 | -0.30 |
| New intake + exhaust − Nov 6 rear pull | -8.99 | 4.71 | 0.36 | -2.77 | -1.40 |
| New intake only − Nov 3 old one fan | -5.44 | 88.74 | 7.21 | 25.17 | 14.66 |
| New intake + exhaust − Nov 3 old one fan | -11.54 | 91.72 | 7.45 | 22.99 | 13.38 |
| Nov 6 rear pull − Nov 3 old one fan | -2.55 | 87.01 | 7.07 | 25.76 | 15.00 |

## Interpretation

- **Adding exhaust coincided with a 6.10°C lower mean temperature**, 2.98 MHz higher mean SM clock (+0.23%) and 2.19 W lower mean board power (−1.11%). Peak sampled temperature was 77°C in both groups; peak clock was 1328 MHz in both. The practical observed advantage is temperature headroom, not a demonstrated inference-speed improvement.
- **The new intake alone is a clear descriptive improvement over the old ~170 W operating point:** 5.44°C lower mean GPU temperature and 88.74 MHz higher mean clock (+7.21%), while sustaining 25.17 W more board power (+14.66%). Different dates, uncertain workload/software provenance and changed fan geometry prevent treating these as controlled causal deltas.
- Relative to November 6, the new intake alone was 2.89°C cooler at essentially the same clocks/power; intake + exhaust was 8.99°C cooler. Yesterday’s precise case/workload/fan speeds/ambient were not independently captured, so these are historical references only.
- **Important drift caveat:** both-fan run 3 averaged 70.12°C and reached 77°C, compared with ~66°C means and 67°C maxima in runs 1–2. All three remain included. This could reflect a physical/control/ambient change or another cause; the timing of exhaust removal relative to that run is not established. It weakens a clean fixed-setup interpretation. Intake-only run means were much tighter (73.38–73.69°C).
- Provisionally, use intake + exhaust when temperature headroom is the priority, subject to confirming that the exhaust remained installed/unchanged through all three captures. The new intake alone also maintained near-maximum clocks. Noise, fan electrical consumption, throughput and actual thermal-throttle flags were not measured.

## Repeatability of run means

Sample SD across run means and their range describe repeatability, not independent-sample confidence intervals.

| Setup | Temp SD / range °C | SM SD / range MHz | Board SD / range W |
| --- | --- | --- | --- |
| New intake only | 0.18 / 0.31 | 0.11 / 0.23 | 1.22 / 2.41 |
| New intake + exhaust | 2.36 / 4.11 | 1.30 / 2.35 | 0.64 / 1.13 |
| Nov 6 rear pull | 0.23 / 0.41 | 0.31 / 0.61 | 0.91 / 1.68 |
| Nov 3 old one fan | 0.05 / 0.06 | 2.66 / 3.76 | 0.33 / 0.47 |

## Every selected run

| Setup / run | Temp mean / max °C | SM mean / max MHz | Board mean / max W | GPU mean % | Samples | Wh | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| New intake only / 1 | 73.39 / 77.00 | 1319.94 / 1328.00 | 198.28 / 255.49 | 99.87 | 565 | 33.05 | [CSV](../2026-11-07-p100-server-fan-intake-exhaust/results/20261107T125314.991061Z-intake-1.csv) / [JSON](../2026-11-07-p100-server-fan-intake-exhaust/results/20261107T125314.991061Z-intake-1.json) |
| New intake only / 2 | 73.69 / 77.00 | 1320.05 / 1328.00 | 195.86 / 254.90 | 99.44 | 565 | 32.64 | [CSV](../2026-11-07-p100-server-fan-intake-exhaust/results/20261107T130316.492069Z-intake-2.csv) / [JSON](../2026-11-07-p100-server-fan-intake-exhaust/results/20261107T130316.492069Z-intake-2.json) |
| New intake only / 3 | 73.38 / 77.00 | 1319.82 / 1328.00 | 196.71 / 258.50 | 99.87 | 566 | 32.79 | [CSV](../2026-11-07-p100-server-fan-intake-exhaust/results/20261107T131317.971244Z-intake-3.csv) / [JSON](../2026-11-07-p100-server-fan-intake-exhaust/results/20261107T131317.971244Z-intake-3.json) |
| New intake + exhaust / 1 | 66.00 / 67.00 | 1323.56 / 1328.00 | 194.03 / 253.08 | 99.43 | 566 | 32.34 | [CSV](../2026-11-07-p100-server-fan-intake-exhaust/results/20261107T115851.337003Z-intake-exhaust-1.csv) / [JSON](../2026-11-07-p100-server-fan-intake-exhaust/results/20261107T115851.337003Z-intake-exhaust-1.json) |
| New intake + exhaust / 2 | 66.04 / 67.00 | 1323.78 / 1328.00 | 195.12 / 253.81 | 99.96 | 566 | 32.52 | [CSV](../2026-11-07-p100-server-fan-intake-exhaust/results/20261107T120852.836431Z-intake-exhaust-2.csv) / [JSON](../2026-11-07-p100-server-fan-intake-exhaust/results/20261107T120852.836431Z-intake-exhaust-2.json) |
| New intake + exhaust / 3 | 70.12 / 77.00 | 1321.43 / 1328.00 | 195.15 / 255.10 | 99.73 | 566 | 32.53 | [CSV](../2026-11-07-p100-server-fan-intake-exhaust/results/20261107T121854.305605Z-intake-exhaust-3.csv) / [JSON](../2026-11-07-p100-server-fan-intake-exhaust/results/20261107T121854.305605Z-intake-exhaust-3.json) |
| Nov 6 rear pull / 1 | 76.12 / 77.00 | 1318.16 / 1328.00 | 197.95 / 258.50 | 99.58 | 566 | 32.99 | [CSV](../2026-11-06-p100-rear-exhaust-cooling/results/20261106T172551.928683Z-rear-pull-reference-1.csv) / [JSON](../2026-11-06-p100-rear-exhaust-cooling/results/20261106T172551.928683Z-rear-pull-reference-1.json) |
| Nov 6 rear pull / 2 | 76.49 / 77.00 | 1318.55 / 1328.00 | 196.49 / 256.97 | 99.38 | 567 | 32.75 | [CSV](../2026-11-06-p100-rear-exhaust-cooling/results/20261106T173552.530002Z-rear-pull-reference-2.csv) / [JSON](../2026-11-06-p100-rear-exhaust-cooling/results/20261106T173552.530002Z-rear-pull-reference-2.json) |
| Nov 6 rear pull / 3 | 76.52 / 77.00 | 1317.93 / 1328.00 | 198.18 / 261.65 | 99.43 | 566 | 33.03 | [CSV](../2026-11-06-p100-rear-exhaust-cooling/results/20261106T174553.143168Z-rear-pull-reference-3.csv) / [JSON](../2026-11-06-p100-rear-exhaust-cooling/results/20261106T174553.143168Z-rear-pull-reference-3.json) |
| Nov 3 old one fan / 1 | 78.96 / 80.00 | 1229.32 / 1328.00 | 172.01 / 253.32 | 99.62 | 565 | 28.67 | [CSV](../2026-11-03-p100-open-case-cooling/results/20261103T150015.811323Z-open-1fan-1-json.csv) / [JSON](../2026-11-03-p100-open-case-cooling/results/20261103T150015.811323Z-open-1fan-1-json.json) |
| Nov 3 old one fan / 2 | 78.89 / 80.00 | 1233.08 / 1328.00 | 171.54 / 250.65 | 98.80 | 566 | 28.59 | [CSV](../2026-11-03-p100-open-case-cooling/results/20261103T152207.850774Z-open-1fan-2-json.csv) / [JSON](../2026-11-03-p100-open-case-cooling/results/20261103T152207.850774Z-open-1fan-2-json.json) |

## Measurement and scope limits

All 11 selected historical/new CSVs were recomputed using the same sample-and-hold method, including the final sampling interval, and checked against original JSON means within 1e-6. Only complete 600-second captures are included; the old interrupted attempt and earlier exploratory runs remain excluded as in their source report. Original raw CSV/JSON bytes were not changed. Unrounded derived values, within-run min/max/SD, sample gaps, energy and source SHA-256 hashes are preserved in results/comparison-analysis.json.

New order was both-fans then intake-only, with user-reported heat soak. Sequential order, unmeasured ambient/RPM, fan-curve feedback, brief utilization dips and unrecorded exact workload prevent significance/efficiency claims. Historical configurations are not pooled as repeats of the new fan setups. This is cooling telemetry, not a BetterBench result, model-quality test or inference-speed benchmark. No new measurement was started for reporting; the user-managed server/workload is left untouched.
