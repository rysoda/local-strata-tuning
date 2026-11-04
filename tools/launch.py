"""Launch a campaign recommendation without publishing local API credentials.

python tools/launch.py CAMPAIGN [--context TOKENS] [--check]
--check resolves/validates paths and credentials, but writes nothing and starts nothing.
"""
import argparse
import json
import os
import pathlib
import socket
import subprocess

REPO = pathlib.Path(__file__).resolve().parents[1]


def resolve(campaign, context=None):
    root = REPO/'campaigns'/campaign
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    name = manifest.get('recommended_profile')
    if not name:
        raise SystemExit('This campaign has no deployable recommendation; see its README.md.')
    source = root/'configs/private'/name
    if not source.exists():
        source = root/'configs/shareable'/name
    cfg = json.loads(source.read_text(encoding='utf-8'))
    if not cfg.get('api_key') or cfg['api_key'] == '<REDACTED>':
        key = os.environ.get('STRATA_API_KEY')
        installed = pathlib.Path(os.environ['LOCALAPPDATA'])/'Strata/launch/iq3_s-128k.json'
        if not key and installed.exists():
            key = json.loads(installed.read_text(encoding='utf-8')).get('api_key')
        if not key or key == '<REDACTED>':
            raise SystemExit('Set STRATA_API_KEY or restore the private profile credential.')
        cfg['api_key'] = key
    control = pathlib.Path(cfg['cwd'])
    for path in (pathlib.Path(cfg['exe']), control/'serve/server.py', control/'python/python.exe'):
        if not path.is_file():
            raise SystemExit(f'Validated installation path is missing: {path}. Adapt local paths; do not silently upgrade.')
    if context is not None:
        if context <= 0:
            raise ValueError('Context must be positive.')
        args = cfg.setdefault('args', [])
        if '--max-context' in args:
            args[args.index('--max-context') + 1] = str(context)
        else:
            args.extend(['--max-context', str(context)])
    cfg.update(host='127.0.0.1', port=8080, open_browser=False)
    cfg['log'] = str(root/'results/recommended.engine.log')
    return root, control, cfg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaign', choices=sorted(p.parent.name for p in (REPO/'campaigns').glob('*/manifest.json')))
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--context', type=int, help='Runtime context override; saved profiles stay unchanged')
    args = parser.parse_args()
    if args.context is not None and args.context <= 0:
        parser.error('--context must be positive')
    root, control, cfg = resolve(args.campaign, args.context)
    if args.check:
        context = cfg.get('args', [])
        detail = f" Context: {context[context.index('--max-context') + 1]}." if '--max-context' in context else ''
        print(f'{args.campaign}: profile, credential and installation resolved; no files written or server started.{detail}')
        return 0
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1', 8080)) == 0:
            raise SystemExit('Port 8080 is occupied; stop your existing server first. Nothing was stopped.')
    runtime = root/'configs/private/recommended.runtime.json'
    runtime.parent.mkdir(parents=True, exist_ok=True)
    (root/'results').mkdir(exist_ok=True)
    runtime.write_text(json.dumps(cfg, indent=2), encoding='utf-8')
    env = os.environ.copy()
    env.update(STRATA_NO_PRESET='1', PYTHONIOENCODING='utf-8')
    return subprocess.call([
        str(control/'python/python.exe'), str(control/'serve/server.py'),
        '--engine', 'strata', '--config', str(runtime), '--host', '127.0.0.1', '--port', '8080',
    ], cwd=control, env=env)


if __name__ == '__main__':
    raise SystemExit(main())
