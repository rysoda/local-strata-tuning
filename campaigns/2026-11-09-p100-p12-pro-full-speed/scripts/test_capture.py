"""Offline safety/statistics regression tests; never touches live campaign state."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('full_speed_capture', Path(__file__).with_name('capture.py'))
capture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'state').mkdir()
        (self.root / 'results').mkdir()
        self.patch = patch.multiple(capture, ROOT=self.root, STATE=self.root/'state/queue-state.json', LOCK=self.root/'state/capture.lock')
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def state(self, phase, runs=None):
        capture.save(capture.STATE, dict(phase=phase, current=None, runs=runs or {}))

    def test_completed_is_noop(self):
        self.state('complete', {'existing': {'status': 'complete'}})
        before = capture.STATE.read_bytes()
        with patch.object(capture, 'preflight', side_effect=AssertionError('must not inspect or launch')):
            capture.main()
        self.assertEqual(before, capture.STATE.read_bytes())

    def test_incomplete_refuses_without_modifying_state(self):
        self.state('running', {'existing': {'status': 'running'}})
        before = capture.STATE.read_bytes()
        with self.assertRaises(SystemExit):
            capture.main()
        self.assertEqual(before, capture.STATE.read_bytes())

    def test_stop_refuses_before_preflight(self):
        self.state('planned')
        (self.root/'state/STOP').touch()
        with patch.object(capture, 'preflight', side_effect=AssertionError('must not run')):
            with self.assertRaises(SystemExit):
                capture.main()

    def test_failure_pauses_and_removes_owned_lock(self):
        self.state('planned')
        with patch.object(capture, 'preflight', side_effect=RuntimeError('test failure')):
            with self.assertRaisesRegex(RuntimeError, 'test failure'):
                capture.main()
        self.assertEqual(json.loads(capture.STATE.read_text())['phase'], 'error')
        self.assertFalse(capture.LOCK.exists())

    def test_capture_preserves_label_and_time_weighted_metrics(self):
        def sample(temp):
            row = {key: 0.0 for key in capture.KEYS[:8]}
            row.update(temperature_c=temp, power_w=200.0, sm_clock_mhz=1328.0, pstate='P0')
            row.update({key: 'Not Active' for key in capture.KEYS[9:]})
            return row
        with patch.object(capture, 'query', side_effect=[sample(64), sample(65)]), \
             patch.object(capture.time, 'monotonic', side_effect=[0,0,1,1,600,600,600]), \
             patch.object(capture.time, 'sleep'):
            path = self.root / capture.capture('p12-pro-100pct-test')
        result = json.loads(path.read_text())
        self.assertIn('p12-pro-100pct-test', path.name)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['duration_seconds'], 600)
        self.assertEqual(result['sample_count'], 2)
        self.assertEqual(result['metrics']['temperature_c']['mean'], 64)
        self.assertEqual(result['metrics']['temperature_c']['max'], 65)
        self.assertAlmostEqual(result['energy_wh'], 200/6)
        self.assertTrue(all(v == 0 for v in result['throttle_active_percent'].values()))


if __name__ == '__main__':
    unittest.main()
