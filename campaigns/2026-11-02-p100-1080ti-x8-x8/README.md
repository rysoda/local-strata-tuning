# P100 + GTX 1080 Ti: CPU PCIe x8/x8 tuning

[Campaign index](../../README.md) · [Manifest](manifest.json) · **[Final report](REPORT.md)**

**Current hardware recommendation; complete 2026-11-02.** Sixteen complete BetterBench runs, two rejected configurations and one preserved interrupted attempt. P100 16 GB/TCC + GTX 1080 Ti 11 GB/WDDM, both CPU-connected PCIe 3 x8; i5-11400F, 64 GB RAM. Engine/Control 0.1.55 CUDA12, BetterBench 0.6.1; IQ3_S, 131072 context, int8 KV / 32768 residency.

## Recommendation

- P100 GPU 0: layers **0–31**.
- 1080 Ti GPU 1: layers **32–47 / Main**.
- `gpu=[0,1]`, `gpu_order=as_given`, `layer_split=32`.
- `--trim-stage-weights --vram-reserve-later-mib 1600`; pipeline off/default.
- Keep full expert routing and the original target model/context/precision.

Final confirmations: **37.30–40.62 decode / 317.70–319.54 prefill tok/s**; nearby P100 reference **32.36 / 264.12**. Decode gains +15.3% to +25.5% in quick screening, not formal significance. Prefill gain depends materially on which reference is used. Candidate and reference each passed 6/6 smoke checks including **119151 actual prompt tokens**; not comprehensive quality proof.

Launch [launchers/Run-P100-1080Ti-X8.cmd](../../launchers/Run-P100-1080Ti-X8.cmd), or validate without inference from repository root:

```sh
python tools/launch.py 2026-11-02-p100-1080ti-x8-x8 --check
```

## Navigate

- **[Report](REPORT.md)**: selection, comparisons, quality/thermal caveats and launch instructions
- [All run results](RESULTS.md), [work/recovery log](NOTES.md)
- [Redacted recommendation](configs/shareable/recommended-x8.json); private copy in ignored `configs/private/`
- [Raw evidence](results/), [queue checkpoint](state/gpu-x8-state.json)
- Related: [old x16/x4 comparison](../2026-11-01-p100-1080ti-x16-x4/) and [original single-card tuning](../2026-10-28-1080ti-tuning/)

## Resume safety

```sh
python campaigns/2026-11-02-p100-1080ti-x8-x8/scripts/run.py
```

Now exits at `gpu-tuning-complete` and starts nothing. Pause flag: campaign `state/STOP-GPU-X8`; state and supervisor log are in `state/`. Do not restart this queue for a new card/topology. If intentionally extending this exact comparison, preserve completed entries/failure notes, add new unique IDs, and inspect processes/port/locks before changing the top-level final phase.

## Relocation notes

Old `GPU_X8_REPORT.md`, `GPU_X8_RESULTS.md`, `GPU_X8_NOTES.md` became `REPORT.md`, `RESULTS.md`, `NOTES.md`. Old `scripts/gpu_x8.py` became campaign `scripts/run.py`. Shared mechanics are in repository `tools/`; workload is [workloads/betterbench-16k.json](../../workloads/betterbench-16k.json). Raw artifacts and checkpoint contents remain unchanged, including historical paths/PIDs. Historical commands in the work log describe the old layout, not current restart commands.
