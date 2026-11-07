# Work log

## 2026-11-07 — created, awaiting setup confirmation

User requests a new cooling campaign: 120×38 mm nominal 4000 RPM intake server fan, curve reaching 100% at 75°C; three single-fan captures, then three with an exhaust fan, with complete comparative tables.

Created a fresh campaign using tools/new_campaign.py. Read repository conventions, existing monitor and rear-pull supervisor; historical campaigns/state left untouched. Proposed 600-second captures at ~1-second intervals, matching prior passive cooling measurements. No measurements started and no fan settings changed.

Live preflight at creation found Control PID 5624 and engine PID 4676 (historical identifiers; reverify before action), existing P100-only 131072-context server from the user's prior request. P100 telemetry: 66°C, 100% utilization, 1328 MHz, 250 W power limit; this single observation is not a benchmark or proof of thermal equilibrium. NVIDIA driver 582.66. User-managed workload appears active but exact invocation/settings are not yet documented. Existing 1080 Ti remains the display card. No server/network/API changes made.

Unknown: current physical setup, lower-temperature fan curve, exhaust model/location/speed, case/shroud, room temperature, precise workload and heat-soak readiness. Await confirmation before A. A-to-B transition requires manual confirmation and fresh warm-up. Do not infer setup or readiness solely from GPU telemetry.

Scripts checkpoint every capture, refuse incomplete/error state and competing monitors/queues, preserve raw CSV/JSON, and rebuild tables after complete captures. No automated fan/workload control; no generated code execution. Existing user-managed server/workload intentionally left running. Unrelated quick-benches and historical modified logs/state left untouched.

Validation: five synthetic tests passed (time weighting/final interval, missing telemetry rejection, six-run report/partial exclusion, completed-group no-op, incomplete-state refusal). Read-only live preflight passed for P100-only loaded model/context; no capture launched. Repository validation passed for seven campaigns, 648 unchanged archived artifacts, privacy and Markdown links. Initial REPORT.md contains no measured results (0/6).

## User update — hold measurements; historical tables

User confirms case open, prefill-only stress workload, both intake and exhaust currently installed. Explicitly requested no measurements yet. New campaign remains 0/6; created state/STOP to enforce the hold. Proposed intake-first order remains unstarted and requires physical confirmation or an explicit schedule revision before proceeding. Exact prefill parameters, shroud and exhaust details remain unknown.

Generated YESTERDAY_RESULTS.md and results/yesterday-analysis.json solely from the three original 2026-11-06 CSV/JSON captures. Includes mean/min/max/SD temperature, clocks, power, utilization, sampling/energy, group repeatability and all three run-pair deltas. Recomputed means match original JSON within 1e-8; raw source hashes retained. Original evidence unchanged. Initial report console printing encountered Windows cp1252 Unicode output failure after files were saved; changed to ASCII status printing and reran. No GPU query, workload change, monitor or benchmark needed for historical analysis. Today's setup declaration is not assigned retroactively to yesterday.

## Start authorization — both fans first

User requested commit/push before measurement and reports the existing prefill-only stress has run for 15 minutes and is heat soaked. Case open, intake plus exhaust installed. Revised order to B then A; supervisor enforces three both-fan captures first and then waits for user to remove exhaust and re-warm. Fan curve unchanged, reaching 100% at 75°C. Ambient, actual RPM, exhaust details, shroud and exact prefill invocation remain unknown; no equilibrium proof claimed. Only new campaign files and root index are included in this commit; unrelated quick-benches and previous campaign working-tree changes remain untouched. STOP hold to be released only after successful push and fresh live preflight. No workload/server/fan changes requested or performed.

Commit 99ebee5 pushed successfully to origin/main before starting. Six synthetic tests and repository privacy/layout validation passed. Fresh live preflight found P100-only loaded model/context, no competing monitor/queue, no campaign capture lock or prior evidence. Historical locks in completed campaigns left untouched. P100 snapshot: 66°C, 100% utilization, 1328 MHz, power limit 250 W.

Released STOP and launched both-fan three-run passive supervisor; historical identifiers: supervisor PID 13740, first monitor PID 11504. First capture 20261107T115851.337003Z-intake-exhaust-1 is confirmed running and CSV growing. Verify live commands before any action on saved PIDs. Receipt: state/launch.json; log: state/capture-supervisor.log; progress: state/queue-state.json. Supervisor stops after these three captures and waits for intake-only setup; it does not stop the user-managed workload/server. No automatic fan change or second-group launch.

## Intake-only authorization and launch

User confirms exhaust removed, intake only, and reports plenty heat soaked; elapsed warm-up time unspecified. Verified all three both-fan captures complete (600 seconds each), state awaiting-intake-setup, no campaign lock/STOP or competing live measurement queue, and unchanged inference fingerprint. P100 preflight: 70°C, 100% utilization, 1316 MHz, 250 W limit. Added explicit --heat-soaked declaration with nullable duration rather than inventing a warm-up time. Six synthetic tests passed before launch.

Started three sequential 600-second intake-only captures, preserving all both-fan results. Historical supervisor PID 1868, first monitor PID 3736; verify live ownership before action. Raw first capture: results/20261107T125314.991061Z-intake-1.json/csv, confirmed running and writing samples. Launch/preflight: state/intake-launch.json, state/intake-start-preflight.json; log: state/intake-supervisor.log. User-managed Strata/prefill workload, fan controls and network unchanged. Report regenerates per completed capture; queue completes after all six without stopping user workload.

Review caveat: both-fan run 3 mean temperature rose to 70.12°C (max 77°C), versus ~66°C means/max 67°C in runs 1–2. Preserve all evidence; timing/cause of that drift relative to physical changes is not established. Do not silently exclude run 3 or attribute the full group difference solely to exhaust. Exact workload, ambient and fan RPM remain unrecorded.

## Final report and historical comparison

All six new captures completed successfully (600 seconds each); final intake capture ended 2026-11-07T13:23:18Z. State is complete, capture lock absent, and live process inspection found no monitor/capture/reference processes. No processes stopped; existing user-managed server/workload untouched.

Produced COMPARISON.md and results/comparison-analysis.json from 11 selected original CSV/JSON pairs: six new runs, three November 6 rear-pull captures and the two selected November 3 open-case one-fan runs. Recomputed all means against original summaries within 1e-6 and retained original source SHA-256 hashes; raw evidence unchanged. The remembered ~170 W reference is 171.78 W, but historical fan orientation was not documented, so it is labeled old one fan rather than definitively without a pulling fan.

New intake + exhaust mean: 67.39°C, 1322.92 MHz, 194.76 W; intake-only: 73.49°C, 1319.94 MHz, 196.95 W. Difference: −6.10°C, +2.98 MHz (+0.23%), −2.19 W (−1.11%). Both groups peaked at 77°C and 1328 MHz. November 6: 76.38°C / 1318.21 MHz / 197.54 W; old one fan: 78.92°C / 1231.20 MHz / 171.78 W. Historical deltas descriptive only. Third both-fan run's temperature drift remains explicitly included and flagged; no quality, inference-speed, efficiency or significance claim. Final report, manifest and root index now mark completion.
