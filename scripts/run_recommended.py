"""Launch the tuned local profile, resolving credentials without committing them."""
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOCAL = pathlib.Path(os.environ['LOCALAPPDATA']) / 'Strata'
CONTROL = LOCAL / 'components/control/0.1.51'


def main():
    source = ROOT / 'configs/recommended.json'
    if not source.exists():
        source = ROOT / 'configs/shareable/recommended.json'
    cfg = json.loads(source.read_text(encoding='utf-8'))
    if cfg.get('api_key') == '<REDACTED>':
        key = os.environ.get('STRATA_API_KEY')
        installed = LOCAL / 'launch/iq3_s-128k.json'
        if not key and installed.exists():
            key = json.loads(installed.read_text(encoding='utf-8')).get('api_key')
        if not key:
            raise SystemExit('Set STRATA_API_KEY or restore the private local profile; refusing to launch with a redacted credential.')
        cfg['api_key'] = key
    cfg['host'] = '127.0.0.1'
    if '--check' in sys.argv:
        print('Recommended profile and credential resolved; no server started.')
        return
    runtime = ROOT / 'configs/recommended.runtime.json'
    runtime.write_text(json.dumps(cfg, indent=2), encoding='utf-8')
    env = os.environ.copy()
    env['STRATA_NO_PRESET'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    return subprocess.call([
        str(CONTROL / 'python/python.exe'), str(CONTROL / 'serve/server.py'),
        '--engine', 'strata', '--config', str(runtime), '--host', '127.0.0.1', '--port', '8080',
    ], cwd=CONTROL, env=env)


if __name__ == '__main__':
    sys.exit(main() or 0)
