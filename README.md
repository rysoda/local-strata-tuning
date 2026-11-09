# Local Strata benchmark campaigns

Hardware-specific tuning of **Qwen3.8-Flash-Next IQ3_S**, using the existing Windows Strata installation and BetterBench. Current context is **256K (262144)**; older campaigns used 128K. Each campaign keeps its own reports, configurations, raw evidence and resumable state.

## Current setup at a glance

| Item | Current recommendation / result |
|---|---|
| Hardware / engine | P100 CPU PCIe x16 + 1080 Ti chipset x4; Strata 0.1.57 |
| Model / quality settings | IQ3_S, 256K context, full experts, int8 KV; existing MTP/reasoning retained |
| Placement | P100 layers 0–35; 1080 Ti layers 36–47/Main; trimmed stage weights |
| **VRAM reserves: before → after** | **P100 1400 → 640 MiB; 1080 Ti 2304 → 896 MiB** |
| **Decode: before → after** | **37.49 → 38.86 tok/s (+3.65%)** |
| **Prefill: before → after** | **325.98 → 331.35 tok/s (+1.65%)** |
| Validation | Three alternating candidate/reference confirmations; candidate passed both scheduled 7/7 smoke sets, including ~230K-token recall |
| Startup | Updated to 640/896 MiB; existing experimental projection retained |
| Read more | [Recommendation and before/after table](campaigns/2026-11-08-p100-1080ti-reserve-performance/README.md) · [Full report](campaigns/2026-11-08-p100-1080ti-reserve-performance/REPORT.md) · [Startup deployment](campaigns/2026-11-08-p100-1080ti-reserve-performance/STARTUP_UPDATE.md) |

Speed figures are means of three per-run medians on the same workload **without projection**. Modest gains are not statistically proven; Startup's retained projection was not validated by this comparison. Older topology/software results below are historical, not directly comparable.

## P100 cooling quick summary

All selected runs are 10 minutes. Temperature and SM clock show **mean / sampled maximum**; power is **mean GPU board power**, excluding fan power.

| Setup | Date | Runs | Temperature °C | SM clock MHz | Mean power W |
|---|---|---:|---:|---:|---:|
| **New server intake + exhaust** | Nov 7 | 3 | **67.39 / 77** | **1322.92 / 1328** | **194.76** |
| New server intake only | Nov 7 | 3 | 73.49 / 77 | 1319.94 / 1328 | 196.95 |
| Previous rear-pull setup | Nov 6 | 3 | 76.38 / 77 | 1318.21 / 1328 | 197.54 |
| Older open-case one-fan setup | Nov 3 | 2 | 78.92 / 80 | 1231.20 / 1328 | 171.78 |

**New exhaust comparison:** mean temperature **−6.10°C**, mean clock **+0.23%** versus intake alone. Both groups reached 77°C. The third both-fan run drifted warmer; historical rows have unmatched conditions and old fan orientation is undocumented. These are cooling measurements, not inference-speed gains.

[Full comparison, run-by-run tables and caveats](campaigns/2026-11-07-p100-server-fan-intake-exhaust/COMPARISON.md)

## Campaign index

| Campaign | Hardware / links | Engine / Control | Status | Decode (tok/s) | Prefill (tok/s) | Main finding |
|---|---|---|---|---:|---:|---|
| [1080 Ti parameter tuning](campaigns/2026-10-28-1080ti-tuning/) | GTX 1080 Ti; original single-card topology | 0.1.52 / 0.1.51 | Complete: 54 benchmarks | 31.25–31.27 | 426.38–428.51 | About +3.2% decode against the full-expert reference; prefill essentially unchanged |
| [P100 + 1080 Ti x16/x4](campaigns/2026-11-01-p100-1080ti-x16-x4/) | P100 x16; 1080 Ti x4 | 0.1.55 / 0.1.55 | Historical: 6 benchmarks | 35.08–35.93 | 283.96–287.42 | Dual-card screening; superseded by the new topology |
| **[P100 + 1080 Ti x8/x8](campaigns/2026-11-02-p100-1080ti-x8-x8/)** | Both CPU-connected PCIe 3 x8 | 0.1.55 / 0.1.55 | **Complete: 16 benchmarks, 2 rejected configurations** | **37.30–40.62** | **317.70–319.54** | **Validated for the tested x8/x8 slots: explicit 32/16 split, trim, later reserve 1600 MiB** |
| [Cooled x16/x4 128K attempt](campaigns/2026-11-07-p100-x16-1080ti-chipset-x4-retune/) | P100 CPU x16; 1080 Ti chipset x4 | 0.1.57 / 0.1.57 | Superseded; first run intentionally interrupted | — | — | User requested 256K; partial 128K evidence preserved, excluded from new results |
| **[Cooled P100 x16 + 1080 Ti chipset x4 — 256K](campaigns/2026-11-07-p100-x16-1080ti-chipset-x4-256k/)** | **Current slots; cards stay put** | 0.1.57 / 0.1.57 | **Complete: 17 benchmarks** | 35.32–37.47 | 325.60–326.31 | Nearby confirmations and 256K recall smoke complete; see report for memory/quality limits |
| **[Minimum VRAM reserve — 256K](campaigns/2026-11-07-p100-x16-1080ti-x4-reserve-floor/)** | P100 CPU x16 / 1080 Ti chipset x4; fixed 36/12 split | 0.1.57 / 0.1.57 | **Complete: validated reserve floor** | 39.21–41.17 | 251.27–267.46 | P100 0 / 1080 Ti 0 MiB explicit reserve; see report for boundary/compatibility limits; Startup unchanged |
| [Reserve performance around 512 MiB](campaigns/2026-11-08-p100-1080ti-reserve-performance/) | P100 CPU x16 / 1080 Ti chipset x4; fixed 36/12 | 0.1.57 / 0.1.57 | **Complete** | 38.86 | 331.35 | Selected 640/896 MiB; Startup updated afterward by user request; see report for reference and projection caveats |

Speeds are ranges of per-run medians from final confirmation runs, not discovery maxima. The historical x16/x4 row covers the two repeated Main-card orders, not one selected configuration. Prefill uses the shared BetterBench 16K-target workload (roughly 12K actual model tokens).

**Historical inference recommendation (tested x8/x8 topology only):** [x8/x8 final report](campaigns/2026-11-02-p100-1080ti-x8-x8/REPORT.md). Final confirmations measured **37.30–40.62 decode / 317.70–319.54 prefill tok/s**. Quick screening is not a significance claim or comprehensive quality proof. Do not rank campaigns by raw speed across changed hardware/software; read their reference and quality caveats.

**Current topology retuning:** [new **256K** campaign and initial test plan](campaigns/2026-11-07-p100-x16-1080ti-chipset-x4-256k/README.md). Actual links verified x16/x4 after cooling changes; active installed software is now 0.1.57. **Complete: 17 benchmarks**. The selected 36/12 trimmed split averaged **36.40 decode / 325.96 prefill tok/s**, versus nearby P100-only **33.27 / 333.98**. Candidate/reference each passed **7/7** smokes including **230146 prompt tokens**. See the report for decode variability and headroom limits; the old x8/x8 results are not a same-condition reference. Installed profile snapshots are preserved; new tests use the explicitly requested **262144 context**, full experts and int8 KV, and exclude the as-found speed-projection vector. The interrupted 128K attempt is kept separate.

## Cooling measurements (separate from inference tuning)

- [Five-setup P100 fan comparison](campaigns/2026-11-09-p100-new-fan/README.md): **Complete**, including ARCTIC P12 Pro at 70% / ~2230 RPM + extractor, S12038-4K auto with/without extractor, and P9 PWM PST with/without extractor. Simple summary and all 14 runs: mean/max temperature and core clock, plus board power. [P12 detailed survey](campaigns/2026-11-09-p100-new-fan/REPORT.md).

- [P100 120×38 mm server intake + exhaust comparison](campaigns/2026-11-07-p100-server-fan-intake-exhaust/README.md): **Complete, 6/6 captures**. Intake + exhaust averaged **67.39°C / 1322.92 MHz / 194.76 W**, versus intake-only **73.49°C / 1319.94 MHz / 196.95 W**. Nominal 4000 RPM intake curve reaches 100% at 75°C. [Final report and historical comparisons](campaigns/2026-11-07-p100-server-fan-intake-exhaust/COMPARISON.md) include the ~172 W old one-fan reference and a third-run drift caveat.

- [P100 rear pull fan](campaigns/2026-11-06-p100-rear-exhaust-cooling/README.md): new user-requested setup; P100-only Strata at **131072 context**. Three 10-minute reference captures completed: **197.54 W** mean board power; no controlled comparison yet.

- [P100 closed-case shroud cooling](campaigns/2026-11-03-p100-closed-case-shroud-cooling/README.md): **11 completed runs** with a closed case and fan shroud, varying the auxiliary outside-air intake fan at the shroud edge. **Auxiliary fan off provisionally preferred:** balanced two-run reference **162.81 W / 1200 MHz**, versus **149.14 W / 1160 MHz** at 100%, all near **79°C**. Includes 25%, 50%, 75% and suspected warm-up evidence.
- [P100 open case cooling](campaigns/2026-11-03-p100-open-case-cooling/README.md): four selected completed open-case, unducted runs favor **one fan provisionally**: **171.78 W / 1231 MHz** versus **152.13 W / 1167 MHz** with two fans, both near **79°C**. Two repeats per setup.

These are separate physical comparisons and cooling evidence, not measured inference-speed gains. Do not pool their results.

## Run the previous x8/x8 recommendation

Double-click **[launchers/Run-P100-1080Ti-X8.cmd](launchers/Run-P100-1080Ti-X8.cmd)** on the tested machine, or validate without inference:

```sh
python tools/launch.py 2026-11-02-p100-1080ti-x8-x8 --check
```

**Startup context is now 256K (262144)** by user request, via a launcher-only runtime override. Archived profiles and original campaign measurements remain at 128K. [Two quick tests](campaigns/2026-11-02-p100-1080ti-x8-x8/QUICK_CONTEXT_CHECK.md) showed about −1.1% decode and unchanged prefill on the same short workload; full 256K context performance/quality is not validated. The direct `tools/launch.py ... --check` command above checks the archived profile; add `--context 262144` to check or launch the new runtime setting.

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

Completed campaigns remain closed; their supervisors exit without starting new tests. The cooled x16/x4 256K campaign is complete; its runner refuses to repeat completed work. Adding a second P100 is a reason for another campaign, not for deleting old state.
