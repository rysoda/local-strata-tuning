# Project: local Strata performance tuning

## Start here

- Read root `README.md` for the campaign index and current recommendation.
- Work inside a named `campaigns/<date>-<hardware>-<purpose>/`. Read its `README.md`, `manifest.json`, report, work log and `state/` **before** starting anything.
- All three existing campaigns are complete. Do not restart them or clear state to test new hardware. Current recommendation: `campaigns/2026-11-02-p100-1080ti-x8-x8/REPORT.md`.
- Repository conventions: `docs/REPOSITORY_LAYOUT.md`; shared tools: `tools/README.md`; new work: `templates/campaign/` and `tools/new_campaign.py`.

## Scope and quality invariants

Tune the already installed [Strata](https://github.com/Niko1221/Strata/releases) for the actual hardware. Unless explicitly requested otherwise, retain **qwen3.8-flash-next-iq3_s**, **131072 context**, target weights, existing reasoning behavior, full expert routing and int8 KV. Decode matters slightly more than prefill for agentic work.

- No target precision reduction, expert pruning/skipping, routing approximations, reduced reasoning/context or speed projections as optimizations.
- Preserve original installed profiles. Test isolated copies with localhost API binding and presets disabled.
- Research plausible settings in source/docs/community benchmarks before testing; do not brute-force unrelated parameters. Check the installed engine's help and startup logs rather than assuming current online docs match it.
- Keep software/model/workload fixed within a comparison. New cards, topology, engine or model versions normally require a new campaign and fresh baseline. Do not upgrade the installation mid-comparison.
- Existing source submodule `research/strata-source` is pinned to original engine 0.1.52's commit and is reference material, not proof of newer engine behavior.

## Measurement procedure

Use BetterBench with the exact requested workload:

```text
--quick --decode --categories code --prefill --no-concurrency --config <repo>/workloads/betterbench-16k.json
```

The config is `{"prefill_depths":[16384]}`. This is a corpus target, not necessarily exactly 16384 model tokens. Retain actual token counts and all samples/errors. Quick mode is screening, not statistical significance or comprehensive quality proof.

1. Capture hardware/software/topology and original baseline first.
2. If original routing approximations are enabled, keep that baseline distinct and create a full-expert quality reference for speed comparisons.
3. Write a reasoned parameter plan. Test individual settings, checkpoint every run and mark provisional gains.
4. Combine worthwhile settings, review interactions and memory headroom, then confirm around a nearby same-quality reference.
5. Run functional/tool/long-context smoke checks before recommending. Never execute generated code. Do not present smoke checks as comprehensive intelligence equivalence.
6. Offer a separate ready profile/launcher, report limitations, stop owned test processes and mark completion durably.

## Data, privacy and restart safety

- Campaign `configs/private/` contains existing credentials and runtime profiles; **never publish or force-add it**. Use `python tools/publish_configs.py` to refresh redacted copies under `configs/shareable/`.
- Save original artifacts to campaign `results/`; queue state, logs and pause flags belong to `state/`. Preserve failed/interrupted attempts and note recovery decisions. Raw logs/JSON can contain historical paths: do not rewrite that evidence for navigation cleanup.
- Check actual processes, command lines, locks and port 8080 before resuming. Historical PIDs are not proof of ownership. Never kill unrelated processes or launch competing benchmark queues.
- Supervisors must refuse ambiguous incomplete runs, pause on errors and skip completed work. Checkpoint before and after every run; pause flags take effect between runs.
- `tools/benchmark.py`, `tools/gpu_topology.py` and `tools/sanity.py` are shared mechanics; campaign scripts own experiment definitions and reporting.
- Validate layout/privacy with `python tools/validate_repository.py`; validate an installed recommendation without launching with `python tools/launch.py CAMPAIGN --check`.

## Current completed checkpoint

- x8/x8 campaign: 16 complete benchmarks, two reviewed failures. P100 GPU 0 layers 0–31; 1080 Ti GPU 1 layers 32–47/Main; explicit split 32, trim stage weights, later reserve 1600 MiB. Full details in campaign report/notes/state. Candidate and P100 reference each passed 6/6 checks including 119151 actual prompt tokens.
- Original 1080 Ti campaign: 54 complete benchmarks, one rejected startup; approximation caveat is essential. Its Control 0.1.51 installation is no longer present locally; do not silently substitute 0.1.52 or 0.1.55 for reproduction.
- Historical x16/x4 campaign: six complete screens, superseded by x8/x8. No standalone deployment recommendation.
- Older agent checkpoints are preserved in the original campaign's `AGENT_HISTORY.md`; those paths and process IDs are historical, not current instructions.
