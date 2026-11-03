# Closed-case shroud cooling — work log

## Measurements: 2026-11-03

- User collected 11 ten-minute runs: auxiliary fan off three times (first suspected insufficiently warmed up), and 25%, 50%, 75%, 100% twice each.
- User confirmed closed case, fan shroud and a second fan at the shroud edge drawing outside air inward. Off means the auxiliary fan is not running, not necessarily physically removed. Primary-fan details, RPM and ambient conditions were not saved.
- Actual UTC order: 19:17 off, 19:27 off/1bis, 19:37 100%, 19:48 75%, 20:00 50%, 20:17 25%, 20:32 off/2, 20:44 25%, 21:02 50%, 21:17 75%, 21:28 100%.

## Separation and completed review

- Created this named campaign at the user's request to separate closed-case/shroud evidence from the open-case unducted measurements. Moved all 22 raw CSV/JSON files without changing bytes or names; checked SHA-256 before and after and saved the relocation inventory in results/relocation-sha256.json. Earlier open-case evidence and original planning state remain untouched.
- Recomputed all 11 runs' power, temperature, utilization and SM-clock means from CSV: agreement with JSON within 1e-6. All completed 600 seconds without errors on the same P100 UUID, with a constant 250 W power limit. Inspected final-five-minute power; README records the results and limitations.
- Balanced off reference (1bis + 2): 162.81 W / 1199.9 MHz. Including the possible warm-up run: 163.20 W / 1201.4 MHz. Enabled auxiliary fan means: 25% 158.63 W, 50% 151.61 W, 75% 148.20 W, 100% 149.14 W. Temperatures approximately 79°C throughout.
- Provisional recommendation: auxiliary outside-air intake off in this exact arrangement. No measured inference-speed/efficiency or comprehensive quality claim. No deployment profile created or inference recommendation changed.
- Updated root index and open-case navigation. No process, monitor, benchmark, inference server or workload was started/stopped, and no hardware/software settings changed. There are no owned processes or automatic queues to resume. Checkpoint marks the telemetry review complete, with measurements distinguished from BetterBench benchmarks.
