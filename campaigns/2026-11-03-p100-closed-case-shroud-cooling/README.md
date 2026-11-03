# P100 closed-case shroud cooling

[Campaign index](../../README.md) · [Manifest](manifest.json) · [Measurement plan](PLAN.md) · [Work log](NOTES.md)

**Completed review: keep the auxiliary intake fan off provisionally for this exact arrangement.** With the case closed and a fan shroud installed, the primary fan alone sustained the highest P100 board power and SM clocks at approximately 79°C. Turning on the second fan generally reduced both. These are cooling telemetry results, not measured inference-speed gains.

## Physical setup and workload

User-confirmed setup: **closed case, fan shroud, primary fan operating**, plus a **second fan at the edge of the shroud drawing air in from outside**. “One fan” means this auxiliary fan is off; the other settings are its commanded 25%, 50%, 75% and 100% speeds. Its physical presence is not a tested variable. Fan models, actual RPM, dimensions, primary-fan speed and ambient/inlet temperatures were not recorded.

GPU: Tesla P100-PCIE-16GB, UUID `GPU-bab5c751-1e02-b6a7-cf6f-b6256c3a5999`. Intended workload: the user-managed P100-only Strata prefill stress test. Exact invocation, software versions and proof of fixed workload/settings were not captured. The monitor only observed telemetry; it did not control the workload. No inference configuration, model or GPU setting was changed for this review.

This is separate from the earlier [open-case, unducted campaign](../2026-11-03-p100-open-case-cooling/README.md). Do not pool these physical comparisons or attribute differences between them solely to the shroud.

## All measurements

All 11 runs completed 600 seconds on 2026-11-03. Times below are UTC. Power and clock values are time-weighted sample-and-hold means, verified against the original CSVs. Each evidence link opens the JSON summary; its `csv_file` names the neighboring raw CSV in [results/](results/).

| Start UTC | Auxiliary fan | Run | Mean board power | Mean SM clock | Evidence |
|---|---|---|---:|---:|---|
| 19:17:00 | Off | 1, possible warm-up | 163.98 W | 1204.3 MHz | [JSON](results/20261103T191700.411468Z-closed-1fan-1-json.json) |
| 19:27:06 | Off | 1bis | 159.99 W | 1194.7 MHz | [JSON](results/20261103T192706.955593Z-closed-1fan-1bis-json.json) |
| 19:37:33 | 100% | 1 | 148.12 W | 1159.6 MHz | [JSON](results/20261103T193733.289621Z-closed-2fan-100-1-json.json) |
| 19:48:42 | 75% | 1 | 146.81 W | 1141.0 MHz | [JSON](results/20261103T194842.834385Z-closed-2fan-75-1-json.json) |
| 20:00:32 | 50% | 1 | 151.46 W | 1160.8 MHz | [JSON](results/20261103T200032.814272Z-closed-2fan-50-1-json.json) |
| 20:17:59 | 25% | 1 | 158.90 W | 1191.5 MHz | [JSON](results/20261103T201759.795036Z-closed-2fan-25-1-json.json) |
| 20:32:56 | Off | 2 | 165.63 W | 1205.2 MHz | [JSON](results/20261103T203256.121894Z-closed-1fan-2-json.json) |
| 20:44:03 | 25% | 2 | 158.35 W | 1177.2 MHz | [JSON](results/20261103T204403.503281Z-closed-2fan-25-2-json.json) |
| 21:02:47 | 50% | 2 | 151.76 W | 1164.4 MHz | [JSON](results/20261103T210247.125361Z-closed-2fan-50-2-json.json) |
| 21:17:28 | 75% | 2 | 149.60 W | 1151.4 MHz | [JSON](results/20261103T211728.005777Z-closed-2fan-75-2-json.json) |
| 21:28:40 | 100% | 2 | 150.17 W | 1160.8 MHz | [JSON](results/20261103T212840.375709Z-closed-2fan-100-2-json.json) |

Actual order was **off → off again → 100 → 75 → 50 → 25 → off → 25 → 50 → 75 → 100**. The first off run was repeated because the user suspected insufficient warm-up. That suspicion is retained, not treated as proven or used to erase the measurement.

## Setup averages and interpretation

For a balanced two-run comparison, the main off reference uses **1bis and 2**, excluding only the first suspected warm-up run. All runs remain above.

| Auxiliary fan | Selected runs | Mean board power | Mean SM clock |
|---|---|---:|---:|
| **Off** | **1bis + 2** | **162.81 W** | **1199.9 MHz** |
| 25% | 1 + 2 | 158.63 W | 1184.4 MHz |
| 50% | 1 + 2 | 151.61 W | 1162.6 MHz |
| 75% | 1 + 2 | 148.20 W | 1146.2 MHz |
| 100% | 1 + 2 | 149.14 W | 1160.2 MHz |

Including all three off runs gives **163.20 W / 1201.4 MHz**, so the broad conclusion does not depend on discarding the first run. Compared with 100%, the balanced off reference sustained **13.67 W more (+9.2%)** and **39.7 MHz more (+3.4%)**. The off-versus-25% margin is smaller: **4.18 W / 15.6 MHz**, with appreciable off-run variation; do not overstate its certainty.

- Average temperatures were approximately **78.95–78.99°C** across individual runs. Similar temperature does not mean similar cooling when clocks/power can adjust to a thermal ceiling. Higher sustained power accompanied by higher clocks at the same temperature is consistent with better effective cooling under comparable load. Thermal throttle flags were not captured, so this mechanism is not directly verified.
- All CSV samples report a **250 W power limit**. Mean GPU utilization was **99.57–99.88%**; this supports sustained load but does not prove identical work.
- The broad separation remains in the last five minutes: off **161.51 / 162.70 W** (selected runs), 25% **161.58 / 158.55 W**, 50% **151.07 / 151.26 W**, 75% **146.66 / 148.33 W**, 100% **147.23 / 149.39 W**. The small off-versus-25% difference is not cleanly separated in every window.
- Each run has 562–566 samples; the largest sample gap is 1.688 seconds. All runs completed without reported errors. Recomputed power, temperature, utilization and clock means match the JSON summaries within 1e-6.
- Increasing the auxiliary fan is not strictly monotonic: 100% recovers somewhat versus 75%. Two repeats do not establish an exact optimal speed curve.

The auxiliary intake may disturb flow through the shroud/heatsink or promote recirculation, but these measurements **do not identify the airflow mechanism**. Its outside-air source alone does not guarantee that it improves heatsink flow.

## Recommendation, limitations and further measurements

**Leave the second, outside-air intake fan off for this tested closed-case/shroud arrangement, provisionally.** Do not generalize this to different fan positions, shrouds, ambient conditions or workloads. Higher GPU power is not an electrical-efficiency gain; fan consumption and delivered work were not measured.

Only two comparison runs per setting are available, with suspected warm-up and unmeasured ambient drift. Exact workload/software provenance, RPM, throttle reasons and throughput are missing. There is no statistical-significance, inference-speed or model-quality-equivalence claim. The inference deployment recommendation elsewhere in the repository is unchanged.

Review is complete; **no automatic queue or owned process exists in this campaign**. No resume command is needed. For a new confirmation, record the missing conditions, stabilize first, and alternate off/25% or off/100% under the same workload. Use unique labels and retain incomplete attempts. The existing passive monitor can target this campaign explicitly (one measurement at a time, after checking no other monitor is writing the same comparison):

```sh
python campaigns/2026-11-03-p100-open-case-cooling/scripts/monitor_power.py --label closed-shroud-aux-off-confirmation --output-dir campaigns/2026-11-03-p100-closed-case-shroud-cooling/results
```

This command only observes telemetry; it starts no stress workload and provides no thermal protection. Do not relaunch completed inference campaigns.

## Evidence preservation

The 11 CSV/JSON pairs were moved from the open-case campaign without changing filenames or bytes. [Relocation hashes](results/relocation-sha256.json) record original paths, new paths and SHA-256 values for all 22 files. Historical labels ending in `.json` are retained exactly. The manifest and [review checkpoint](state/queue-state.json) describe this completed telemetry review, not BetterBench runs.
