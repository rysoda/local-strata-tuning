"""Offline checks for cooling telemetry math; never launch a workload."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[2] / 'campaigns/2026-11-03-p100-open-case-cooling/scripts/monitor_power.py'
SPEC = importlib.util.spec_from_file_location('power_monitor', PATH)
monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(monitor)


class PowerMonitorTests(unittest.TestCase):
    def test_irregular_samples_and_final_interval(self):
        rows = [dict(elapsed_seconds=t, power_w=p, temperature_c=80,
                     utilization_percent=100, sm_clock_mhz=1200)
                for t, p in [(0, 100), (1, 200), (4, 300)]]
        result = monitor.summary(rows, 10)
        self.assertEqual(result['average_power_w'], 250)
        self.assertAlmostEqual(result['energy_wh'], 2500 / 3600)
        self.assertEqual(result['max_sample_gap_seconds'], 6)

    def test_empty_result(self):
        self.assertIsNone(monitor.summary([], 0)['average_power_w'])

    def test_optional_unavailable(self):
        row = dict(elapsed_seconds=0, power_w=150, temperature_c=None,
                   utilization_percent=None, sm_clock_mhz=None)
        result = monitor.summary([row], 5)
        self.assertEqual(result['average_power_w'], 150)
        self.assertIsNone(result['average_temperature_c'])
        self.assertIsNone(result['max_temperature_c'])

    def test_invalid_telemetry(self):
        for value in ['N/A', '[Not Supported]', 'NaN', 'inf']:
            self.assertIsNone(monitor.number(value))


if __name__ == '__main__':
    unittest.main()
