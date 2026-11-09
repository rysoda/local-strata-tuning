# ARCTIC P12 Pro — P100 cooling survey

Completed: 3/3 ten-minute captures.

Fan fixed at 100%, approximately 2900 RPM (user reported), continuing the extractor setup. Heat-soak duration after changing speed is unknown; initial settling is retained, not discarded. Fan RPM is not measured by NVIDIA telemetry. Ambient, case/shroud and exact stress settings unknown.

| Run | Temp mean/max °C | SM clock mean/max MHz | Board power mean W | GPU mean % |
| --- | --- | --- | --- | --- |
| p12-pro-100pct-1 | 65.13/66 | 1324.25/1328 | 191.37 | 99.71 |
| p12-pro-100pct-2 | 65.92/67 | 1324.34/1328 | 193.67 | 99.72 |
| p12-pro-100pct-3 | 66.02/67 | 1323.70/1328 | 194.91 | 99.77 |

p12-pro-100pct-1: 456 samples; max gap 1.36s; throttle-active percentages: {"sw_power_cap": 14.505333333332752, "sw_thermal_slowdown": 0.0, "hw_thermal_slowdown": 0.0, "hw_power_brake_slowdown": 0.0}.


p12-pro-100pct-2: 441 samples; max gap 1.48s; throttle-active percentages: {"sw_power_cap": 17.049499999999775, "sw_thermal_slowdown": 0.0, "hw_thermal_slowdown": 0.0, "hw_power_brake_slowdown": 0.0}.


p12-pro-100pct-3: 426 samples; max gap 1.47s; throttle-active percentages: {"sw_power_cap": 19.580499999998967, "sw_thermal_slowdown": 0.0, "hw_thermal_slowdown": 0.0, "hw_power_brake_slowdown": 0.0}.


CSV/JSON under results retain all samples, min/max/SD, memory clocks/utilization/usage, P-state, power limit and power/thermal throttle flags. Means and flag percentages use time-weighted sample-and-hold; extrema are sampled, not continuous. External fan power excluded. Three sequential runs are not independent controlled trials; no inference-speed or quality claim, nor controlled comparison with historical fans. User-managed workload/server left untouched.

## Comparison and interpretation

See [findings and 70% comparison](README.md). Independent CSV throttle checks passed; original reference hashes unchanged.
