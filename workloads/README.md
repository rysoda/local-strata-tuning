# Benchmark workloads

[Campaign index](../README.md)

[betterbench-16k.json](betterbench-16k.json) is the original `16k.json`, unchanged:

```json
{"prefill_depths": [16384]}
```

Use with BetterBench `--quick --decode --categories code --prefill --no-concurrency`. Preserve its normal sample counts, corpus and sampling; retain actual token lengths. This is a 16K corpus target, not necessarily 16384 model-token prefill (the tested model sees roughly 12K).

All three migrated campaigns used this workload. If future work needs another depth or workload, add a separately named config and reference it from that campaign's manifest; do not silently change this shared historical definition.
