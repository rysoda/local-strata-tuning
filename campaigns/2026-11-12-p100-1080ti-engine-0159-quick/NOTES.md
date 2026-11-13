# Work log

## 2026-11-12 preflight

Read repository index/layout/tools docs and latest reserve-performance README/report/manifest/work log; reviewed prior projected one-off runner/results. New campaign scaffold read before implementation. No report existed yet.

Actual user-owned engine PID5776 is 0.1.59 CUDA12, Control0.1.57 API PID4748 on port8080. P100 GPU0 PCIe3 x16, 1080Ti GPU1 PCIe3 x4, driver582.66. User server has 256K, int8, MTP, full experts, split36, trim, reserves640/896, experimental projection. Do not kill these user processes. No other BetterBench/queue found. Unrelated preexisting working-tree modifications and quick-benches/ left untouched.

Implemented read-only existing-server diagnostic runner, no engine management. Retains projection as found; this is not a full-quality reference comparison. Three requested runs only. State/STOP pauses between runs. `python campaigns/2026-11-12-p100-1080ti-engine-0159-quick/scripts/run.py` resumes only planned/paused state; failed/incomplete attempts require explicit review and preserved evidence. Complete state refuses repeats. User should avoid using API during measurements.

## Complete

All three runs completed validly: 15/15 decode and 24/24 prefill samples total. Means of run medians38.431 decode /329.728 prefill. Final report records both historical comparisons and confounders; no clear engine-caused improvement established. API confirmed0.1.59/262144/int8/project:4-44. Owned benchmark processes exited; user server left untouched and running. Repository validation passed14 campaigns/648 preserved artifacts/redaction/links. Completed supervisor cannot repeat the benchmarks.
