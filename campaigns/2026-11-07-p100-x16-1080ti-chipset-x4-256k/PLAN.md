# Plan: cooled P100 CPU x16 + 1080 Ti chipset x4

## Fixed question and objective

With the cards staying in their current slots, is the 1080 Ti worth using for one agentic request, and if so which Main order, layer placement and memory budget are best? No moving the 1080 Ti for any run. The future second P100 on CPU x8+x8 is explicitly outside this campaign and needs its own fresh baseline.

Keep Qwen3.8-Flash-Next IQ3_S target weights, 262144 maximum context, 32768 resident cells, int8 KV, full expert routing, existing reasoning/MTP behavior (spec 4/min-p 0.5), expert ranking, CPU tasks/adaptation, engine/Control 0.1.57 CUDA12, BetterBench 0.6.1 and workload fixed. No precision reduction, expert skipping, speed-projection vectors, reduced context or reasoning changes. No engine/model updates during comparison.

Decode matters slightly more than prefill: report both, not a misleading single winner by whichever metric happens to improve. For shortlist ranking only, use normalized score `(decode/reference_decode)^0.55 * (prefill/reference_prefill)^0.45`. Disclose material regressions in either metric. Noise-sized differences trigger nearby repeats, not a declared winner; the score is a preference, not a confidence estimate.

## Baseline distinction

The installed `iq3_s-128k.json` name is misleading: captured arguments request 262144 context and an experimental speed-projection vector. Its `exe` is a component alias and `cwd` still names Control 0.1.55, while the active Control is 0.1.57. Exact original bytes are preserved privately; a redacted snapshot is published. No original profile is edited and no performance result from it is treated as a same-quality baseline.

First measure a **quality-restored installed layout**: P100 0–31 / 1080 Ti 32–47 Main, trim, at 262144 with no projection and full experts, explicitly pinned to engine/Control 0.1.57. The known archived full-quality P100 recipe supplies common inference settings, not an old speed result. New single-P100 and single-1080 references use identical quality/software/workload. All numerical comparisons require these fresh measurements; old x16/x4 and x8/x8 numbers are motivation only.

## Phase 1: five initial screens, then mandatory review

| ID | Cards / Main | Placement | Why |
|---|---|---|---|
| r01-quality-reference-layout | P100 then 1080 Ti Main | Explicit K=32 + trim | Current installed layout, restored quality and fixed 256K |
| r02-p100-only | P100 only | All 48 layers | Does the x4 helper actually beat this cooled reference? |
| r03-1080-only | 1080 Ti only | All 48 layers | Establish current x4/display-card floor without moving it |
| r04-auto-1080-main | P100 then 1080 Ti Main | Auto requested; engine automatically trimmed at K=35 | Effective behavior recorded; not an untrimmed control |
| r05-auto-p100-main | 1080 Ti then P100 Main | Auto, no trim | Test head/MTP on faster-link HBM card, not assume x8 result transfers |

Reserve **700 MiB on physical P100 and 1600 MiB on physical 1080 Ti**, mapping first/later flags to card order. This is a starting safety policy, not proof of enough WDDM headroom; inspect actual free memory. Only change a reserve later as a named experiment. Pipeline is default/off in phase 1. The installed help confirms trim/pipeline/prefill-pipe; some reserve and split options are omitted from help but occur in the installed binary. Binary string presence is not behavioral validation: startup logs must establish effective reserves, split, draft placement and measured host transfer rates.

The runner stops after five completed screens. Check exact startup configuration, expert-cache counts/hit coverage, per-card PCIe probes, stage ranges, active MTP, prefill chunk sizes, VRAM/RAM/commit, temperatures/clocks and all errors before defining phase 2. Refuse silent drafter loss, target/context/precision change or automatic fallback as an equivalent candidate.

## Reviewed executable continuation

Initial five screens passed log/thermal review. Current continuation (`scripts/continue.py --run`) executes r06–r14: isolated P100 reserve 1400, then display reserve 2304 on trim32; trim28/36 neighbors; explicit reverse14 then reverse14+trim; safe trim32+mmap; safe trim32+prefill-pipe1; safe P100 reference. The initial auto1080Main arm already auto-trimmed at K=35, so no claim of auto-versus-trim isolation for it.

Then select by the stated preference score among reviewed candidates with observed headroom, execute candidate–P100–candidate confirmations, run standard plus ~230K actual-token smoke checks on candidate/reference, and produce a report/profile. No further planned idle checkpoint; pause on incomplete/error/thermal anomalies or missing eligible candidates. Pipeline, peer, PLE-in-RAM and unrelated parameter sweeps remain deferred with rationale. This is a targeted screen, not every possible flag combination.

## Phase 2 rationale: targeted placement and trim isolation

1. Re-run best auto order as a nearby control. Set an explicit split equal to its logged K **without trim**: isolate auto versus explicit behavior at the same placement.
2. Add `--trim-stage-weights` to that exact explicit profile: isolate reclaiming duplicate dense weights for expert-cache residency. All model layers remain active.
3. Try at most two neighboring boundaries around the strongest explicit split. K=28/32/36 is a reasonable initial bracket when P100 is first (32/16 was useful historically); center on observed cache coverage and stage balance rather than sweeping all 47 boundaries. If P100 is Main, use corresponding first-stage counts near 12/16/20, guided by its own auto result.
4. If order remains unresolved, compare the best reasoned reverse-order split with the same physical reserves. Do not assume the narrow-link card should always receive fewer layers: its compute, head/MTP cost and cache complement all matter.
5. If 1080 Ti merely makes prefill worse, retain P100-only as a valid winner; no obligation to use both cards.

## Phase 3: at most a few evidence-driven follow-ups

- **PLE I/O mode:** first 0.1.57 startup measured only 14556 random PLE rows/s in direct mode and warned about prompt stalls. This makes `--ple-io mmap` a worthwhile isolated follow-up after the direct-mode references, keeping weights, quality and workload fixed. Record first-touch versus warmed file-cache conditions; do not import the engine warning's other-machine speed estimates as results. `--ple-io ram` is deferred because the huge table would compete with the expert arena and available RAM/commit; no paging-prone attempt merely to test every flag.
- **Prefill/chunk balance:** only if logs show stage starvation or mismatched chunk counts, test `--prefill-pipe 1` alone against the selected placement; a fixed chunk only if observed workspace warrants it. Keep requested context fixed.
- **PCIe policy:** retain per-card automatic probes first. Do not force one `--pcie-frac` across unequal links without evidence. `STRATA_SPLIT_UNIFORM` appears in installed binary and current docs mention x16/x4, but require installed behavior/startup confirmation before an exploratory arm; explicit split is preferred to assuming newer auto rules apply.
- **Memory headroom:** adjust only the affected physical card's reserve after logging free VRAM, cache allocation and WDDM/commit. No headroom optimization that merely swaps OOM risk for a nominal speed gain.
- **Pipeline:** low priority and separately gated. Old 0.1.55 tests had non-finite/watchdog failures and slower safer variants. Newer online defaults do not prove 0.1.57 behavior. Only a fresh safety smoke and adequate reserve justify testing pipeline plus explicit draft placement as named, separate arms; never combine an untested pipeline with the primary placement screen.
- **Expert peer/cache helper instead of layer split:** not a default arm. Previous peer attempt OOM'd; chipset/DMI traffic and lack of proven P2P can make it worse. Only investigate if startup memory budgets and installed semantics support it and the main split fails to help. Do not repeat known failure blindly or change quality to force a fit.
- Do not sweep unrelated kernels, CPU workers, batch/concurrency, target precision, routing approximations, projection vectors or speculative/MTP settings. Keep inherited common CPU/PCIe-balance settings fixed for topology isolation.

## Exact workload and evidence

Every measured arm runs BetterBench:

```text
--quick --decode --categories code --prefill --no-concurrency --config <repo>/workloads/betterbench-16k.json
```

The JSON is `{"prefill_depths":[16384]}`: corpus target, not exactly 16384 model tokens. Preserve all JSON/HTML, actual token counts, five decode/eight prefill samples, failures, server/engine/bench logs, metrics and GPU telemetry. Quick mode is screening, not statistical significance or comprehensive quality proof. No speed estimates are accepted as measured improvements.

## Cooling / chipset controls

Hardware snapshot confirms P100 PCIe 3 x16 TCC and 1080 Ti PCIe 3 x4 WDDM. PnP paths are PEG1 versus RP21; chipset placement is consistent with user report. The 1080 Ti remains the display card. No NVLink or GPU peer-to-peer capability is assumed; pipeline uses host hand-offs. `nvidia-smi topo -m` is unsupported by this local Windows build; retain that limitation rather than inventing a topology matrix.

At start authorization the user confirms **open case, intake + exhaust, 75°C target, intake limited to 45% for noise**. This supersedes earlier intake-only/full-speed cooling records. Store that exact configuration in `--cooling-note`; no pooled comparison with earlier cooling runs. Do not mix fan configurations in this campaign. Record ambient if available, warm-up policy, both cards' temperatures/clocks, GPU/display load, throttle flags and PCIe width under load. Avoid unrelated chipset/SSD/network traffic; native model/expert and PLE reads may share the chipset path. No fan/clock/voltage/power/page-file changes by the runner. Captured power limits are 250 W P100 and 280 W 1080 Ti. Existing page file is 18 GiB; watch RAM+commit during dual loading rather than interpreting every allocation failure as VRAM or modifying Windows automatically.

## Confirmation and finish

After review, explicitly define candidate–P100 reference–candidate nearby confirmations on the same software/model/workload, plus a nearby noncandidate dual control if needed. At least two winner repeats; add more only to resolve unstable rankings. Run functional/tool/32K/~119K-token recall smoke checks on the candidate and full-quality reference before recommendation, plus an explicit above-128K actual-token recall/functional smoke (target approximately 220K–240K prompt tokens with response headroom) to exercise the requested 256K allocation. Standard shared sanity checks alone do not validate 256K context. Retain actual prompt usage; never execute generated code. These checks are not intelligence equivalence.

Offer separate private/shareable ready profile and launcher only after memory/thermal/error review. Stop only owned test processes, leave installed profiles untouched, mark completion in state/manifest/report and index. Do not transfer a result to two P100s or CPU x8+x8 without a new campaign.
