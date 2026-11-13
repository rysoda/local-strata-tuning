# Two P100 deployment with existing settings — work log and checkpoint

## Current checkpoint

- 2026-11-13: complete, 3/3 requested diagnostic screens via `scripts/quick.py`; supervisor PID 9644 is historical. Existing user server was not managed or stopped by this runner.
- Exact state and per-run ownership: `state/queue-state.json`; supervisor output `state/quick-supervisor.log`.
- `state/STOP` pauses between runs. Completed queue exits without repeating work; failed or running state refuses restart and requires review. Do not clear state to retry.
- All runs complete: decode 31.827 / 33.091 / 31.085; prefill 345.244 / 344.676 / 343.908 tok/s. Mean medians 32.001 / 344.609. All 15 decode and 24 prefill measured samples valid. Report and README written; repository validation passed.
- Safe resume only from planned/paused with no other benchmark and verified idle server: `python campaigns/2026-11-12-dual-p100-deployment/scripts/quick.py`.

## Run/recovery log

### 2026-11-13 — user-requested startup recovery

- Confirmed no server/listener before manual launch. Existing startup settings select GPUs 0,1, 256K, split 36, reserves 640/896 MiB.
- Manual `--no-tui` start failed: stale managed-runtime child PID 3692 was reported present. Current PID 3692 was Windows `spoolsv.exe`, created after this boot; recorded host PID 1832 absent. No listener on old runtime port 55595 or API port 8080. No unrelated process stopped.
- Archived the three stale runtime state/child/ready files under ignored `configs/private/stale-runtime-20261113/`, then retried via `state/manual-start-20261113.cmd` (same startup arguments, no TUI). Launcher output: `state/manual-start-20261113.log`.
- Server reached HTTP 200 at `http://127.0.0.1:8080/health`; both P100s hold model memory (15456/15105 MiB sampled during loading). Left server running at user request. Startup batch unchanged. No benchmark or tuning performed. Original scaffold status above is historical, not current deployment status.

Append dated decisions, unique run IDs, process ownership, errors, preserved interrupted artifacts and exact recovery steps. Never treat historical PIDs as still owned without checking command lines. On completion record final report/profile, quality checks and confirmation that owned servers/benchmarks have stopped.
