# P100 + GTX 1080 Ti: final x8/x8 recommendation

Completed 2026-11-02: **16 complete BetterBench runs, 2 rejected configurations**, plus an archived interrupted attempt. All test servers/benchmarks stopped; port 8080 free. Original installed profile and original `configs/recommended.json` / `Run-Tuned.cmd` unchanged.

## Use this configuration

Launch **`Run-Tuned-X8.cmd`**. Private local profile: **`configs/recommended-x8.json`** (contains existing API credentials; do not publish).

- GPU 0 **Tesla P100 16 GB**: first stage, layers **0–31**.
- GPU 1 **GTX 1080 Ti 11 GB**: last stage/**Main**, layers **32–47**, output head and draft layer.
- `gpu: [0, 1]`, `gpu_order: "as_given"`, `layer_split: "32"`.
- Add **`--trim-stage-weights --vram-reserve-later-mib 1600`**.
- Keep pipeline windows **off/default**. Do not add the experimental expert peer.
- Retain existing tuned tasks/adaptation/PCIe balance, **full expert routing**, IQ3_S weights, **131072 context**, int8 KV and 32768 resident KV. No precision/context reduction, expert pruning or model change.

Trimming removes duplicate dense weights from cards that do not execute those layers; it does **not** remove model layers. Explicit placement outperformed auto in this screening. The later-card reserve avoids filling the display card to its WDDM limit: final-profile startup showed about **779 MiB free on P100 / 890 MiB on 1080 Ti**, without the earlier LOW warning. This is headroom for the measured desktop workload, not a guarantee alongside a game or another GPU application.

## Nearby confirmation

Same installed **engine/control 0.1.55 CUDA12**, both CPU-connected PCIe 3 x8. Exact requested BetterBench workload: `--quick --decode --categories code --prefill --no-concurrency --config 16k.json`. Values are medians of five code decode / eight prefill samples in tok/s. BetterBench's 16K-target corpus actually tokenizes to roughly 12K with this model; no claim that each sample contains exactly 16384 model tokens.

Chronological sequence:

| Run | Configuration | Decode | Prefill | Functional/recall |
|---|---|---:|---:|---|
| x8-final-1 | Recommended dual split | **40.62** | **317.70** | **6/6** |
| x8-p100-reference | P100 alone | 32.36 | 264.12 | **6/6** |
| x8-final-2 | Recommended dual split | **37.30** | **319.54** | Not repeated |

Against the intervening P100 reference, confirmed decode gains range **+15.3% to +25.5%**; prefill **+20.3% to +21.0%**. The descriptive mean of the two candidate run medians is **38.96 decode / 318.62 prefill**, about **+20.4% / +20.6%** versus that reference. These are quick screening runs, **not a formal statistical-significance claim**. Decode fluctuated materially even between final confirmations.

The earlier midnight P100-only screen was faster on prefill (31.95 / 295.52): against that older reference the final candidate's prefill gain is only about **8%**, not 21%. Auto cache/chunk allocation, temperature/clocks, desktop load and run-to-run conditions can change results. Use the new nearby reference as the direct comparison, but do not promise a universal 21% prefill gain.

## What was tested and rejected

Full live table: **`GPU_X8_RESULTS.md`**; restart/recovery log: **`GPU_X8_NOTES.md`**.

| Configuration | Decode | Prefill | Decision |
|---|---:|---:|---|
| P100 only, early screen | 31.95 | 295.52 | Single-card fallback |
| 1080 Ti only | 20.70 | 201.49 | Clearly slower |
| Auto split, P100 Main | 36.18 | 304.59 | Better than single-card screen, not best |
| Auto split, 1080 Main | 34.80 | 300.45 | Not best; very low VRAM headroom |
| Pipeline 2, P100 Main, default draft | 37.92 | 287.20 | Lower prefill, not selected |
| Pipeline 2, 1080 Main, default draft | — | — | **Rejected: hangs, non-finite logits, watchdog restarts** |
| Trim 32 P100 / 16 1080 Main | 38.72 | 321.33 | Promising, but only ~46 MiB later-card headroom |
| Trim equal 24/24, 1080 Main | 36.77 | 316.90 | Slower decode |
| Auto P100 Main, later reserve 1600 | 34.17 | 286.71 | Not selected |
| Pipeline 2 + stage-0 draft + reserve, P100 Main | 35.94 | 274.73 | Not selected |
| Pipeline 2 + stage-0 draft + reserve, 1080 Main | 30.42 | 287.00 | Completed, but slower |
| P100 primary / 1080 expert peer | — | — | **Rejected: startup `peer experts: stream: out of memory`** |
| Auto P100 Main + prefill-pipe 1 + reserve | 34.93 | 303.60 | No compelling overall gain |
| Trim 32/16, 1080 Main, later reserve 1600 | **40.56** | **316.56** | Selected for confirmation |
| Trim 16/32, P100 Main, later reserve 1600 | 37.40 | 286.10 | Reverse Main order slower |

Reserve and stage-0 draft were combined in pipeline follow-ups for safety, so those arms do not isolate each setting's individual contribution. The selected configuration was tested and confirmed as a complete configuration, not inferred by adding isolated speedups.

## Correctness and thermals

Candidate and nearby P100 reference each passed stable-unique, Python alias tracing, binary-search boundaries, a structured tool call, and recall at approximately 32K and 119K content tokens. The longest request used **119151 actual prompt tokens** and recovered all three distributed keys. These are functional/recall smoke checks, **not comprehensive proof of unchanged model quality** or validation of every token up to the 131072 limit. GPU placement and reduction order can change floating-point rounding.

No non-finite/watchdog/unexpected-engine-stop errors were found in the 16 completed runs' server logs. The rejected pipeline configuration is excluded, not averaged into speed results.

Final runs peaked at **80 C P100 / 62–63 C 1080 Ti**. Sampled hardware/software thermal-slowdown flags were not active; this does not prove clocks were constant or rule out power/thermal effects between samples. Ensure the passive P100 continues to receive adequate forced airflow. No clocks, voltage or power-limit changes were made.

## Files and restart

- `results/gpu-x8-state.json`: final phase **`gpu-tuning-complete`**, 18 reviewed arms, selected profile and confirmation IDs.
- `scripts/gpu_x8.py`: resumable queue, exclusive lock, explicit reviewed-failure handling. Running it now reports completion and starts nothing. Do not clear completed state unless intentionally extending experiments.
- `results/x8-*`: raw JSON/HTML, engine/server/benchmark logs and per-run GPU samples.
- `results/gpu-x8-telemetry.csv`: per-card temperatures/clocks/thermal flags/link widths.
- `results/interrupted-x8-dual-p100-20261102/`: preserved interrupted attempt; no final speed result.
- `python scripts/run_gpu_tuned.py --check`: validates local profile/install resolution without launching. Actual launcher binds localhost:8080 and refuses to stop an existing server.
- To extend, add deliberately chosen new unique run IDs and reset only the top-level final phase after reviewing processes; preserve completed entries and failure notes. `STOP-GPU-X8` pauses between experiments. See work log before resuming.

Research: upstream [MULTI_GPU.md](https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md) and [SECOND_GPU.md](https://github.com/Niko1221/Strata/blob/main/docs/SECOND_GPU.md), checked against installed `--help`, installed server logic and startup logs. In particular, this CUDA build did not automatically place the pipelined draft on stage 0, unlike some newer documented defaults.
