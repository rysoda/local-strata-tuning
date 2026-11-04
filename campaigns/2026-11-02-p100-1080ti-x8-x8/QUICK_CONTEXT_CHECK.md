# One-off 128K versus 256K capacity check — 2026-11-04

User requested two quick tests, not a new tuning campaign. Completed separately from the original completed queue; original profiles, report and queue state unchanged. No new deployment recommendation or full-context quality validation.

Only scientific setting changed: `--max-context 131072` → `262144`, using isolated private copies of `recommended-x8.json`. Engine/Control 0.1.55, IQ3_S, int8 KV, `--kv-resident 32768`, full expert routing, 32/16 layer split, trim and later reserve 1600 retained. Localhost:8080, presets disabled.

## Results

One BetterBench 0.6.1 quick pass per capacity, sequential 128K then 256K. Exact workload: `--quick --decode --categories code --prefill --no-concurrency --config workloads/betterbench-16k.json`.

| Capacity | Decode median tok/s | Prefill median tok/s | P100 resident experts | 1080 Ti resident experts | Total GPU-resident experts |
|---|---:|---:|---:|---:|---:|
| 131072 | 39.054 | 346.407 | 6323 | 2691 | 9014 |
| 262144 | 38.641 | 347.096 | 6238 | 2643 | 8881 |

256K change: **−0.413 decode tok/s (−1.06%)**, **+0.689 prefill tok/s (+0.20%)**. This is effectively little difference in these screens, not proof of a repeatable 1% penalty. Five successful decode samples and eight prefill samples per arm. Decode samples span 35.95–41.53 tok/s at 128K and 37.50–40.34 at 256K; generated output lengths vary with normal sampling.

Startup expert cache residency falls **133 slots (1.48%)**: P100 −85, 1080 Ti −48. These are GPU-cached layer/expert pairs, not a reduction in routed/available model experts. Host expert arena remains 40290 MiB locked in both startup logs. KV resident cells remain 32768; pinned host KV storage rises **1.03 → 2.06 GiB**. No routing/pruning changes.

Actual prefill prompt token counts:
- 128K: 12003, 12098, 12123, 12177, 12070, 12110, 12091, 12082.
- 256K: 12009, 12075, 12027, 12110, 12102, 12147, 12131, 12057.

## Interpretation and limitations

Increasing the configured ceiling appears inexpensive for the same short workload. This does **not** measure decode speed at 128K/256K populated context, nor verify recall/quality near 256K. Longer live context increases attention/KV-streaming work regardless of this capacity comparison. No long-context or functional sanity tests requested/performed.

Both arms logged similar low-VRAM warnings (~800 MiB, later ~620 MiB); no non-finite, watchdog or OOM errors found. Extra desktop/GPU workloads remain a headroom risk. No further parameter tuning attempted.

All owned servers/benchmarks stopped; no listening server on port 8080 after completion. Repository validation passed (648 original artifacts/checkpoints unchanged).

## Evidence

- [Raw results, logs, all samples and provenance](results/quick-context-20261104-183154/)
- [Summary](results/quick-context-20261104-183154/summary.json)
- [Separate quick-check checkpoint](state/quick-context-20261104-183154.json)
- [One-off runner](scripts/quick_context_check.py) (each invocation creates new IDs, never resumes original queue)

Private experimental profiles are under ignored `configs/private/quick-context-20261104-183154/`; credentials are not published. Installed/default/recommended startup profiles remain at 128K, as requested for a test only.
