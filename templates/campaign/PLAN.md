# {{title}} — experiment plan

## Comparison boundary

Record the fixed hardware/topology, installed engine/Control versions, model, precision, context and workload. Explain why this is a new campaign and link related campaigns.

## Baseline and quality reference

Measure untouched behavior first. If original expert approximations are enabled, retain that baseline but compare tuning against a separate full-expert reference. Record actual startup settings and memory headroom.

## Reasoned candidate list

| Setting | Baseline / candidate | Evidence and expected benefit | Quality/safety gate | Run ID |
|---|---|---|---|---|
| To research | — | Link source/help/community measurements | No quality-reducing tradeoff | — |

## Exclusions

Document settings not worth testing and why; avoid indiscriminate brute force.

## Measurement and confirmation

Use the repository BetterBench 16K-target workload with quick code decode/prefill and no concurrency. Retain all samples, actual prompt lengths, failures, thermal/clock/memory telemetry and startup logs. Treat individual gains as provisional. Review combined winners against nearby fresh references and run functional/tool/long-context smoke checks. Decode has slightly higher priority than prefill. Do not change workload/software mid-comparison or claim formal significance from quick screens.
