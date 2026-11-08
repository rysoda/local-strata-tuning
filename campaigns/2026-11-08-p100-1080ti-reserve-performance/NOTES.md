# Work log

## 2026-11-08 — autonomous performance follow-up authorized

User correctly distinguishes reserve minimization from optimizing throughput. Reviewed previous19-run campaign:512 screens retained prefill while0/0 lost20%. Previous campaign stays complete and unmodified. Created new performance campaign with fresh reference, two starts per card/value, joint neighborhood including512/512, independent top-two joint repeats, and three alternating final candidate/reference confirmations. Explicit262144 context from current campaigns retained. No projections. Up to46 runs, sequential; approximately8–10hours including four smoke sets.

Read root README, layout/tools instructions and prior README/manifest/report/plan/notes/state plus shared benchmark/sanity code. Search for reserve issue493 returned no result; reopened known issue directly and confirmed maintainer describes reserve/cache tradeoff. Copied frozen baseline/inventory and installed-commit source provenance without altering historical evidence. Fresh engine --help, nvidia-smi and private live-process snapshot captured. Frozen input hashes/model metadata and actual16/4 links/UUIDs verified. Preflight found no existing Strata/BetterBench/queue process and no port8080 listener; no process was stopped.

Supervisor reuses a campaign-local snapshot of prior reviewed measurement primitives. New search/ranking/report code and watchdog provide finite progression and hard phase limits even if logs continue growing. Unexpected failures stop with a durable report; expected allocation boundaries are preserved/reviewed, not retried. Existing installed presets/Startup untouched. Separate ready profile only after confirmation; no arbitrary free-VRAM rejection. Test-created configs are ignored/private, published with credential redaction.

Four offline tests passed: prefill gate, headroom tie, complete synthetic search/resume with unique IDs and run-count bound, and projection-free512/512 profile invariants. Default check launches no inference. Repository validation passed for11 campaigns and648 unchanged archive artifacts; redacted baseline published.

Launched detached sequential supervisor at2026-11-08T07:48:43Z; launch receipt in state/launch.json and log state/performance-supervisor.log. Historical supervisorPID10864, first serverPID13076, first BetterBenchPID13752. These numbers are not proof of current ownership. Actual first startup confirms engine0.1.57,262144/int8/resident32768, full36/12 split, MTP/spec4/min-p0.5, trim,1400/2304,7977 resident expert slots and no projection. First reference reached benchmark-running. CPU-only vision helper logs its expected CUDA-unavailable message, while both actual inference GPUs initialize normally. Queue proceeds through all screens, joint selection, confirmations, smoke checks and final report without another planned idle gate. PID ownership must be verified before any later action.

## First full transition verified

At09:15 local, fresh reference completed37.66 decode/326.87 prefill with all5/8 benchmark samples and7/7 smokes, including above128K recall. No thermal flags. Supervisor inspected/accepted it, cleaned up the reference server and automatically advanced toP100256/Ti2304; that next run reached benchmark-running. This verifies actual end-to-end benchmark, extended smoke, inspection, cleanup and automatic queue progression—not merely successful launch.

## Complete

Final pair (640, 896). Confirmation and all attempts in report/state. Owned processes stopped; Startup unchanged.
