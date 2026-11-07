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
