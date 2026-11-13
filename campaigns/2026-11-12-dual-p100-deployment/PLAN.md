# Two P100 deployment with existing settings — experiment plan

## Requested diagnostic — 2026-11-13

Run three sequential BetterBench screens against the existing dual-P100 user server, without restarting, retuning or changing its installed profile. Preserve IQ3_S, 262144 context, int8 KV, full experts, MTP, 36/12 split, reserves 640/896 MiB and existing experimental projection. This is an as-found diagnostic, not projection validation or a tuning comparison. No candidates or software upgrades. Use `--quick --decode --categories code --prefill --no-concurrency --config <repo>/workloads/betterbench-16k.json`. Save original results, all samples/errors, actual token counts, GPU telemetry and before/after metrics. Stop queue on errors; never stop the user server. `state/STOP` pauses between runs. Completed runs must not repeat; failed/incomplete state requires review. Existing installed help is retained in results/. No generated code is executed and no new quality-equivalence claim is made.

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
