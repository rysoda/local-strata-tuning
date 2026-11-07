# P100 120×38 mm server intake fan: exhaust comparison

[Campaign index](../../README.md) · [Manifest](manifest.json) · [Plan](PLAN.md) · [Work log](NOTES.md) · [Results table](REPORT.md)

**Complete: 6/6 new captures.** [Final comparison with historical results](COMPARISON.md): new intake + exhaust **67.39°C / 1322.92 MHz / 194.76 W**, versus intake alone **73.49°C / 1319.94 MHz / 196.95 W** (means). November 6 rear pull: **76.38°C / 1318.21 MHz / 197.54 W**; older one-fan reference: **78.92°C / 1231.20 MHz / 171.78 W**. Adding exhaust coincided with lower mean temperature; third both-fan run drifted warmer, so the final report flags uncertainty rather than claiming a clean causal gain. No inference-throughput measurement.

Physical sequence: **case open, prefill-only stress workload; both fans first, then exhaust removed for intake-only**. Exact prefill command/settings and exhaust details remain unconfirmed. **Revised order: B (both fans) first, then A (intake only)**, matching the installed setup at authorization. The supervisor enforces that order. User subsequently confirmed exhaust removal and heat soak; A completed after B. No active campaign monitors remain; existing server/workload was not stopped.

**[Yesterday’s full results tables](YESTERDAY_RESULTS.md)** summarize the three 2026-11-06 rear-pull-fan captures separately. Historical evidence is unchanged; these results are not pooled with this campaign.

- **A / intake:** one 120×38 mm nominal 4000 RPM server fan feeding the P100. User fan curve: **100% at 75°C**; lower-temperature curve and actual RPM not yet confirmed.
- **B / intake-exhaust:** same intake and curve, plus an exhaust fan. Exhaust model, location and speed not yet confirmed.
- Three sequential **600-second** captures per setup, ~1-second NVIDIA telemetry. Five minutes minimum continuous warm-up after each physical change; preferably wait for stable temperature/clocks. Run duration/interval are proposed defaults from prior cooling work.
- Existing P100-only Strata, engine/Control 0.1.55, Qwen3.8-Flash-Next IQ3_S, **131072 context**, int8 KV, full experts. No settings, server, network binding or credentials changed here.
- Workload is user-managed and must be documented and identical across both groups. No generated code executed. These are passive cooling measurements, not BetterBench inference-speed results.

## Intake-only A — second group, after B

Confirm intake-only physical setup, case/shroud arrangement, lower-temperature fan curve, fixed stress workload and warm-up. Record room temperature if available. Do not change any fan, workload, power/clock setting or case configuration during a group.

```sh
python campaigns/2026-11-07-p100-server-fan-intake-exhaust/scripts/capture.py intake --ready --warmup-minutes 5 --workload "EXACT SAME STRESS WORKLOAD AND SETTINGS" --setup-notes "CASE/SHROUD; INTAKE POSITION; FAN CURVE; NO EXHAUST" --ambient-c 22
```

Replace placeholders and example ambient with actual observations; omit `--ambient-c` if unknown. Never put keys/credentials in these declarations. The script only records the declaration; it does not establish equilibrium or verify fan RPM automatically.

## Intake + exhaust B — first group, currently installed

```sh
python campaigns/2026-11-07-p100-server-fan-intake-exhaust/scripts/capture.py intake-exhaust --ready --warmup-minutes 5 --workload "EXACT SAME STRESS WORKLOAD AND SETTINGS" --setup-notes "SAME CASE/INTAKE/CURVE; EXHAUST MODEL, POSITION, SPEED" --ambient-c 22
```

The workload string and inference configuration must match across groups exactly. No automatic transition from B to A: the program cannot install or confirm a physical fan. Each command takes roughly 30 minutes. Keep stress running throughout the captures.

## Outputs and restart safety

[REPORT.md](REPORT.md) is regenerated after every completed run: mean/min/max/within-run SD for temperature, SM clocks, power and utilization; energy, duration, samples/gaps; group repeatability; consecutive-run differences; final exhaust-minus-intake deltas. Machine-readable derived data: `results/analysis.json`. Original timestamped CSV/JSON remain unchanged. Regenerate without measuring:

```sh
python campaigns/2026-11-07-p100-server-fan-intake-exhaust/scripts/report.py
```

Exclusive `state/capture.lock`; `state/STOP` pauses between runs. Completed runs are skipped. Errors, orphaned evidence and incomplete attempts require explicit review; do not clear state or delete failed evidence to retry. Check live command lines and locks before resuming; saved PIDs are not ownership proof. Lock after an abrupt crash requires review. The monitor is reused unchanged from the open-case campaign; **its historical supervisor is never run**. No server/workload is started, stopped or reconfigured by these scripts. On interrupt only this campaign's newly created monitor may be terminated; raw partial files remain.

Sequential B-then-A runs can be confounded by ambient drift and workload differences; three samples per setup are descriptive, not statistical significance. Board power excludes fan electrical power. Actual fan tachometer RPM is unavailable until separately instrumented. No comparison with old campaigns is treated as a controlled result.
