# P100 cooling with rear pull fan

[Campaign index](../../README.md) · [Manifest](manifest.json) · [Plan](PLAN.md) · [Work log](NOTES.md)

User requested a new cooling setup: added fan pulling air behind the P100. Case/shroud configuration, fan speed and ambient temperature have not yet been confirmed.

Start only Strata on P100 GPU 0, Qwen3.8-Flash-Next IQ3_S, **131072 context**, int8 KV and full expert routing. Engine/Control 0.1.55; isolated copy of the archived P100-only profile. Installed profiles and historical campaigns remain unchanged.

Fresh launch: `python campaigns/2026-11-06-p100-rear-exhaust-cooling/scripts/start.py`. Refuses non-planned state, an occupied port or detected existing inference/measurement processes. No automatic recovery, stress workload or monitor. Inspect live command lines before stopping or recovering the owned server; saved PIDs are not ownership proof.

API binds `0.0.0.0:8080` at user request, using the usual installed API key. Local: `http://127.0.0.1:8080`; LAN: `http://172.27.73.6:8080` (subject to firewall/routing). Credential-bearing runtime configuration is ignored under `configs/private/`; engine/server logs are in `results/`. See `state/queue-state.json` for launch checkpoint. Three sequential 10-minute reference captures completed: mean board power **197.95 W, 196.49 W, 198.18 W** (three-run mean **197.54 W**). These are cooling telemetry, not inference-speed measurements. Progress: `state/reference-state.json`; raw CSV/JSON: `results/*-rear-pull-reference-*`. `state/STOP` pauses between runs. No comparative cooling conclusion or report yet. The supervisor finished without stopping the user-managed workload.
