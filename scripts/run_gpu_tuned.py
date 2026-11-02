"""Launch the separately validated x8/x8 profile; original recommendation is untouched."""
import json
import os
import pathlib
import socket
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    profile = ROOT / 'configs/recommended-x8.json'
    if not profile.exists():
        raise SystemExit('Missing local configs/recommended-x8.json; see GPU_X8_REPORT.md.')
    cfg = json.loads(profile.read_text(encoding='utf-8'))
    control = pathlib.Path(cfg['cwd'])
    if not cfg.get('api_key') or cfg['api_key'] == '<REDACTED>':
        raise SystemExit('Restore the private local profile credential before launching.')
    if not pathlib.Path(cfg['exe']).is_file() or not (control / 'serve/server.py').is_file():
        raise SystemExit('Validated engine/control installation is missing; do not silently upgrade.')
    if '--check' in sys.argv:
        print('Local x8/x8 profile and installation resolved; no server started.')
        return 0
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1', 8080)) == 0:
            raise SystemExit('Port 8080 is occupied; stop your existing server first. Nothing was stopped.')
    env = os.environ.copy()
    env.update(STRATA_NO_PRESET='1', PYTHONIOENCODING='utf-8')
    return subprocess.call([
        str(control / 'python/python.exe'), str(control / 'serve/server.py'),
        '--engine', 'strata', '--config', str(profile), '--host', '127.0.0.1', '--port', '8080',
    ], cwd=control, env=env)


if __name__ == '__main__':
    sys.exit(main() or 0)
