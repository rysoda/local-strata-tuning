# Work log

## Completed surveys and five-setup comparison

All three P12 captures completed (600 seconds each); final capture checkpoint is complete. At the subsequent reporting request the user clarified that the P12 measurements included the extractor, the previous server fan was ARCTIC S12038-4K auto targeting 75 C, and the older fan was ARCTIC P9 PWM PST. Mapped P9-alone to the selected Nov 3 old-one-fan runs (~172 W), and P9+extractor to the Nov 6 rear-pull runs (~198 W). These model/extractor labels are user-provided retrospective identification, not newly measured fan telemetry.

Created a simple five-setup summary and all-run table in README.md, with mean/max temperature/core clock and mean board power. scripts/comparison.py recomputes all 14 complete CSVs using the previous sample-and-hold metrics routine and checks saved means within 1e-6. Source hashes and derived statistics saved to results/five-fan-comparison.json. Original evidence and previous campaign reports unchanged. Retained historical/software/ambient/workload and third S12038+extractor run drift caveats. No new measurements or server/workload changes performed for reporting.

2026-11-09: User requested P100-only Strata at 128K with usual network/API access for a new fan. Before launch no Strata/Python inference processes or listener on 8080 were detected. P100 idle 46 C, 27 W. Saved initial nvidia-smi output.

Created an isolated copy of the current 0.1.57 recommendation; changed context to 131072, GPU to 0, removed multi-GPU split/trim/reserves to use the single-card automatic cache headroom. Full routing, int8 KV, MTP and CPU vision retained. Installed API credential preserved, 0.0.0.0 bind. No projection vector added. Presets disabled; original installed profiles unchanged.

Server PID at launch: 10460 (historical ownership hint only; verify live command line). Authenticated /v1/models returned loaded and n_ctx 131072. Engine log confirms Tesla P100 only, 746 MiB VRAM free after load. CPU vision's CUDA initialization warning is expected with its GPUs hidden; CPU vision loaded successfully. No requests generating text, stress workloads or monitors launched.

Server intentionally left running for user. State is serving; no automatic relaunch/recovery. No thermal/performance conclusions.

User subsequently confirmed ARCTIC P12 Pro fixed at 70%, approximately 2230 RPM, and card heat soaked. Authorized three consecutive 600-second surveys, 1-second sampling. Exact stress command, heat-soak duration, ambient and case/shroud remain unknown. Live process/health/config/compute-GPU checks confirmed the campaign's 0.1.57 P100-only 128K server and no competing monitor/queue. Preflight observed 73 C, 100% GPU, ~187–210 W and 1316–1328 MHz. Started detached supervisor PID 3940 (verify live command before recovery), checkpoint `state/capture-state.json`, log `state/capture-supervisor.log`. No workload or fan settings changed. Captures preserve throttle flags as well as prior cooling metrics; no controlled historical comparison implied. Supervisor checkpoints before/after each run, pauses on errors/STOP, refuses incomplete reruns, and leaves user-managed workload/server running.
