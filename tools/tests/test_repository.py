"""No-inference regression checks for the campaign layout and shared tools."""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import runpy
import sys
import tempfile
import unittest
import urllib.request
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools import launch, new_campaign, publish_configs, validate_repository


class LayoutTests(unittest.TestCase):
    def test_evidence_manifests_links_and_redaction(self):
        validate_repository.validate()

    def test_redacts_nested_credentials_without_altering_settings(self):
        source = {'api_key': 'private-key', 'env': {'nested': [{'password': 'secret'}]}, 'args': ['--spec', '4']}
        result = publish_configs.redact(source)
        self.assertEqual(result['api_key'], '<REDACTED>')
        self.assertEqual(result['env']['nested'][0]['password'], '<REDACTED>')
        self.assertEqual(result['args'], source['args'])
        self.assertEqual(source['api_key'], 'private-key')

    def test_new_campaign_is_planned_not_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = pathlib.Path(directory)
            root = new_campaign.create('2026-12-01-test-card', 'A "quoted" title', parent)
            manifest = json.loads((root/'manifest.json').read_text())
            self.assertEqual(manifest['title'], 'A "quoted" title')
            self.assertEqual(manifest['status'], 'planned')
            self.assertIsNone(manifest['resume_script'])
            self.assertEqual(json.loads((root/'state/queue-state.json').read_text())['phase'], 'planned')
            self.assertFalse(list((root/'scripts').iterdir()))
            self.assertTrue((root/'configs/private').is_dir())
            self.assertNotIn('{{id}}', (root/'README.md').read_text())
            with self.assertRaises(FileExistsError):
                new_campaign.create(root.name, 'Do not overwrite', parent)
            with self.assertRaises(ValueError):
                new_campaign.create('../unsafe', 'Unsafe', parent)

    def test_private_and_runtime_files_are_ignored(self):
        patterns = (REPO/'.gitignore').read_text()
        self.assertIn('/campaigns/*/configs/private/', patterns)
        self.assertIn('/campaigns/*/state/*.lock', patterns)
        self.assertIn('/campaigns/*/state/STOP*', patterns)

    def test_launch_check_uses_redacted_fallback_without_process_or_write(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = pathlib.Path(directory)
            root = repo/'campaigns/test-campaign'
            shared = root/'configs/shareable'
            shared.mkdir(parents=True)
            control = repo/'installed/control'
            (control/'serve').mkdir(parents=True)
            (control/'python').mkdir()
            (control/'serve/server.py').touch()
            (control/'python/python.exe').touch()
            exe = repo/'installed/strata.exe'
            exe.touch()
            (root/'manifest.json').write_text(json.dumps({'recommended_profile': 'recommended.json'}))
            (shared/'recommended.json').write_text(json.dumps({'api_key': '<REDACTED>', 'exe': str(exe), 'cwd': str(control)}))
            with mock.patch.object(launch, 'REPO', repo), mock.patch.dict(os.environ, {'STRATA_API_KEY': 'test-only-key', 'LOCALAPPDATA': str(repo)}), mock.patch.object(sys, 'argv', ['launch.py', 'test-campaign', '--check']), mock.patch.object(launch.subprocess, 'call', side_effect=AssertionError('No processes allowed')), mock.patch.object(launch.socket, 'socket', side_effect=AssertionError('No network allowed')):
                self.assertEqual(launch.main(), 0)
                _, _, cfg = launch.resolve('test-campaign')
                self.assertEqual(cfg['api_key'], 'test-only-key')
                self.assertEqual(cfg['host'], '127.0.0.1')
                self.assertEqual(pathlib.Path(cfg['log']).parent, root/'results')
            self.assertFalse((root/'configs/private').exists())

    @unittest.skipUnless(os.name == 'nt', 'Legacy campaign supervisors use Windows msvcrt')
    def test_completed_supervisors_do_not_start_processes_or_network(self):
        paths = [
            '2026-10-28-1080ti-tuning/scripts/tune.py',
            '2026-10-28-1080ti-tuning/scripts/run_combined.py',
            '2026-10-28-1080ti-tuning/scripts/start_baseline.py',
            '2026-10-28-1080ti-tuning/scripts/run_baseline.py',
            '2026-11-01-p100-1080ti-x16-x4/scripts/run.py',
            '2026-11-02-p100-1080ti-x8-x8/scripts/run.py',
        ]
        for relative in paths:
            script = REPO/'campaigns'/relative
            with self.subTest(script=relative), contextlib.ExitStack() as stack:
                stack.enter_context(mock.patch.object(sys, 'path', [str(script.parent)]+sys.path))
                for target in ('subprocess.Popen', 'subprocess.call', 'subprocess.run', 'subprocess.check_output', 'socket.socket', 'urllib.request.urlopen'):
                    stack.enter_context(mock.patch(target, side_effect=AssertionError('Completed queue attempted inference/network')))
                stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                try:
                    runpy.run_path(str(script), run_name='__main__')
                except SystemExit as error:
                    self.assertEqual(error.code, 0)

    @unittest.skipUnless(os.name == 'nt', 'Shared benchmark mechanics use Windows msvcrt')
    def test_shared_runner_uses_campaign_paths_and_exact_workload(self):
        from tools import benchmark
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            benchmark.configure(root, root/'control')
            cfg = {'api_key': 'test-only-key', 'model_name': 'test-model', 'env': {}, 'args': ['--spec', '4']}
            benchmark.save(benchmark.CONFIGS/'baseline.json', cfg)
            server, bench = mock.Mock(), mock.Mock()
            server.pid, server.poll.return_value, server.wait.return_value = 123, None, 0
            bench.pid, bench.wait.return_value = 456, 0
            commands = []
            def popen(command, **kwargs):
                commands.append(command)
                if len(commands) == 1:
                    return server
                output = pathlib.Path(command[command.index('--out')+1])
                benchmark.save(output, {'single_stream': {'code': [{'ok': True, 'decode_tps': 30}]*5}, 'prefill': [{'pp_tps': [300]*8}]})
                return bench
            def run(command, **kwargs):
                if str(REPO/'tools/sanity.py') in command:
                    benchmark.save(pathlib.Path(command[-1]), {'passed': 6, 'total': 6})
                return mock.Mock(returncode=0)
            state = {'runs': {}}
            with mock.patch.object(benchmark, 'load', benchmark.read_json), mock.patch.object(benchmark, 'checkpoint'), mock.patch.object(benchmark, 'request', return_value={'loaded': True, 'status': 'ok'}), mock.patch.object(benchmark.time, 'sleep'), mock.patch.object(benchmark.subprocess, 'Popen', side_effect=popen), mock.patch.object(benchmark.subprocess, 'run', side_effect=run):
                benchmark.run_one({'id': 'test', 'args': ['--spec', '3'], 'env': {}, 'sanity': True}, state)
            self.assertEqual(state['runs']['test']['phase'], 'complete')
            self.assertEqual(state['runs']['test']['sanity'], {'passed': 6, 'total': 6})
            saved = benchmark.read_json(benchmark.CONFIGS/'test.json')
            self.assertEqual(saved['args'], ['--spec', '3'])
            self.assertEqual(saved['env']['STRATA_ROUTE_TAIL_SKIP'], '0')
            self.assertEqual(pathlib.Path(saved['log']).parent, root/'results')
            command = commands[1]
            self.assertEqual(command[command.index('--config')+1], str(REPO/'workloads/betterbench-16k.json'))
            start, end = command.index('--quick'), command.index('--config')
            self.assertEqual(command[start:end], ['--quick', '--decode', '--categories', 'code', '--prefill', '--no-concurrency'])

    @unittest.skipUnless(os.name == 'nt', 'Shared benchmark mechanics use Windows msvcrt')
    def test_result_parser_preserves_final_speeds(self):
        from tools import benchmark
        root = REPO/'campaigns/2026-11-02-p100-1080ti-x8-x8'
        state = json.loads((root/'state/gpu-x8-state.json').read_text())
        for run in ('x8-final-1', 'x8-p100-reference', 'x8-final-2'):
            self.assertEqual(benchmark.summarize(root/f'results/{run}.json'), state['runs'][run]['metrics'])


if __name__ == '__main__':
    unittest.main()
