# {{title}} — work log and checkpoint

## Current checkpoint

- Phase: planned; no benchmark server or supervisor started.
- Next: capture actual hardware/software and fill the manifest/plan.
- Safe resume command: none yet; implement and document a supervisor before measuring.
- Pause flag: planned `state/STOP`, honored between experiments once implemented.

## Run/recovery log

Append dated decisions, unique run IDs, process ownership, errors, preserved interrupted artifacts and exact recovery steps. Never treat historical PIDs as still owned without checking command lines. On completion record final report/profile, quality checks and confirmation that owned servers/benchmarks have stopped.
