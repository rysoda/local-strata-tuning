# Dual P100 decode tuning on installed engine 0.1.59 — work log and checkpoint

## Current checkpoint

- Phase: complete. Ten valid benchmarks, two reviewed exclusions; all original artifacts preserved. Queue cannot repeat completed work.
- Selected 24/24 + pipeline2 + last-card MTP (explicit STRATA_MTP_STAGE0=0), reserves640/896 unchanged, no projection. Candidate confirmations 44.660/47.632 decode and 347.259/347.571 prefill; nearby reference31.696/345.886.
- Reference and candidate each passed7/7 smoke checks including230146 actual API prompt tokens. Candidate B max76/71C, sampled minfree526/738MiB, no sampled thermal flags. Generated code not executed.
- All owned test processes stopped; original installed profile/Startup byte/equality checks passed at finalization. Separate ready launcher: `launchers/Run-Dual-P100-Tuned.cmd`; archived queue no longer resumable.
- All listed test PIDs are historical; check actual command lines and port8080 before any deployment. `tools/launch.py ... --check` validates without starting anything.

## Ready-profile deployment and final validation

After all test processes exited and port8080 was confirmed free, launched the separate ready profile using `python tools/launch.py 2026-11-13-dual-p100-decode-tuning`. It is now the user deployment, not a benchmark queue. Recorded launcher PID14620, server4588, engine15068 are historical identifiers only; inspect current command lines before stopping anything. Runtime config is ignored `configs/private/recommended.runtime.json`, localhost8080, log `state/deployment.server.log` and `results/recommended.engine.log`. HTTP health200; actual engine command confirms split24/pipeline2/no projection, context262144, engine0.1.59, idle. Deployment health/metrics saved in results/. Original installed profile and boot launcher remain unchanged; future logon will still use old36/12 projected settings unless separately updated.

Repository validation passed (16 campaigns,648 original artifacts/checkpoints), all12 shared unit tests passed, ready launcher `--check` passed. Completed runner exercised and exited without launching. Reviewed exclusion phase standardized to `invalid` for repository count validation; original samples unchanged. Unrelated existing cooling-log working-tree changes were not edited or reverted.

## Run/recovery log

### Override correction (2026-11-13)

The first reference36/split24 attempts completed sample counts but effective engine arguments retained projection and split36: Control merges `user_args` over `args` independently of STRATA_NO_PRESET. The placement check caught split24; review also invalidated reference36 as a projection-free reference. Both marked rejected with explicit notes; raw logs, samples and pre-recovery state preserved. Removed `user_args`, `args_written`, `args_derived`, `launch_set` from isolated baseline only, preserved old baseline/frozen manifest, re-froze revised baseline and added a pre-benchmark effective-command gate. New unique IDs reference36-v2 and split24-v2; no old artifact overwritten. Installed originals and boot launcher untouched. v2 startup confirms no control-vector flags. Supervisor PID 14020 at launch is historical; use live process checks before recovery.

Append dated decisions, unique run IDs, process ownership, errors, preserved interrupted artifacts and exact recovery steps. Never treat historical PIDs as still owned without checking command lines. On completion record final report/profile, quality checks and confirmation that owned servers/benchmarks have stopped.
