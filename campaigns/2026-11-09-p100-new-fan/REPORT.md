# ARCTIC P12 Pro — P100 cooling survey

**This report retains the original 70% survey.** Subsequent [100% / ~2900 RPM findings](../2026-11-09-p100-p12-pro-full-speed/README.md): three more ten-minute runs averaged **65.69°C / 1324.09 MHz / 193.32 W**, peak **67°C**. Versus this 70% group: **−8.09°C**, **+4.89 MHz (+0.37%)**, **−3.22 W**. All six setups/all 17 runs are in the [comparison README](README.md). Original raw files and completed 70% checkpoint remain unchanged; separate full-speed state preserves the additional work. Historical, sequential-order, ambient and initial-settling caveats apply.

Completed: 3/3 ten-minute captures.

Fan fixed at 70%, approximately 2230 RPM; heat soaked (user reported). Fan RPM is not measured by NVIDIA telemetry. Ambient, case/shroud and exact stress settings unknown.

| Run | Temp mean/max °C | SM clock mean/max MHz | Board power mean W | GPU mean % |
| --- | --- | --- | --- | --- |
| p12-pro-70pct-1 | 73.62/74 | 1318.82/1328 | 195.37 | 99.67 |
| p12-pro-70pct-2 | 73.94/75 | 1319.06/1328 | 196.64 | 99.71 |
| p12-pro-70pct-3 | 73.77/75 | 1319.74/1328 | 197.62 | 99.47 |

p12-pro-70pct-1: 505 samples; max gap 1.23s; throttle-active percentages: {"sw_power_cap": 20.82866666666617, "sw_thermal_slowdown": 0.0, "hw_thermal_slowdown": 0.0, "hw_power_brake_slowdown": 0.0}.


p12-pro-70pct-2: 490 samples; max gap 1.27s; throttle-active percentages: {"sw_power_cap": 19.007833333333412, "sw_thermal_slowdown": 0.0, "hw_thermal_slowdown": 0.0, "hw_power_brake_slowdown": 0.0}.


p12-pro-70pct-3: 473 samples; max gap 1.33s; throttle-active percentages: {"sw_power_cap": 19.02483333333339, "sw_thermal_slowdown": 0.0, "hw_thermal_slowdown": 0.0, "hw_power_brake_slowdown": 0.0}.


CSV/JSON under results retain all samples, min/max/SD, memory clocks/utilization/usage, P-state, power limit and power/thermal throttle flags. Means and flag percentages use time-weighted sample-and-hold; extrema are sampled, not continuous. External fan power excluded. Three sequential runs are not independent controlled trials; no inference-speed or quality claim, nor controlled comparison with historical fans. User-managed workload/server left untouched.
