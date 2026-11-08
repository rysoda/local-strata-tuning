"""Offline tests; never start an engine."""
import copy
import unittest
from unittest.mock import patch
import run as r


class PerformanceTests(unittest.TestCase):
    def test_prefill_gate(self):
        s = dict(runs={'a': {'metrics': dict(decode=45, prefill=260)}, 'b': {'metrics': dict(decode=39, prefill=325)}}, outcomes={'a': {'accepted': True}, 'b': {'accepted': True}})
        ranked = r.rank(s, {(0, 0): ['a'], (512, 512): ['b']}, dict(decode=37, prefill=325))
        self.assertEqual(ranked[0]['pair'], [512, 512])

    def test_headroom_tie(self):
        s = dict(runs={k: {'metrics': dict(decode=39, prefill=325)} for k in ('a', 'b')}, outcomes={k: {'accepted': True} for k in ('a', 'b')})
        self.assertEqual(r.rank(s, {(384, 512): ['a'], (640, 512): ['b']}, dict(decode=37, prefill=325))[0]['pair'], [640, 512])

    def test_complete_pipeline_and_resume(self):
        s = dict(phase='planned', runs={}, definitions={}, outcomes={})
        seen = set()
        def fake(state, active, p, t, label, sanity=False):
            if label in state['outcomes']:
                return True
            self.assertNotIn(label, seen)
            seen.add(label)
            d = 40 - abs(p-512)/1500 - abs(t-512)/2500
            state['runs'][label] = dict(phase='complete', metrics=dict(decode=d, prefill=325))
            if sanity:
                state['runs'][label]['sanity'] = dict(passed=7, total=7)
            state['outcomes'][label] = dict(accepted=True)
            return True
        with patch.object(r, 'run', side_effect=fake), patch.object(r, 'checkpoint'), patch.object(r, 'report'), patch.object(r, 'finish') as finish:
            r.campaign(s, {})
            first = len(seen)
            self.assertLessEqual(first, 46)
            self.assertGreaterEqual(first, 40)
            self.assertIn('joint-p512-t512', seen)
            self.assertEqual(len(s['confirmation_labels']), 6)
            finish.assert_called_once()
            self.assertTrue(s['confirmation_summary']['accepted'])
            r.campaign(s, {})
            self.assertEqual(len(seen), first)

    def test_projection_free_profiles(self):
        cfg = r.m.config(512, 512, 'unit-offline')
        self.assertNotIn('--control-vector-scaled', cfg['args'])
        self.assertEqual(cfg['args'][cfg['args'].index('--max-context')+1], '262144')
        self.assertEqual(cfg['args'][cfg['args'].index('--vram-reserve-mib')+1], '512')
        self.assertEqual(cfg['args'][cfg['args'].index('--vram-reserve-later-mib')+1], '512')


if __name__ == '__main__':
    unittest.main()
