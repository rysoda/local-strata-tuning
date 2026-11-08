"""Synthetic boundary/profile tests. No inference, probes or GPU allocations."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('reserve_runner', HERE / 'run.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReserveTests(unittest.TestCase):
    def test_zero_floor(self):
        calls = []
        self.assertEqual(m.descend(1400, lambda x: calls.append(x) or True), 0)
        self.assertIn(0, calls)
        self.assertTrue(all(x >= 0 for x in calls))

    def test_integer_boundary_refinement(self):
        calls = []
        self.assertEqual(m.descend(1400, lambda x: calls.append(x) or x >= 301), 301)
        self.assertIn(300, calls)
        self.assertIn(301, calls)
        self.assertEqual(len(calls), len(set(calls)))

    def test_above_700_boundary(self):
        self.assertEqual(m.descend(2304, lambda x: x >= 918), 918)

    def test_profiles_keep_quality_and_zero(self):
        cfg = m.config(0, 0, 'synthetic')
        a = cfg['args']
        self.assertEqual(a[a.index('--vram-reserve-mib') + 1], '0')
        self.assertEqual(a[a.index('--vram-reserve-later-mib') + 1], '0')
        self.assertEqual(a.count('--vram-reserve-mib'), 1)
        self.assertEqual(a.count('--trim-stage-weights'), 1)
        self.assertEqual(a[a.index('--max-context') + 1], '262144')
        self.assertEqual(a[a.index('--kv') + 1], 'int8')
        self.assertEqual(cfg['layer_split'], '36')
        self.assertFalse(any('cvec' in x or 'control-vector' in x for x in a))
        with self.assertRaises(ValueError):
            m.config(-1, 0, 'bad')

    def test_existing_projection_is_separate(self):
        cfg = m.config(256, 700, 'projected', projection=True)
        a = cfg['args']
        self.assertIn('--control-vector-scaled', a)
        self.assertEqual(a[a.index('--cvec-mode') + 1], 'project')
        self.assertEqual(a[a.index('--max-context') + 1], '262144')

    def test_expected_allocation_preserves_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'results').mkdir()
            (root / 'results/trial.engine.log').write_text('fatal : Memory allocation failure')
            state = dict(runs={'trial': dict(phase='failed', error='server exited')})
            with patch.object(m, 'ROOT', root):
                outcome = m.inspect('trial', {}, state, {})
            self.assertFalse(outcome['accepted'])
            self.assertEqual(state['runs']['trial']['phase'], 'failed')
            self.assertTrue(state['runs']['trial']['reviewed_skip'])

    def test_unexpected_failure_pauses(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'results').mkdir()
            (root / 'results/trial.engine.log').write_text('non-finite logits')
            state = dict(runs={'trial': dict(phase='failed')})
            with patch.object(m, 'ROOT', root):
                with self.assertRaises(RuntimeError):
                    m.inspect('trial', {}, state, {})

    def test_default_is_nonexecuting(self):
        with patch('sys.argv', ['run.py']), patch.object(m, 'check') as check, patch.object(m.bench, 'run_one', side_effect=AssertionError('must not launch')):
            m.main()
            check.assert_called_once()


if __name__ == '__main__':
    unittest.main()
