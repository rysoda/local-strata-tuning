# P100 open case cooling — work log

## Later closed-case evidence separated

- At the user's request, moved the 11 closed-case/shroud CSV/JSON pairs into [a separate campaign](../2026-11-03-p100-closed-case-shroud-cooling/README.md). Filenames and bytes are unchanged; the destination results directory contains the original/new path and SHA-256 inventory. No open-case measurements or planning state were changed. The closed-case auxiliary fan sits at the shroud edge and draws outside air inward; that configuration must not be pooled with the unducted comparison below.

## 2026-11-03

- Created a separate campaign; historical campaign state untouched.
- Added passive UUID-pinned NVIDIA monitor; no inference server, queue or workload started/stopped, and no settings changed.
- Local read-only probe identified P100 at NVIDIA index 0 and confirmed power/temperature/utilization/clock queries work. Existing workload was already active; no ownership assumed.
- Three-second validation run saved as `results/20261103T133424.801675Z-monitor-validation-not-airflow.*`. This is monitor validation ONLY, not an airflow baseline or cooling result.
- Phase remains planned for actual A/B/C measurements. User must capture fixed software/workload provenance, ambient temperature and physical configurations. No report or recommendation yet.
- Safe next command from repository root: `python campaigns/2026-11-03-p100-open-case-cooling/scripts/monitor_power.py --label airflow-A` after warm-up. No automatic queue; run one airflow measurement at a time. No owned processes remain.
- Failed/interrupted runs retain CSV and JSON status. Start a fresh unique run rather than appending or resuming an incomplete interval. No GPU settings are restored because none are modified.

## Review of latest four completed measurements

- User confirmed these are open-case runs without ducting, two with one fan and two with two fans. Selected completed runs starting 15:00:15, 15:11:23, 15:22:07 and 15:33:48 UTC on 2026-11-03; excluded the interrupted 39.25-second attempt at 15:33:03 and all earlier measurements.
- Recomputed all selected JSON summary metrics from their CSV samples; they agree within 1e-6. All selected runs lasted 600 seconds, used the same P100 UUID and reported a constant 250 W power limit. No raw artifacts changed.
- One fan averaged 171.78 W / 1231.2 MHz; two fans 152.13 W / 1167.0 MHz, both near 79°C. The power separation persists in the final five minutes. README now contains the evidence table, interpretation and provisional one-fan recommendation for this arrangement only.
- Fan geometry/RPM, ambient temperature, exact software/workload provenance and throttle reasons remain unrecorded. No throughput or significance claim. Manifest now marks measurements available and points to README; the original queue planning checkpoint remains unchanged because it is not a run inventory. No monitor/workload was started or stopped for this review.
