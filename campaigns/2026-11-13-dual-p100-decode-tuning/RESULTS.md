# Dual P100 tuning — live results

Complete: 10 valid benchmarks and 2 reviewed exclusions. Valid main arms: IQ3_S, 256K, int8 KV, full experts, no projection. Excluded first attempts retained projection/old split via user_args and are not comparison evidence; their raw results remain unchanged.

| Run | Phase | Decode | Prefill |
|---|---|---:|---:|
| reference36 | invalid (reviewed exclusion) | 31.436827313864768 | 343.72977598254954 |
| split24 | invalid (reviewed exclusion) | 32.04270118639572 | 344.29734283501 |
| reference36-v2 | complete | 32.042130340988265 | 345.8690226763893 |
| split24-v2 | complete | 40.627621740615794 | 347.36539131087636 |
| split24-pipeline | complete | 43.59908542205952 | 346.8594284727494 |
| split24-downws | complete | 41.07693897509102 | 345.33360576285963 |
| split24-pin0 | complete | 39.5825920695818 | 377.6723813702339 |
| split24-pipeline-stage0 | complete | 40.32768251685596 | 346.2290688458261 |
| split24-pipeline-stage0-pin0 | complete | 41.476136386416265 | 378.0051627217048 |
| confirm-candidate-a | complete | 44.659921319096064 | 347.25855020661766 |
| confirm-reference | complete | 31.695759820091894 | 345.8863254932925 |
| confirm-candidate-b | complete | 47.63166003126275 | 347.5713244216135 |
