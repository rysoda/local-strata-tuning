"""Synthetic tests only; no GPU queries, server or measurements."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('cooling_report', HERE / 'report.py')
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)
spec = importlib.util.spec_from_file_location('cooling_capture', HERE / 'capture.py')
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


class ReportingTests(unittest.TestCase):
    def rows(self):
        return [dict(elapsed_seconds=t, temperature_c=v, sm_clock_mhz=v * 10,
                     power_w=v * 2, utilization_percent=100) for t, v in [(0, 60), (1, 70), (3, 80)]]

    def test_weighted_mean_and_final_interval(self):
        m = report.metrics(self.rows(), 4)
        self.assertEqual(m['temperature_c']['mean'], 70)
        self.assertEqual(m['temperature_c']['max'], 80)
        self.assertEqual(m['sm_clock_mhz']['max'], 800)
        self.assertEqual(m['max_gap_s'], 2)
        self.assertAlmostEqual(m['energy_wh'], 140 * 4 / 3600)

    def test_missing_values_refused(self):
        rows = self.rows()
        rows[0]['temperature_c'] = 'nan'
        with self.assertRaises(ValueError):
            report.metrics(rows, 4)

    def test_six_run_report_and_partial_exclusion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'results').mkdir()
            (root / 'state').mkdir()
            runs = {'partial-attempt': {'status': 'failed'}}
            for group in ('intake', 'intake-exhaust'):
                for i in range(1, 4):
                    label = f'{group}-{i}'
                    name = label + '.csv'
                    with (root / 'results' / name).open('w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=self.rows()[0].keys())
                        writer.writeheader()
                        writer.writerows(self.rows())
                    result = f'results/{label}.json'
                    (root / result).write_text(json.dumps(dict(status='complete', duration_seconds=4, csv_file=name)))
                    runs[label] = dict(status='complete', group=group, result=result)
            (root / 'state/queue-state.json').write_text(json.dumps(dict(runs=runs)))
            with patch.object(report, 'ROOT', root):
                report.main()
            text = (root / 'REPORT.md').read_text(encoding='utf-8')
            self.assertIn('**6/6**', text)
            self.assertNotIn('Pending three', text)
            self.assertEqual(len(json.loads((root / 'results/analysis.json').read_text())), 6)

    def test_completed_group_starts_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'state.json'
            state.write_text(json.dumps(dict(phase='complete', runs={f'intake-{i}': dict(status='complete') for i in range(1, 4)})))
            argv = ['capture.py', 'intake', '--ready', '--warmup-minutes', '5', '--workload', 'synthetic', '--setup-notes', 'synthetic']
            with patch.object(capture, 'STATE', state), patch('sys.argv', argv), patch.object(capture, 'preflight', side_effect=AssertionError('must not query')):
                capture.main()

    def test_both_fans_first_order_and_hold(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'state').mkdir()
            state = root / 'state/queue-state.json'
            state.write_text(json.dumps(dict(phase='planned', runs={})))
            (root / 'manifest.json').write_text(json.dumps(dict(capture_order=['intake-exhaust', 'intake'])))
            (root / 'state/STOP').write_text('hold')
            for group, message in [('intake', 'Complete the three intake-exhaust'), ('intake-exhaust', 'STOP flag present')]:
                argv = ['capture.py', group, '--ready', '--warmup-minutes', '15', '--workload', 'synthetic', '--setup-notes', 'synthetic']
                with patch.object(capture, 'ROOT', root), patch.object(capture, 'STATE', state), patch('sys.argv', argv):
                    with self.assertRaisesRegex(SystemExit, message):
                        capture.main()

    def test_incomplete_attempt_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'state.json'
            state.write_text(json.dumps(dict(phase='running', runs={})))
            argv = ['capture.py', 'intake', '--ready', '--warmup-minutes', '5', '--workload', 'synthetic', '--setup-notes', 'synthetic']
            with patch.object(capture, 'STATE', state), patch('sys.argv', argv):
                with self.assertRaises(SystemExit):
                    capture.main()


if __name__ == '__main__':
    unittest.main()
