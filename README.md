# Local Strata tuning

Reproducible tuning records for Qwen3.8-Flash-Next IQ3_S at 131072 context on a GTX 1080 Ti, i5-11400F and 64 GB RAM, using the existing Windows Strata installation.

**Start with [FINAL_REPORT.md](FINAL_REPORT.md).** It contains the recommendation, final confirmation results, quality caveats and limitations. The 54 successful benchmark runs are quick screening measurements, not formal significance or comprehensive quality-equivalence claims.

## P100 + 1080 Ti follow-up (PCIe x8/x8)

See **[GPU_X8_REPORT.md](GPU_X8_REPORT.md)** for the new engine/control 0.1.55 comparison: 16 complete benchmarks and two rejected configurations. Recommended: P100 layers 0–31, 1080 Ti layers 32–47/Main, stage-weight trimming and 1600 MiB later-card reserve. Original single-card results are historical, not directly comparable.

On the tested machine use **`Run-Tuned-X8.cmd`** with private `configs/recommended-x8.json`. A redacted copy is published under `configs/shareable/`; restore credentials and adapt paths before use elsewhere. This separate launcher does not overwrite the original recommendation. Results: [GPU_X8_RESULTS.md](GPU_X8_RESULTS.md); recovery/checkpoints: [GPU_X8_NOTES.md](GPU_X8_NOTES.md). Both candidate and fresh P100 reference passed 6/6 functional/recall smoke checks; this is not comprehensive quality proof.

## Contents

- [RESULTS.md](RESULTS.md): all single-parameter and follow-up results, with final usage marks.
- [COMBINED_RESULTS.md](COMBINED_RESULTS.md): combined tests and confirmations.
- [TUNING_PLAN.md](TUNING_PLAN.md), [STAGE1_REVIEW.md](STAGE1_REVIEW.md): research, rationale and interpretation.
- `results/`: raw JSON, HTML reports, logs, telemetry and sanity checks.
- `configs/shareable/`: redacted copies of **every** run configuration. Target weights are not included.
- `scripts/`: resumable runners, sanity checks and publication helpers.
- `research/strata-source/`: upstream Strata source as a submodule pinned to the tested engine's source commit, not a modified engine.

## Clone

```sh
git clone --recurse-submodules git@github.com:rysoda/local-strata-tuning.git
```

Or initialize the research checkout later with `git submodule update --init`.

## Run the recommendation

On the original Windows machine, double-click `Run-Tuned.cmd`. It uses the existing installed binaries; it does not upgrade or overwrite the installed profile. Stop other servers using port 8080 first.

The launcher prefers the private `configs/recommended.json`, when present. From a fresh clone it uses `configs/shareable/recommended.json` and resolves the API key from `STRATA_API_KEY` or the existing installed 128K profile. It writes only an ignored runtime configuration. Machine-specific paths in the configuration must be adapted before using it on another machine.

The speed settings are `--pool-tasks 36 --adapt-every 1` and `STRATA_PCIE_BALANCE=1`. Approximate routing is disabled. **The approximately +3.2% decode result is against a full-expert reference, not the faster original approximate baseline.** See the final report before interpreting the numbers.

## Credentials and local artifacts

Private originals in `configs/*.json`, runtime configurations, lock files and Python caches are excluded from Git. All scientific configuration settings are published in `configs/shareable/`; only credentials are redacted. Refresh those copies with:

```sh
python scripts/publish_configs.py
```

Reports retain the original machine paths and hardware details. Do not add private configuration files with `git add -f`. Benchmark queues are completed and their scripts exit without starting new tests when they see the final checkpoint.
