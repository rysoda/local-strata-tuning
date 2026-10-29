# First-stage review (2026-10-29)

All raw measurements and errors are preserved in `results/`. See `RESULTS.md` for the complete single-parameter table.

## Findings before combined testing
- Untouched original: 36.08 decode / 381.83 prefill tok/s; quality reference (tail skipping disabled): 28.95 / 385.46. Restoring all target expert contributions costs speed; **do not disguise that as a tuning regression or re-enable skipping to win**.
- 29 valid single-setting measurements completed; `--prefill-head-alias` refused startup because it requires `--short-read 0`. This is a compatibility failure, not zero throughput. Test the prerequisite independently before any head-alias pair.
- Highest initial single decode: `--adapt-every 1` 31.53, followed by PCIe balance 30.81, tasks 36 30.73, suffix-off 30.63, lookup-chain 2 30.56. These are small, sampled gains; ranking can move.
- Reduced worker counts, host sibling, PLE mmap, fixed PCIe .15/.40, spec 5 and confidence .3 did not help decode. Prefill 2048 badly regressed prefill (297.79); reject.
- **Important confound:** first reference auto-sized to 1513 cache slots / 4864 prompt chunk. Most later starts got about 1605 slots / 5376 chunk, and almost every unrelated switch appears to improve prefill ~11%. This is auto-allocation / desktop-VRAM state, not proof that every setting speeds prefill. A late identical reference is running; compare candidates against that as well, do not stack fake prefill gains.
- Initial PLE probe was 8636 rows/s; later probe is ~46721. The slow-probe warning was not stable. Mmap measured slower overall, so do not recommend it based only on the first warning.
- WDDM startup headroom remains small (often ~380-560 MiB); reserve 1400 avoided some pressure but lost prefill. No OS/driver fallback-policy changes made.

## Combined-stage intent
Test resource/scheduling changes as a compact core (KV resident 20480, host last, tasks 36); then adaptive interval 1 and per-layer PCIe balance. Also test a conservative speculative refinement only if the core helps. Keep original target weights, all 128K context and int8 KV; all approximate routing stays disabled. Compare with a fresh quality reference at the start/end and report drift. Do not infer independent effects from combination results.

## Combined-stage review (04:36)
- Resource core alone: 28.83 / 373.29; adding adaptation + balance: 31.99 / 377.00; adding lookup: 31.48 / 375.35; smaller/quantized draft arm: 32.63 / 374.48.
- Post-combination unchanged reference: 30.17 / 426.85. Decode drift/noise is several percent; confirmation is required.
- Head alias with its valid short-read-0 prerequisite was measured: 29.70 / 290.88. Reject for severe prefill regression; prerequisite alone 30.02 / 424.02.
- A simpler core **keeps original KV residency, target and draft settings**, changing only host last, tasks 36, adapt interval 1 and PCIe balance: **32.51 / 422.19**. This is the preferred confirmation candidate: about +10% decode against the immediately subsequent reference with only ~1% less prefill.
- GPU telemetry across late reference and combinations: ~52-62 C, median clocks ~1949 MHz. No evidence of thermal throttling explaining the chunk-specific prefill regressions.
- **Correction to attempted chunk-cap experiment:** `--prefill auto:5376` does NOT cap chunks at 5376 in this engine. Parser `src/program/generate.cpp:3116-3122` maps any auto:N below 16384 to ordinary auto's 8192 upper limit. The draft arm still logged a 5632 chunk. Preserve these no-op experiment artifacts, but do not attribute changes to a working cap. The simple arm's recovered prefill came from retaining original KV residency and getting a 5376 auto chunk. Recommend plain `--prefill auto`, not this misleading spelling.

## Gates and final outcome
- Identical late reference completed: **28.75 decode / 429.32 prefill**. Decode is within 0.7% of the first quality reference; the 11.4% prefill shift confirms allocation/chunk drift, not 11% improvements from unrelated settings.
- Head-alias prerequisite and compatible pair completed; pair rejected for prefill regression.
- Final candidate and quality reference passed 6/6 coding/tool/recall smoke checks, including 119151-token prompts. These are not proof of unchanged model intelligence.
- Final ablation/confirmation selected **tasks 36 + adapt interval 1 + PCIe balance**, leaving original host placement, KV residency and draft settings intact. Final confirmation decode 31.25 and 31.27 versus intervening reference 30.30; prefill essentially unchanged. See `FINAL_REPORT.md` for the approximately +3.2% confirmed screening gain and the approximate-original-baseline quality caveat.
- All runs are finished and benchmark processes stopped. Ready profile: `configs/recommended.json`; launcher `Run-Tuned.cmd`.
- `STRATA_DENSE_F32` remains deferred: installed cuBLAS 12.9 parity untested, and no MSVC host compiler found on PATH / standard installation path for nvcc parity-tool build. Do not enable merely on CUDA 12.4 evidence.
