# Local Strata benchmark campaigns

Hardware-specific tuning of **Qwen3.8-Flash-Next IQ3_S at 131072 context**, using the existing Windows Strata installation and BetterBench. Each campaign keeps its own reports, configurations, raw evidence and resumable state.

## Campaign index

| Campaign | Hardware / links | Engine / Control | Status | Main finding |
|---|---|---|---|---|
| [1080 Ti parameter tuning](campaigns/2026-10-28-1080ti-tuning/) | GTX 1080 Ti; original single-card topology | 0.1.52 / 0.1.51 | Complete: 54 benchmarks | About +3.2% decode against the full-expert reference; prefill essentially unchanged |
| [P100 + 1080 Ti x16/x4](campaigns/2026-11-01-p100-1080ti-x16-x4/) | P100 x16; 1080 Ti x4 | 0.1.55 / 0.1.55 | Historical: 6 benchmarks | Dual-card screening; superseded by the new topology |
| **[P100 + 1080 Ti x8/x8](campaigns/2026-11-02-p100-1080ti-x8-x8/)** | Both CPU-connected PCIe 3 x8 | 0.1.55 / 0.1.55 | **Complete: 16 benchmarks, 2 rejected configurations** | **Recommended for current hardware: explicit 32/16 split, trim, later reserve 1600 MiB** |

**Current recommendation:** [x8/x8 final report](campaigns/2026-11-02-p100-1080ti-x8-x8/REPORT.md). Final confirmations measured **37.30–40.62 decode / 317.70–319.54 prefill tok/s**. Quick screening is not a significance claim or comprehensive quality proof. Do not rank campaigns by raw speed across changed hardware/software; read their reference and quality caveats.

## Run the current recommendation

Double-click **[launchers/Run-P100-1080Ti-X8.cmd](launchers/Run-P100-1080Ti-X8.cmd)** on the tested machine, or validate without inference:

```sh
python tools/launch.py 2026-11-02-p100-1080ti-x8-x8 --check
```

The launcher prefers the campaign's ignored `configs/private/` profile, falling back to its redacted `configs/shareable/` copy. Credentials resolve from `STRATA_API_KEY` or the installed 128K profile if necessary. Machine paths must be adapted on other systems. Runtime files and engine logs stay within the campaign; the installed profile is not overwritten. Port 8080 must be free.

The [original single-card launcher](launchers/Run-1080Ti.cmd) remains available for historical reproduction, **but its validated Control 0.1.51 is no longer installed locally**. It deliberately refuses to silently use a newer version.

## Layout

```text
campaigns/<date>-<hardware>-<purpose>/
  README.md, manifest.json      # Identity, conclusion, navigation and resume
  reports/plans/notes (*.md)    # Campaign-specific interpretation
  configs/shareable/            # Published, credential-redacted profiles
  configs/private/              # Ignored local credentials/runtime profiles
  results/                      # Original raw benchmark evidence
  state/                        # Queue checkpoints; ignored locks/pause flags
  scripts/                      # Experiment definitions and supervisors

tools/                          # Shared benchmark, sanity, launch and publishing tools
workloads/                      # Shared BetterBench workload definitions
launchers/                      # Convenient Windows entry points
templates/campaign/             # Starting point for future campaigns
research/strata-source/          # Unchanged pinned upstream source submodule
```

See [repository conventions and migration notes](docs/REPOSITORY_LAYOUT.md) and [tool usage](tools/README.md). Historical paths inside raw logs/JSON are preserved; executable paths and documentation navigation use the new layout.

## Add another campaign

```sh
python tools/new_campaign.py 2026-11-10-example-hardware --title "Example hardware comparison"
```

This creates a **planned, non-executable** scaffold. Fill its hardware/software/model manifest, research plan and baseline before implementing a supervisor. Keep one engine/model/workload fixed per comparison, use unique run IDs, and preserve interrupted attempts. Instructions: [campaign template](templates/campaign/README.md).

## Validate and publish

```sh
python tools/validate_repository.py
python tools/publish_configs.py                 # All campaigns, or --campaign ID
```

Private profiles, runtime credentials, locks, pause files and Python caches are excluded from Git. Raw benchmark logs retain original machine paths and hardware details. Never force-add private files.

Clone research source too:

```sh
git clone --recurse-submodules git@github.com:rysoda/local-strata-tuning.git
```

All existing campaigns are completed; their supervisors exit without starting new tests. Adding a card is a reason for a new campaign, not for deleting old state.
