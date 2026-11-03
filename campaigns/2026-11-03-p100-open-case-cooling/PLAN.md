# P100 open case cooling — measurement plan

## Boundary and baseline

New P100-only cooling comparison; do not resume the completed inference campaigns. User already runs Strata and a prefill stress test. Monitor only, never launch/stop workloads or change settings. Capture engine/model/workload, driver, fixed power limit, inlet temperature and fan/duct setup before interpreting results. Installed version/configuration is not inferred from previous campaigns.

## Candidates and method

Airflow A is the baseline, B and C are user-defined physical changes. Use the same sustained workload and allow thermal equilibrium before each 600-second run. Log power, temperature, utilization and SM clocks using locally verified NVIDIA query fields. Power is a thermal proxy only while load and thermal throttling are comparable; at a common power ceiling use temperature/clocks too. No precision, routing, context, power limit or clock changes.

Use the time-weighted sample-and-hold power mean, retain raw samples and all failed/partial runs, and repeat in reversed order. Record ambient conditions. No BetterBench comparison, inference recommendation or generated-code execution is part of this user-requested thermal experiment. The existing repository BetterBench workload is not substituted for the user's stress test.

## Confirmation

Review utilization and temperature trends, sampling gaps and constant power limit before ranking. Repeat the apparent winner against A under similar ambient conditions. Do not claim statistical significance, calibrated calorimetry, speed improvement or model-quality equivalence from these measurements.
