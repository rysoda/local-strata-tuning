"""Synthetic safety/profile tests; never launch inference or benchmark."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('retune', HERE / 'run.py')
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
BASE = json.loads((run.ROOT / 'configs/shareable/baseline.json').read_text())


class PlanTests(unittest.TestCase):
    def test_all_profiles_retain_quality(self):
        for item in run.INITIAL:
            with patch.object(run, 'read', side_effect=lambda p: copy.deepcopy(BASE)):
                cfg = run.build(item)
            self.assertEqual(cfg['args'][cfg['args'].index('--max-context') + 1], '262144')
            self.assertEqual(cfg['args'][cfg['args'].index('--kv') + 1], 'int8')
            self.assertEqual(cfg['args'][cfg['args'].index('--kv-resident') + 1], '32768')
            self.assertEqual(cfg['drafting'], 'mtp')
            self.assertEqual(cfg['host'], '127.0.0.1')
            self.assertFalse(any('control-vector' in a or 'cvec' in a for a in cfg['args']))
            self.assertNotIn('user_args', cfg)
            self.assertEqual(cfg['gpu_order'], 'as_given')

    def test_reserves_follow_physical_card_not_stage(self):
        for item in run.INITIAL:
            with patch.object(run, 'read', side_effect=lambda p: copy.deepcopy(BASE)):
                cfg = run.build(item)
            cards = cfg['gpu'] if isinstance(cfg['gpu'], list) else [cfg['gpu']]
            self.assertEqual(cfg['args'][cfg['args'].index('--vram-reserve-mib') + 1], '700' if cards[0] == 0 else '1600')
            if len(cards) == 2:
                self.assertEqual(cfg['args'][cfg['args'].index('--vram-reserve-later-mib') + 1], '700' if cards[-1] == 0 else '1600')
            else:
                self.assertNotIn('layer_split', cfg)

    def test_default_is_check_only(self):
        with patch('sys.argv', ['run.py']), patch.object(run, 'check') as check, patch.object(run.bench, 'run_one', side_effect=AssertionError('must not run')):
            run.main()
            check.assert_called_once()

    def test_completed_initial_queue_is_noop(self):
        state = dict(phase='initial-screening-complete-review-required', runs={})
        with patch('sys.argv', ['run.py', '--run-initial', '--cooling-note', 'synthetic']), patch.object(run, 'read', return_value=state), patch.object(run, 'check', side_effect=AssertionError('must not run')):
            run.main()

    def test_incomplete_state_refuses(self):
        state = dict(phase='running', runs={'r01-quality-reference-layout': dict(phase='loading')})
        with patch('sys.argv', ['run.py', '--run-initial', '--cooling-note', 'synthetic']), patch.object(run, 'read', return_value=state):
            with self.assertRaises(SystemExit):
                run.main()

    def test_check_cannot_be_combined_with_launch(self):
        with patch('sys.argv', ['run.py', '--check', '--run-initial', '--cooling-note', 'synthetic']):
            with self.assertRaises(SystemExit):
                run.main()

    def test_explicit_cooling_declaration_required(self):
        with patch('sys.argv', ['run.py', '--run-initial']):
            with self.assertRaises(SystemExit):
                run.main()


if __name__ == '__main__':
    unittest.main()
