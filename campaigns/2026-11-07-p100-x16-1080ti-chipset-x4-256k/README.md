# Cooled P100 x16 + GTX 1080 Ti chipset x4 retuning

[Campaign index](../../README.md) · [Plan](PLAN.md) · [Research](RESEARCH.md) · [Manifest](manifest.json) · [Work log](NOTES.md) · [Report](REPORT.md) · [Live results](RESULTS.md)

**Complete: 17 benchmarks.** Selected P100 **36 layers** / 1080 Ti **12 layers/Main**, trim, physical reserves **1400/2304 MiB**, **262144 context**. Two final confirmations averaged **36.40 decode / 325.96 prefill tok/s**, versus nearby P100-only **33.27 / 333.98** (**+9.38% decode / −2.40% prefill**). Candidate and reference each passed **7/7** smoke checks, including **230146 actual prompt tokens**. Decode varied between confirmations; no significance or comprehensive quality claim. [Final report](REPORT.md). Cooling fixed by user: **open case, intake + exhaust, 75°C target, intake capped at 45% for noise**. See live state/results for measured progress. This is a new campaign, not a restart of the historical x16/x4 or x8/x8 queues.

## Fixed hardware and quality

- GPU 0: **P100 16 GB/TCC, PCIe 3.0 CPU x16**, bus 01:00.0.
- GPU 1: **GTX 1080 Ti 11 GB/WDDM, PCIe 3.0 chipset x4**, bus 03:00.0; stays in this slot for cooling and remains the display card.
- i5-11400F, approximately 64 GiB RAM, MSI MEG Z490 UNIFY, Windows 11 Pro, NVIDIA driver 582.66. Captured inventory: `results/`.
- **Installed active engine/Control 0.1.57 CUDA12**, BetterBench 0.6.1; frozen for every arm. No software was upgraded for this campaign.
- **Qwen3.8-Flash-Next IQ3_S, 262144 context, int8 KV, 32768 resident KV, full experts, existing MTP/reasoning behavior. No speed projection.**
- Future **two P100s sharing CPU x8+x8** are outside scope and require a separate campaign.

The installed profile named `iq3_s-128k.json` actually requests 262144 context and a speed-projection control vector. Its exact bytes are saved privately; [redacted as-found profile](configs/shareable/original-installed-iq3_s-128k.json) is evidence, **not an endorsed test profile**. It is untouched. Fresh comparison begins with a quality-restored 256K version of its 32/16 trimmed layout and new single-card references. Old results are not reused as baselines.

## Initial tests

| Order | Test | Question |
|---|---|---|
| 1 | Full-quality 32 P100 / 16 1080 Main, trim | Fresh quality-restored installed-layout baseline |
| 2 | P100 alone | Is the chipset card actually worth using? |
| 3 | 1080 Ti alone | Current narrow-link/display-card reference |
| 4 | Auto split, 1080 Ti Main | Does extra expert capacity offset the x4 path? |
| 5 | Auto split, P100 Main | Does head/MTP on CPU x16/HBM win? |

Initial log review is complete: trim32 leads decode at 40.40 tok/s, P100-only leads prefill at 333.90 tok/s; both need better P100 headroom before recommendation. Auto1080Main actually enabled dense trim at K=35 (not an untrimmed control). Continue through targeted split/trim/chunk/reserve follow-ups. [PLAN.md](PLAN.md) explains one-setting-at-a-time tests, priority, exclusions and final confirmation/smoke checks. Decode is weighted slightly more than prefill; no projected speeds or promises.

## Reviewed continuation / progress

Live table: [RESULTS.md](RESULTS.md); durable progress: `state/queue-state.json`; supervisor output: `state/continuation-supervisor.log`.

```sh
python campaigns/2026-11-07-p100-x16-1080ti-chipset-x4-256k/scripts/continue.py
# Default validates only; explicit start/resume after inspecting live ownership:
python -u campaigns/2026-11-07-p100-x16-1080ti-chipset-x4-256k/scripts/continue.py --run
```

The continuation is complete; rerunning it starts nothing. It skips complete work and refuses unreviewed incomplete/error attempts; `state/STOP` pauses between runs. All initial results remain unchanged. It will select a headroom-eligible candidate, confirm around a fresh P100 reference, perform extended smoke checks and write a final report/profile only if those pass. Preference ranking is not statistical significance or comprehensive quality proof.

## Initial phase commands (already complete; no-op on rerun)

Default invocation only checks frozen installation/model/settings, profiles and expected UUID/link topology; it starts nothing:

```sh
python campaigns/2026-11-07-p100-x16-1080ti-chipset-x4-256k/scripts/run.py --check
```

First confirm a single fixed case/fan arrangement and no competing workload, then explicitly launch only the initial five screens:

```sh
python -u campaigns/2026-11-07-p100-x16-1080ti-chipset-x4-256k/scripts/run.py --run-initial --cooling-note "ACTUAL CASE/FAN CONFIGURATION; KEEP UNCHANGED"
```

Replace the placeholder with the actual physical setup. User has now confirmed open case, intake + exhaust, 75°C target, intake capped at 45%; use that exact unchanged declaration. Keep cooling, power limits, desktop/background load and workload fixed. No normal network-facing server is started: isolated test copies bind **127.0.0.1:8080**, presets disabled, original installed profile unchanged. Credential-bearing profiles stay ignored in `configs/private/`; publish with `python tools/publish_configs.py --campaign 2026-11-07-p100-x16-1080ti-chipset-x4-256k`.

Runner uses shared `tools/benchmark.py` and exact BetterBench quick/code/decode/16K-target prefill/no-concurrency workload. It checkpoints before/after every run, refuses unreviewed failed/incomplete attempts or orphan evidence, skips completed work, refuses existing processes/occupied port, and uses exclusive `state/runner.lock`. `state/STOP` pauses between arms. After an abrupt crash inspect live commands, port, locks and state; never clear evidence or kill processes from historical PIDs. Only explicitly owned test processes may be stopped.

## Scope of evidence

The [final report](REPORT.md) and `configs/shareable/recommended-256k.json` describe the benchmarked, projection-free profile. The separate [Startup deployment](../../launchers/Startup-Strata-P100-X16-1080Ti-X4-256K.bat) keeps the user's experimental projection by explicit request; that deviation was not benchmarked or smoke-validated. Current software is newer and P100 cooling differs from previous campaigns, so their speed numbers are research leads only. Thermal results are not decode/prefill measurements. Detailed immutable provenance includes active-version record, engine help/hash, PCI location paths, Windows RAM/page-file state, benchmark version and frozen-source/model inventory. Full model files are frozen by size/mtime inventory, not claimed content hashes; engine/Control sources, expert ranking and benchmark tools are SHA-256 checked.
