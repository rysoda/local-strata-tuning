"""Staged topology screens. Default --check never launches inference.
Only the initial five quality-preserving references are executable yet.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO))
from tools import benchmark as bench

STATE = ROOT / 'state/queue-state.json'
LOCK = ROOT / 'state/runner.lock'
CONTROL = Path(os.environ['LOCALAPPDATA']) / 'Strata/components/control/0.1.57'
GPU_FIELDS = 'timestamp,index,uuid,temperature.gpu,clocks.sm,power.draw,utilization.gpu,memory.used,memory.free,pcie.link.gen.current,pcie.link.width.current,clocks_event_reasons.sw_thermal_slowdown,clocks_event_reasons.hw_thermal_slowdown'
INITIAL = [
    dict(id='r01-quality-reference-layout', gpu=[0, 1], split='32', trim=True,
         reason='Quality-restored installed layout at 256K; no speed projection from the as-found profile'),
    dict(id='r02-p100-only', gpu=0, reason='Fresh x16 P100 fallback; determine whether x4 helper is worthwhile'),
    dict(id='r03-1080-only', gpu=1, reason='Fresh x4 display-card reference, no physical move'),
    dict(id='r04-auto-1080-main', gpu=[0, 1], split='auto', reason='Per-link automatic split with 1080 Ti last/Main'),
    dict(id='r05-auto-p100-main', gpu=[1, 0], split='auto', reason='Reverse Main order; P100 hosts head/MTP'),
]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(item):
    cfg = read(ROOT / 'configs/private/baseline.json')
    cfg['gpu'] = item['gpu']
    cfg['gpu_order'] = 'as_given'
    cfg.pop('gpu_roles', None)
    first = item['gpu'][0] if isinstance(item['gpu'], list) else item['gpu']
    reserves = {0: str(item.get('p100_reserve', 700)), 1: str(item.get('ti_reserve', 1600))}
    cfg['args'] += ['--vram-reserve-mib', reserves[first]]
    if isinstance(item['gpu'], list):
        cfg['layer_split'] = item['split']
        cfg['args'] += ['--vram-reserve-later-mib', reserves[item['gpu'][-1]]]
    else:
        cfg.pop('layer_split', None)
    if item.get('trim'):
        cfg['args'].append('--trim-stage-weights')
    cfg['args'].extend(item.get('args', []))
    cfg['env'].update(item.get('env', {}))
    cfg['log'] = str(ROOT / f"results/{item['id']}.engine.log")
    assert cfg['args'][cfg['args'].index('--max-context') + 1] == '262144'
    assert cfg['args'][cfg['args'].index('--kv') + 1] == 'int8'
    assert cfg['drafting'] == 'mtp' and cfg['mtp'] is True
    assert not any('control-vector' in a or 'cvec' in a for a in cfg['args'])
    assert cfg['env']['STRATA_ROUTE_PRIOR'] == cfg['env']['STRATA_ROUTE_TAIL_SKIP'] == '0'
    return cfg


def check():
    frozen = read(ROOT / 'results/frozen-inputs.json')
    cfg = read(ROOT / 'configs/private/baseline.json')
    clean = {k: v for k, v in cfg.items() if k != 'api_key'}
    if hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest() != frozen['baseline_scientific_sha256']:
        raise RuntimeError('Baseline inference settings changed; explicit review required')
    for item in frozen['files']:
        if fingerprint(Path(item['path'])) != item['sha256']:
            raise RuntimeError('Frozen input changed: ' + item['path'])
    for item in frozen['model_files']:
        stat = Path(item['path']).stat()
        if stat.st_size != item['size'] or stat.st_mtime_ns != item['mtime_ns']:
            raise RuntimeError('Model artifact changed: ' + item['path'])
    cards = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,pcie.link.width.current', '--format=csv,noheader,nounits'], text=True)
    expected = [('0', 'GPU-bab5c751-1e02-b6a7-cf6f-b6256c3a5999', '16'), ('1', 'GPU-7d8ccb39-60d5-bc52-5e38-1cb26b742a23', '4')]
    actual = [tuple(v.strip() for v in row.split(',')) for row in cards.strip().splitlines()]
    if actual != expected:
        raise RuntimeError('GPU UUID/order/link topology changed; use a new campaign: ' + cards)
    for item in INITIAL:
        build(item)
    return cards


def idle():
    script = ('Get-CimInstance Win32_Process | Where-Object { '
              '$_.Name -match "^strata.*\\.exe$|^betterbench" -or '
              '($_.Name -match "^python.*\\.exe$" -and $_.CommandLine -match '
              '"server.py|monitor_power.py|capture.py|reference.py|benchmark|scripts[\\\\/](run|continue).py") '
              '} | Select-Object ProcessId,CommandLine | ConvertTo-Json')
    raw = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command', script], text=True).strip()
    processes = json.loads(raw) if raw else []
    if isinstance(processes, dict):
        processes = [processes]
    if any(p['ProcessId'] != os.getpid() for p in processes):
        raise RuntimeError('Existing inference/measurement/queue processes; inspect live ownership. Nothing stopped.')
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1', 8080)) == 0:
            raise RuntimeError('Port 8080 occupied; nothing stopped')


def checkpoint(state):
    state['updated_utc'] = datetime.now(timezone.utc).isoformat()
    bench.save(STATE, state)
    rows = ['# Initial topology screens', '', 'Quick screening only; no recommendation until confirmation and smoke checks.', '',
            '| Run | State | Decode tok/s | Prefill tok/s |', '|---|---|---:|---:|']
    for item in INITIAL:
        r = state['runs'].get(item['id'], {})
        m = r.get('metrics', {})
        rows.append(f"| {item['id']} | {r.get('phase', 'pending')} | {m.get('decode', '—')} | {m.get('prefill', '—')} |")
    (ROOT / 'RESULTS.md').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    path = ROOT / 'manifest.json'
    manifest = read(path)
    manifest.update(status=state['phase'], completed_benchmarks=sum(r.get('phase') == 'complete' for r in state['runs'].values()))
    bench.save(path, manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--run-initial', action='store_true')
    parser.add_argument('--cooling-note', help='Required physical fan/case configuration; must remain fixed; no credentials')
    args = parser.parse_args()
    if not args.run_initial:
        check()
        print('Frozen software/model/profile and x16/x4 topology checks passed. Five initial profiles validated; nothing started.')
        return
    if not args.cooling_note or not args.cooling_note.strip():
        parser.error('--run-initial requires --cooling-note; confirm case/fans and keep them fixed')
    state = read(STATE)
    if state['phase'] in ('initial-screening-complete-review-required', 'complete'):
        print('Initial phase already complete; review results and define targeted follow-ups. Nothing started.')
        return
    if state['phase'] == 'error' or any(r.get('phase') != 'complete' for r in state['runs'].values()):
        raise SystemExit('Unreviewed incomplete/error state; preserve evidence and inspect before recovery')
    if (ROOT / 'state/STOP').exists():
        raise SystemExit('STOP flag present; no run started')
    with LOCK.open('x') as f:
        f.write(str(os.getpid()))
    bench.configure(ROOT, CONTROL)
    bench.checkpoint = checkpoint
    original_load = bench.load
    active = {}
    def loader(path):
        if Path(path) == ROOT / 'configs/private/baseline.json':
            return copy.deepcopy(active['config'])
        return original_load(path)
    bench.load = loader
    try:
        check()
        idle()
        if state.get('cooling_note') and state['cooling_note'] != args.cooling_note:
            raise RuntimeError('Cooling setup declaration changed; do not pool changed hardware')
        state.update(cooling_note=args.cooling_note, runner_pid=os.getpid())
        checkpoint(state)
        for item in INITIAL:
            if state['runs'].get(item['id'], {}).get('phase') == 'complete':
                continue
            if (ROOT / 'state/STOP').exists():
                state.update(phase='paused', current=None)
                checkpoint(state)
                return
            idle()
            check()
            if list((ROOT / 'results').glob(item['id'] + '.*')):
                raise RuntimeError('Uncheckpointed evidence exists; explicit review required: ' + item['id'])
            active['config'] = build(item)
            state.update(phase='running', current=item['id'])
            checkpoint(state)
            with (ROOT / f"results/{item['id']}.hardware.csv").open('x') as telemetry:
                sampler = subprocess.Popen(['nvidia-smi', '--query-gpu=' + GPU_FIELDS, '--format=csv', '--loop=2'], stdout=telemetry, stderr=subprocess.STDOUT)
                try:
                    bench.run_one(dict(id=item['id'], args=[], env={}), state)
                finally:
                    if sampler.poll() is None:
                        sampler.terminate()
                    sampler.wait(timeout=15)
            if state['runs'][item['id']]['phase'] != 'complete':
                raise RuntimeError('Failed/invalid run; paused for review: ' + item['id'])
        state.update(phase='initial-screening-complete-review-required', current=None)
        checkpoint(state)
        print('Five initial screens complete; queue stops for startup/thermal/memory review. No follow-ups auto-started.')
    except BaseException as error:
        # On interrupt, shared mechanics already stop their created server. Also
        # stop a still-owned benchmark only after checking its live output path.
        current = state.get('current')
        run = state['runs'].get(current, {})
        if run.get('benchmark_pid') and current:
            owned_output = str(ROOT / f'results/{current}.json')
            script = f'$p=Get-CimInstance Win32_Process -Filter "ProcessId={int(run["benchmark_pid"])}"; if ($p -and $p.CommandLine -like "*{owned_output}*") {{ taskkill /PID {int(run["benchmark_pid"])} /T /F }}'
            subprocess.run(['powershell.exe', '-NoProfile', '-Command', script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        state.update(phase='error', error=str(error) or type(error).__name__)
        checkpoint(state)
        raise
    finally:
        bench.load = original_load
        LOCK.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
