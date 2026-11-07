# Research and applicability — 2026-11-07

## Read upstream, then check installed behavior

1. [Current MULTI_GPU.md](https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md), accessed 2026-11-07. Main is last and runs head/draft/verify; split is contiguous layer pipeline, not tensor parallelism. Auto placement/cache behavior depends on per-card memory and link probes; x16+x4 can benefit from a deliberate split. Extra cards are not guaranteed to speed up one request. The current document includes much newer behavior (including 0.2.x defaults), **not evidence that installed 0.1.57 implements those defaults**.
2. [Community report #1586](https://github.com/Niko1221/Strata/issues/1586), engine 0.1.41, two 3090s with CPU x16 plus chipset x4. Explicit split plus trim increased expert residency and had a measured decode gain there. Supports testing trim/placement, not importing its rates, newer cards' CUDA behavior, batch setup or CPU tuning to Pascal. Its follow-up warns that long-context concurrent KV streaming can collapse throughput; this campaign keeps single-request/no-concurrency fixed.
3. [Allocation report #133](https://github.com/Niko1221/Strata/issues/133). Windows dual-card allocation failure may involve system commit, not simply VRAM. Maintainer explicitly points to RAM+page-file accounting. This is historical failure context, not proof of today's root cause or a reason to change page-file settings automatically.

## Local evidence has precedence

- `results/installed-engine-help.txt`: fresh 0.1.57 CUDA12 `--help`, exit 0, no inference. Confirms `--gpu`, trim for explicit splits, pipeline windows, prefill-pipe, int8 KV/residency and peer option. Some split/reserve flags are not printed in help; `results/installed-binary-option-presence.json` records their literal presence in this exact binary. That is **not proof of effective startup semantics**.
- Installed Control 0.1.57 `serve/server.py` inspected around `layer_split_value`, `engine_args`, `ordered_gpus` and `learned_profile_args`. `gpu_order=as_given` prevents automatic reorder, explicit `args` override duplicate split field insertion, and `user_args` can overwrite generated args. Therefore new profiles are built from a clean known full-quality recipe, **not a shallow clone retaining as-found user_args/args_derived/projection settings**. Pin `drafting=mtp`, not current Control's auto drafter selection.
- Active Control is 0.1.57; both 0.1.55 and 0.1.57 engine/Control are installed. All new runs use explicit 0.1.57 paths, never `component:strata-engine` alias or an automatic update. No installation changes performed.
- `results/gpu-links.txt` confirms GPU 0 UUID P100 x16/TCC, GPU 1 UUID 1080 Ti x4/WDDM. PnP paths show PEG1 versus RP21 (`results/pci-location-paths.txt`), consistent with the user's CPU-versus-chipset slot description. No P2P/NVLink assumption. This Windows `nvidia-smi topo -m` returned unsupported-option error during read-only discovery; not retried as a load test.

## Historical findings to use only as leads

- [November 1 x16/x4](../2026-11-01-p100-1080ti-x16-x4/RESULTS.md): six completed 0.1.55 screens; both Main orders worth checking. No independent final deployment recommendation; do not restart its queue. Work log is embedded in README/results/state; no NOTES.md existed.
- [November 2 x8/x8](../2026-11-02-p100-1080ti-x8-x8/REPORT.md): explicit 32/16 plus trim and later reserve 1600 useful; default-draft pipeline on 1080 Main failed with non-finite/watchdog errors, and expert peer OOM'd. These justify safe reserves, staged explicit placement and deferring pipeline/peer, not assuming either failure or winner transfers unchanged.
- [November 7 cooling](../2026-11-07-p100-server-fan-intake-exhaust/COMPARISON.md): improved SM clocks under prefill stress; not new inference-speed evidence. Last confirmed physical setup is intake-only, open case. Confirm the retained fan setup before tuning and hold it fixed.
- Pinned `research/strata-source` belongs to engine 0.1.52. It is not authoritative for 0.1.57 flags/defaults; no source checkout or submodule update was performed.

## Startup acceptance before conclusions

Retain actual engine version, CUDA-visible card order, stage ranges, head/MTP placement, measured host-to-device GB/s/PCIe fractions, per-card expert cache counts, prompt buffers/chunks, reserve/free VRAM, full target/context/int8 KV and any fallback. Reject non-finite logits, watchdog resets, unexpected stops, dropped MTP/changed draft source or silent context/quality changes as equivalent measurements. The first phase stops for manual log/telemetry review; no ranking before real measurements.
