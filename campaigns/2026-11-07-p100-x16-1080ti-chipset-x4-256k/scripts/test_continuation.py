"""Offline continuation safety/profile tests; no inference or measurements."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('continuation', HERE / 'continue.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ContinuationTests(unittest.TestCase):
    def test_ids_and_quality(self):
        items = m.core.INITIAL + m.FOLLOWUPS
        self.assertEqual(len(items), len({i['id'] for i in items}))
        for item in m.FOLLOWUPS:
            cfg = m.core.build(item)
            a = cfg['args']
            self.assertEqual(a[a.index('--max-context') + 1], '262144')
            self.assertEqual(a[a.index('--kv') + 1], 'int8')
            self.assertEqual(a[a.index('--kv-resident') + 1], '32768')
            self.assertEqual(cfg['drafting'], 'mtp')
            self.assertNotIn('--pipeline-windows', a)
            self.assertNotIn('--peer-device', a)
            self.assertEqual(cfg['env']['STRATA_ROUTE_TAIL_SKIP'], '0')

    def test_new_physical_reserves(self):
        for item in m.FOLLOWUPS[1:]:
            cfg = m.core.build(item)
            cards = cfg['gpu'] if isinstance(cfg['gpu'], list) else [cfg['gpu']]
            reserves = {0: '1400', 1: '2304'}
            a = cfg['args']
            self.assertEqual(a[a.index('--vram-reserve-mib') + 1], reserves[cards[0]])
            if len(cards) == 2:
                self.assertEqual(a[a.index('--vram-reserve-later-mib') + 1], reserves[cards[-1]])

    def test_sanity_redirect_and_normal_delegation(self):
        proxy = m.ProcessTools()
        with patch.object(m.subprocess, 'run') as runner:
            proxy.run(['python', str(m.core.REPO / 'tools/sanity.py'), 'config', 'output'])
            self.assertEqual(Path(runner.call_args.args[0][1]), HERE / 'sanity_combo.py')
            proxy.run(['taskkill', '/PID', '1'])
            self.assertEqual(runner.call_args.args[0][0], 'taskkill')
        self.assertTrue((HERE.parents[2] / 'tools/sanity.py').is_file())

    def test_default_never_launches(self):
        with patch('sys.argv', ['continue.py']), patch.object(m.core, 'check') as check, patch.object(m.bench, 'run_one', side_effect=AssertionError('must not launch')):
            m.main()
            check.assert_called_once()

    def test_recorded_initial_logs_review(self):
        reviews = [m.review(i) for i in m.core.INITIAL]
        self.assertTrue(reviews[3]['auto_trim'])
        self.assertFalse(reviews[0]['auto_trim'])


if __name__ == '__main__':
    unittest.main()
