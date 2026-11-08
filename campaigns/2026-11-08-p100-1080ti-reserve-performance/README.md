# VRAM reserve performance optimum

**Complete.** Tested recommendation: **640/896 MiB**.

[Final report](REPORT.md) · [Every run](RESULTS.md) · [Plan](PLAN.md) · [Manifest](manifest.json) · [Work log](NOTES.md)

## My conclusion

**I recommend 640 MiB on the P100 and 896 MiB on the 1080 Ti.** It is the best-supported tested balance: nearby confirmations improved both decode and prefill, with more reserve headroom than 512/512. Minimizing reserve to zero was the wrong performance objective because it substantially hurt prefill. The useful result is a balanced reserve, not maximum VRAM occupancy.

| Setting / measurement | Before | After | Change |
|---|---:|---:|---:|
| P100 / 1080 Ti reserve (MiB) | 1400 / 2304 | **640 / 896** | −760 / −1408 |
| Decode (tok/s) | 37.49 | **38.86** | **+3.65%** |
| Prefill (tok/s) | 325.98 | **331.35** | **+1.65%** |

Speeds are means of three per-run medians from alternating candidate/reference confirmations on the same exact BetterBench workload—not discovery maxima. The candidate passed both scheduled seven-check functional/tool/long-context smoke sets. These modest gains are useful but not statistically proven; decode fluctuated, and 512/512 had only one joint screen, so this is not proof of an absolute optimum. Model, full expert routing, 256K context, int8 KV and reasoning settings stayed fixed. No generated code was executed.

The table is **projection-free benchmark evidence**. Startup retains the user's existing experimental projection; its performance and quality are not established by this comparison.

**Startup updated after completion, by user request:** P100 reserve640 MiB / 1080 Ti reserve896 MiB. Existing256K settings and experimental projection retained; projection-enabled performance was not validated by this campaign. [Deployment record](STARTUP_UPDATE.md). Completed runner refuses new work.
