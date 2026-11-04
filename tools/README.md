# Shared tools

[Campaign index](../README.md) · [Repository conventions](../docs/REPOSITORY_LAYOUT.md)

Run commands from the repository root. Campaign supervisors and launchers also resolve paths from their own files, not the current working directory.

## Launch a recommendation

```sh
python tools/launch.py 2026-11-02-p100-1080ti-x8-x8 --check
python tools/launch.py 2026-11-02-p100-1080ti-x8-x8
```

Optional `--context 262144` overrides only the runtime `--max-context`, including during `--check`; saved source profiles are untouched. The current x8/x8 Windows launcher supplies this override by user request (see [quick-check limitations](../campaigns/2026-11-02-p100-1080ti-x8-x8/QUICK_CONTEXT_CHECK.md)).

`--check` resolves profile, credentials and configured installation without writing a runtime config, opening a port or launching anything. Actual launch writes only the campaign's ignored `configs/private/recommended.runtime.json`, logs to its `results/`, disables presets, binds localhost:8080 and refuses an occupied port. Private source profile first; otherwise published redacted profile plus `STRATA_API_KEY` or existing installed credential. It never silently upgrades engine/Control. The historical 1080 Ti Control 0.1.51 is no longer installed locally, so its launch check currently fails clearly.

Convenient Windows entry points are in [launchers/](../launchers/).

## Publish profiles

```sh
python tools/publish_configs.py
python tools/publish_configs.py --campaign 2026-11-02-p100-1080ti-x8-x8
```

Redacts credential fields from `campaigns/*/configs/private/*.json` into each campaign's `configs/shareable/`. Runtime profiles are excluded. Private originals are not changed. Published configs retain machine-specific paths and all scientific settings.

## Create future work

```sh
python tools/new_campaign.py 2026-11-10-example-hardware --title "Example hardware comparison"
```

Creates manifest/README/plan/notes, an initial planned checkpoint and campaign subdirectories from [templates/campaign/](../templates/campaign/). Refuses an existing destination or unsafe ID. It does **not** copy old completed state, select software automatically, create an executable supervisor, add a root index row or start inference. Fill the manifest/plan and update the root index deliberately.

## Validate without inference

```sh
python tools/validate_repository.py
python tools/validate_repository.py --local
python -m unittest discover -s tools/tests -v
```

Validation checks campaign manifests/counts/final phases, local Markdown links, redacted configs, known local credentials, and SHA-256 preservation of **648 original artifacts/checkpoints** recorded during migration. Historical paths inside raw evidence remain intact. `--local` additionally resolves the current installed recommendation without launching. Unit tests block process/network calls while exercising completed supervisors; they also test profile fallback, redaction, result parsing and new-campaign scaffolding.

## Benchmark internals

- `benchmark.py`: shared profile editing, server readiness, exact BetterBench invocation, metrics extraction, telemetry, sanity invocation and cleanup. Call `configure(campaign_path, control_path)` and install a campaign-specific `checkpoint` callback before `run_one`. Campaigns choose their base-profile loader and run definitions. These legacy Windows mechanics use module-level configuration and are intended for **one campaign per Python process**, not concurrent threads/campaigns.
- `gpu_topology.py`: shared GPU-order/layer-split profile construction. Existing GPU campaigns inherit the original single-card recommendation but pin their own tested engine/Control 0.1.55. This is historical inheritance, not automatic discovery of settings for future cards.
- `sanity.py CONFIG OUTPUT`: functional/tool/32K/119K recall smoke checks against an already-running owned server, using that profile's Control tokenizer. Not a speed benchmark or comprehensive quality proof; generated code is not executed.

Campaign `scripts/` own the candidate list, interpretation, checkpoint paths, pause flags and completion policy. Never run two benchmark campaigns concurrently; inspect active processes/ownership, locks and port 8080 first. Failed/interrupted runs require review, not silent retries. Baseline setup scripts refuse to rerun the completed original campaign.

The migration preservation manifest is a one-time archive check, not a requirement that future campaigns remain frozen. Future experiment artifacts should use new run IDs/campaign paths; do not overwrite the archived evidence.
