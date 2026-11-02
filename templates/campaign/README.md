# {{title}}

[Campaign index](../../README.md) · [Manifest](manifest.json) · [Plan](PLAN.md) · [Work log](NOTES.md)

**Status: planned.** ID: `{{id}}`. No experiments or inference server are started by creating this campaign.

## Before measuring

1. Fill hardware, GPU IDs/modes/link widths, CPU/RAM, OS/driver and exact installed engine/Control/BetterBench versions in `manifest.json`. Capture detailed provenance in `results/`.
2. Confirm model/quantization, 131072 context and full expert routing. Preserve an untouched baseline separately from any quality-restored reference.
3. Complete [PLAN.md](PLAN.md): research, plausible parameters, exclusions and confirmation policy.
4. Put credential-bearing copies in ignored `configs/private/`; publish with `python tools/publish_configs.py --campaign {{id}}`.
5. Implement campaign-specific supervisors under `scripts/`, reusing repository `tools/benchmark.py` and `tools/sanity.py` as appropriate. Set `resume_script` only after it safely handles completion, locking, owned processes and interruptions.
6. Add a row to the root campaign index. Do not compare raw speeds across engine/topology changes without a new reference.

## Storage and restart

- `results/`: immutable original benchmark evidence, actual token counts, errors and quality checks.
- `state/queue-state.json`: initial phase `planned`; checkpoint after each change/run.
- `state/STOP`: suggested between-run pause flag; not an emergency process kill.
- `configs/shareable/`: redacted profiles; `configs/private/`: ignored originals/runtime files.
- `scripts/`: experiment definitions and safe supervisor; **no supervisor exists yet**.

Record current status, unique run IDs, active process ownership and the exact safe restart command in [NOTES.md](NOTES.md). Failed runs pause for review. Preserve incomplete evidence before explicit recovery. Never restart completed historical campaigns to represent a new comparison.

## Finish

Write `REPORT.md` with selected settings, nearby-reference confirmations, quality/thermal caveats and a ready profile if justified. Stop owned test processes. Update manifest status/counts/report/recommendation, final state, root index and notes. Run `python tools/validate_repository.py` before committing. Quick BetterBench is screening, not a significance or comprehensive quality claim.
