# P100 + GTX 1080 Ti: historical PCIe x16/x4 comparison

[Campaign index](../../README.md) · [Manifest](manifest.json) · **[Results](RESULTS.md)**

**Completed historical screening:** six complete benchmarks. P100 16 GB/TCC on PCIe 3 x16; GTX 1080 Ti 11 GB/WDDM on PCIe 3 x4; i5-11400F, 64 GB RAM. Engine/Control 0.1.55 CUDA12, BetterBench 0.6.1; IQ3_S, 131072 context, int8 KV / 32768 residency.

Both-card configurations reached roughly 35–39 decode / 284–296 prefill tok/s. This topology was replaced by [CPU-connected x8/x8](../2026-11-02-p100-1080ti-x8-x8/), which has the current deployment recommendation. These screens are not an interchangeable reference for changed links or older engine versions. One historical dual-card confirmation passed 6/6 smoke checks; no independent final deployment profile was selected here.

## Navigate

- [Comparison table and rationale](RESULTS.md)
- [Redacted configurations](configs/shareable/)
- [Raw evidence](results/), including installed engine help and startup failure records
- [Queue checkpoint](state/gpu-comparison-state.json)
- [Original single-card campaign](../2026-10-28-1080ti-tuning/), whose selected speed settings were inherited

## Resume safety

From repository root:

```sh
python campaigns/2026-11-01-p100-1080ti-x16-x4/scripts/run.py
```

Now reports that historical screening is complete and starts nothing. Its original state phase `screening-complete-review-required` is preserved rather than rewritten to imply a final deployment review. Pause flag is `state/STOP-GPU`. For a new topology start a new campaign instead of clearing this state.

Raw logs/checkpoints retain historical paths and PIDs. Old `GPU_COMPARISON.md` is now this campaign's `RESULTS.md`; old `scripts/gpu_compare.py` became `scripts/run.py`, with shared mechanics under repository `tools/`.
