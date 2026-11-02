# Repository layout and migration checkpoint

## Campaign contract

A campaign is one hardware topology + fixed engine/model/workload comparison. Start a new campaign when those comparison boundaries change. Parameter variations and confirmations are runs *inside* it, identified by unique IDs.

Each campaign owns:

- `README.md`: purpose, hardware/software, conclusion, navigation and safe resume command.
- `manifest.json`: machine-readable identity, software/model/workload, status and recommendation.
- Reports, plans and notes in the campaign directory.
- `configs/shareable/`: published credential-redacted profiles.
- `configs/private/`: ignored local credentials and runtime profiles.
- `results/`: original raw benchmark JSON/HTML, logs, telemetry, sanity checks and provenance. Historical paths inside raw evidence are intentionally retained.
- `state/`: durable queue state, supervisor metadata and ignored locks/pause flags. Historical PID numbers are never proof that a process is still owned.
- `scripts/`: campaign-specific run definitions and supervisors.

Repository-wide `tools/` owns common measurement, sanity, publication, launch and validation utilities. `workloads/` owns benchmark definitions. `launchers/` offers convenient Windows entry points. `research/strata-source` remains at its existing submodule path and pinned commit; it is not upgraded as part of layout changes. Campaign-specific research captures live with their campaign.

Private profiles must never be staged. Use the publication tool for redacted copies. Do not rewrite raw evidence to make historical paths look current. Runnable configs and scripts must use current paths, while reports should explain old paths when they occur in quoted original commands.

## Migration work log — 2026-11-02

- Starting from clean commit `6b1e002`.
- Approved: split original 1080 Ti tuning, historical P100/1080 x16/x4 comparison, and P100/1080 x8/x8 work into three campaigns.
- Preserve raw artifact contents, queue decisions, private credentials and pinned research submodule. No benchmark or inference server should be started for validation.
- **Migration complete.** Reports/configs/artifacts/state are grouped into three campaigns; shared mechanics extracted to `tools/`; root README is the campaign dashboard. Added per-campaign manifests/READMEs, planned-only scaffold/template, launcher/profile resolution and validation tests.
- Captured SHA-256 hashes **before relocation** for 648 original artifacts/checkpoints (excluding runtime locks). `migration-evidence-hashes.json` maps old to current paths and records both original working-copy hashes and authoritative source-commit byte hashes (`6b1e002`). All 648 committed artifacts are byte-identical to that source commit. For 644 files the original working copy had CRLF while Git stored LF: restored the original committed representation after verifying that line endings were the only difference. No measurement, log text or checkpoint value changed. Git attributes disable further line-ending conversion for campaign results/state so future checkouts preserve the exact committed evidence bytes.
- All 82 published scientific profiles compared to source commit `6b1e002`: settings unchanged after excluding only `log`, whose destination was rebased into its campaign. Private copies/credentials remain ignored; publication redacts them. Original installed profiles and the upstream source submodule were not changed.
- Validation passed: all manifests/counts/final phases, 648 evidence hashes, local Markdown links, known-credential scan, Python compilation and eight unit tests (including a mocked shared-runner lifecycle verifying campaign output paths, exact workload flags and shared sanity invocation). Completed supervisors (including baseline scripts) were exercised with process/network calls blocked. Current Windows launcher passed `--check` from a different working directory. A clean export of the staged Git tree, with no private profiles or working-copy extras, also passed validation and all eight tests. No benchmark/server was started.
- Historical Control 0.1.51 is absent locally (0.1.52 and 0.1.55 remain). The old single-card launcher now fails explicitly on that missing validated installation rather than silently substituting a version. Current x8/x8 installation resolves successfully.

## Old-to-new navigation

| Former root location | Current location |
|---|---|
| `FINAL_REPORT.md`, tuning/combined reports and manifests | `campaigns/2026-10-28-1080ti-tuning/` |
| `GPU_COMPARISON.md` | `campaigns/2026-11-01-p100-1080ti-x16-x4/RESULTS.md` |
| `GPU_X8_REPORT.md`, `GPU_X8_RESULTS.md`, `GPU_X8_NOTES.md` | x8/x8 campaign `REPORT.md`, `RESULTS.md`, `NOTES.md` |
| `configs/*.json`, `configs/shareable/*.json` | Owning campaign `configs/private/`, `configs/shareable/` |
| `results/<run>.*` | Owning campaign `results/<run>.*` |
| Queue states, supervisor metadata/logs | Owning campaign `state/` |
| `scripts/gpu_compare.py`, `scripts/gpu_x8.py` | Respective GPU campaign `scripts/run.py` |
| Original parameter/baseline/combined scripts | Original 1080 Ti campaign `scripts/` |
| `scripts/sanity.py`, publishing/launch helpers | Shared `tools/` |
| `Run-Tuned.cmd`, `Run-Tuned-X8.cmd` | `launchers/Run-1080Ti.cmd`, `launchers/Run-P100-1080Ti-X8.cmd` |
| `16k.json` | `workloads/betterbench-16k.json` |
| Root task-specific AGENTS checkpoints | Original campaign `AGENT_HISTORY.md` (root AGENTS is now general policy) |

Original logs/state/provenance retain old relative/absolute paths and historical PIDs. The manifest, campaign README and current scripts are authoritative for current navigation. The ignored original `.local/` deployment backups moved to the original campaign's `state/local-deployment/`; they are historical deployment evidence, not new launch instructions.

New campaigns are not frozen by the migration hash manifest. To intentionally extend a migrated campaign, first preserve its original checkpoint as an immutable archive and update only that entry's **destination path** in the preservation manifest (never its original SHA-256), then create new working state/run IDs. For changed hardware/software/topology, prefer a new campaign instead.
