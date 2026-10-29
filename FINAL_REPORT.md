# Strata IQ3_S 128K tuning — final recommendation

Completed 2026-10-29. **54 complete BetterBench runs**, one rejected startup, plus functional/long-context sanity checks. The original installed profile is unchanged. Benchmark servers have been stopped and their RAM/VRAM released.

## Recommended mix

Keep the existing model, native weights, MTP, int8 KV, **131072 context**, KV residency 32768, `--prefill auto`, and five CPU workers plus the host. Add only these speed settings:

```text
--pool-tasks 36
--adapt-every 1
```

Engine environment:

```text
STRATA_PCIE_BALANCE=1
STRATA_ROUTE_PRIOR=0
STRATA_ROUTE_TAIL_SKIP=0
```

The first environment variable is a speed setting. The last two **disable approximate routing**; the prior was already disabled in your existing profile. Tail skipping was an engine default, not an explicit setting in your profile.

**Run:** double-click [`Run-Tuned.cmd`](Run-Tuned.cmd), or use the private local profile `configs/recommended.json`. The published, credential-redacted equivalent is [`configs/shareable/recommended.json`](configs/shareable/recommended.json); the launcher resolves its credential from the existing installation or `STRATA_API_KEY` when no private copy is present. It uses your existing installed Control/engine and API key, listens on `127.0.0.1:8080`, and prevents saved presets from silently overwriting the tested settings. Stop any other server using port 8080 first. It does not overwrite the installed launcher/profile. The local config contains your existing API credential: do not publish it.

## Final confirmation results

Medians, tokens/s. Identical requested BetterBench workload; each row is a fresh server, 5 measured code passes and 8 measured prefill passes after warmups.

| Configuration | Code decode | Prefill | Notes |
|---|---:|---:|---|
| Untouched installed baseline | 36.08 | 381.83 | Approximate expert-tail skipping ON; earlier auto allocation chose a smaller chunk |
| Initial quality reference | 28.95 | 385.46 | Only expert-tail skipping disabled |
| Late unchanged quality reference | 28.75 | 429.32 | Auto chunk/cache allocation changed; see caveat below |
| Selected combination, discovery (`ablate-no-host`) | 31.97 | 428.29 | Host/core, KV and drafting remain at their original settings |
| Selected combination, confirmation 1 | **31.25** | **428.51** | Also passed 6/6 functional/recall checks |
| Nearby unchanged quality reference | **30.30** | **424.61** | Between the two final confirmations |
| Selected combination, confirmation 2 | **31.27** | **426.38** | Same three speed settings |

The two final confirmations average **31.26 decode / 427.45 prefill**, versus the intervening reference **30.30 / 424.61**: approximately **+3.2% decode**, with essentially unchanged prefill (**+0.7%** in these samples).

**Important:** this is NOT a speedup over the 36.08 tok/s approximate original baseline. Restoring all routed target-expert contributions costs speed. The recommendation makes no new quality-reducing trade, but its restored full-expert computation is slower than the original approximate default. Do not compare those modes as if their computations were identical.

Five sampled code passes are too few for a strong significance claim. Final confirmation gains are modest, not the +10% suggested by some discovery runs. Treat this as the best observed quality-preserving mix on this workload, not a guaranteed improvement on every agent session. No formal paired A/B significance is claimed.

## Why this combination

- **36 pool tasks:** more evenly distributes CPU expert work than the automatic 18-task granularity without reducing worker count.
- **Adapt every window:** follows the code's expert usage more quickly. The engine may choose its existing asynchronous tier; no forced async mode is added.
- **Per-layer PCIe balance:** divides missed-expert work using each layer's CPU/transfer balance instead of forcing one global fraction.
- **No host pinning override:** `--host-core last` looked promising alone, but removing it from the combination gave better prefill and simpler, repeatable results.
- **No KV-residency change:** lowering residency changed cache/chunk geometry and hurt combined prefill. Keep 32768 and the complete 128K capacity.
- **No speculative changes:** the narrow/quantized draft and extra lookup variants did not deliver a better confirmed balance. Keep original spec 4 / confidence .5 and original draft files.

The final changes schedule/locate existing expert computation; they do not prune experts, reduce target precision, modify reasoning instructions, or shrink context.

## Correctness and context checks

The final recommendation (`final-candidate-1`) and unchanged quality reference (`reference-confirm`) each passed **6/6**:

1. Stable-unique algorithm result.
2. Python alias/copy execution trace.
3. Binary-search insertion bounds.
4. Correct declared tool name and JSON arguments.
5. Three records retrieved at 10%, 50%, 90% depth in **32151 actual prompt tokens**.
6. Three records retrieved at those depths in **119151 actual prompt tokens**.

All recall requests were cold (`cached_tokens: 0`). The long check exercises KV streaming while retaining the configured 131072-token capacity. It is not an exact 131072-token needle test. Generated code was never executed; coding checks compare expected results. These are smoke checks, **not proof of unchanged intelligence across a full coding/agent benchmark**.

Evidence: `results/final-candidate-1.sanity.json`, `results/reference-confirm.sanity.json`, and `scripts/sanity.py`. An earlier four-setting candidate also passed 6/6, but was not selected after ablation.

## Measurement and interpretation

Every timed run used:

```text
betterbench run --endpoint http://127.0.0.1:8080/v1 --model qwen3.8-flash-next-iq3_s --quick --decode --categories code --prefill --no-concurrency --config C:/ai/tuning/16k.json --out <unique-result.json>
```

The API key was passed in the environment. `16k.json` is exactly `{"prefill_depths":[16384]}`. No shortened outputs, changed sampling, suppressed reasoning, extra concurrency or fewer prefill passes were substituted. Decode includes reasoning tokens, as BetterBench normally measures them; some short corpus responses hit their requested output cap. This is a speed test, not corpus answer grading.

**16K is the BetterBench target, not an exact tokenizer length:** this model receives approximately 12K actual prompt tokens for that synthetic filler. Actual counts remain in every JSON. No claim of exact 16384-token prefill is made.

Auto allocation is material on this WDDM display GPU. The first reference got about 1513 expert slots and a 4864-token prompt chunk; later unchanged starts got about 1605 slots and a 5376 chunk. Thus many unrelated early switches falsely appeared to improve prefill by ~11%. The final claim uses nearby confirmation/reference runs, not that initial-reference artifact.

Larger 5632-token auto chunks were sometimes **slower** than 5376 on Pascal's cuBLAS path. `auto:5376` was attempted as a cap, but source inspection and logs proved this spelling is treated as ordinary auto in engine 0.1.52; it did not impose that cap. Those no-op trials are retained and are not recommended. The final profile uses plain `auto`.

GPU telemetry during later trials was roughly 52–62 C, with median clocks around 1949 MHz; no evidence of thermal throttling causing the observed chunk-related differences. Free VRAM remained limited on WDDM. Raising reserve to 1400 MiB was tested but lost prefill, so the reserve is unchanged. Extra GPU applications can change the result; no driver fallback policies, overclocks, power limits or privilege policies were changed.

## Rejected / deferred

- PLE mmap, reduced worker counts, host sibling, fixed PCIe shares, spec 5, lower draft confidence: no useful balanced gain.
- Explicit prefill 2048: severe prefill regression. Head alias needs `--short-read 0`; after testing that prerequisite independently, the valid pair still regressed prefill severely. The original rejected startup is retained, not assigned zero speed.
- Combining every apparent single-run winner was worse than the selected small combination. Several larger decode discovery gains shrank on confirmation.
- Lower KV precision, routing biases, tail skipping, speed projections, target quantization changes, expert pruning, lower reasoning/context: excluded as quality-reducing optimizations.
- Pascal dense FP32 route: deferred because bitwise parity was established externally only for cuBLAS 12.4.5.8, not this installed 12.9. No suitable MSVC host compiler was found for locally building the parity tool. Do not assume its quality/speed gate transfers.
- Multi-GPU, NUMA, Linux-only, hybrid-core and newer-architecture/Tensor Core switches: inapplicable here. Large pages require a privilege/logon change, not applied.

## Hardware/software and evidence

- GTX 1080 Ti 11 GiB (sm_61, WDDM display GPU), NVIDIA driver 582.66.
- i5-11400F, 6 physical / 12 logical cores; ~63.9 GiB usable RAM; PCIe probe ~12.7 GB/s.
- Existing engine 0.1.52 CUDA12 package (CUDA 12.9), build commit `a42cc3d7df70d1940de82cd0882f03e1f5dfc741`; Control 0.1.51.
- BetterBench 0.6.1, checkout `f72bb9011a830fd98e82ab89d01e549efa76e9c5`.
- Research/evidence links and candidate rationale: [`TUNING_PLAN.md`](TUNING_PLAN.md).
- All single/follow-up results and final usage marks: [`RESULTS.md`](RESULTS.md).
- Combined-stage table: [`COMBINED_RESULTS.md`](COMBINED_RESULTS.md); interpretation: [`STAGE1_REVIEW.md`](STAGE1_REVIEW.md).
- Per-run raw JSON, HTML, engine/server logs, telemetry and sanity results: `results/`.
- Engine binary hash and original-profile check: `results/final-provenance.json`.

The baseline initially hit a Windows cp1252 Unicode error **after all measurements were saved**. Its report was re-rendered from saved JSON with UTF-8; measurements were not discarded or rerun. Subsequent runs used UTF-8. All other failures/measurements are retained.
