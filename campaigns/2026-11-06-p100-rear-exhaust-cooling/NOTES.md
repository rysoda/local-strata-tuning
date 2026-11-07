# Rear pull fan — work log

## 2026-11-06 launch

User added a fan pulling air behind the P100 and requested P100-only Strata with 128K context. No stress workload requested to be launched yet. Case/shroud state, RPM and ambient unconfirmed.

Preflight: no Strata/Python workload processes or listener on 8080 found; GPU 0 P100 TCC idle at 41°C, 26 W / 250 W, 9 MiB, 0% utilization. GPU 1 1080 Ti remains the display card. NVIDIA driver 582.66. Historical lock files exist in completed campaigns, but no associated live workload was found; none removed. Unrelated untracked `quick-benches/` left untouched.

Used archived redacted x8-p100-only profile, supplied credential privately via shared resolver, kept engine/Control 0.1.55 and all inference settings. Runtime-only log location, localhost binding and presets-disabled launch. Installed source confirms explicit CUDA GPU selection. New launcher refuses non-planned state, detected workload processes or occupied port; no resume queue exists.

Owned Control server launched as PID 13944 (historical identifier; verify live command line before action). Command and launch timestamp in state/queue-state.json. Startup engine log confirms Tesla P100, max-context 131072, int8 KV, 32768 resident cells. CPU vision helper emits a CUDA-unavailable warning because GPU use for vision is disabled; main engine detects P100 normally.

Server is intentionally left running for the user.

## Three-run reference capture

All three captures completed successfully, each 600 seconds: 197.9455 W, 196.4932 W, 198.1777 W; equal-duration mean 197.5388 W. Reference supervisor phase is complete. Raw evidence retained; no comparative inference-speed or cooling-improvement claim. Server/workload intentionally left available for the user.

At user request, started three sequential 600-second passive captures at approximately 1-second intervals, using the existing monitor unchanged. User reports about five minutes of stress warm-up and considers heat soaked; equilibrium is not independently established. Pre-capture P100 telemetry: 235.66 W / 250 W, 75°C, 100% utilization, 1316 MHz. No other Python monitor was present. No workload, fan, clock or power settings changed.

Supervisor started PID 6756; first monitor PID 2292, first raw CSV/JSON timestamp 20261106T172551.928683Z. Verify live commands before acting on these historical identifiers. Progress: state/reference-state.json; output: state/reference-supervisor.log; evidence: results/*-rear-pull-reference-[1-3].csv/json. Exclusive lock, checkpoints before/after each run, pause on errors, and state/STOP honored between runs. Completed references are not rerun; incomplete attempts require review. Stress workload remains user-managed and is not stopped on completion.

Network correction before measurements: user requested normal network access; verified usual installed API key already matched, stopped only the verified owned server tree and restarted on 0.0.0.0:8080. Both localhost and 172.27.73.6 health checks returned loaded=true, context 131072. New server PID 14848. One immediate relaunch preflight refused while the terminated old engine was still disappearing; retried after confirming termination. Original logs and launch state retained. No heat test, telemetry capture, benchmark or generated-code execution started. Before any restart, inspect actual processes, command lines, port and logs; preserve this attempt and explicitly review state. Do not restart completed historical supervisors.

## 2026-11-07 user-requested server restart

Verified no running Python/Strata processes and no port 8080 listener; P100 idle at 9 MiB. Started only the archived P100 configuration at 131072 context with the usual API credential and 0.0.0.0:8080 binding. Preserved previous launch state; no supervisor, stress workload or measurement restarted. Control PID 5624 and engine PID 4676 are historical identifiers requiring live verification before action. Localhost and 172.27.73.6 health checks returned loaded=true, max_context=131072. NVIDIA process telemetry confirms Strata only on P100. New timestamped logs: results/20261107T114323Z-p100*.log. Installed profiles unchanged.

At the user's later stop request, verified the live server command/config and stopped only its owned tree. Engine and vision processes exited; localhost and LAN-address port 8080 were no longer reachable. State records server-stopped at 2026-11-07T14:26:05Z. Historical cooling captures and completed reference supervisor remain unchanged.
