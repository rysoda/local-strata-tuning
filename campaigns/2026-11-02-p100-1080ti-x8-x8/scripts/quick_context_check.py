"""Two one-off context-capacity screens; never resumes or alters the completed queue."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from tools import benchmark as bench
from tools.launch import resolve


def main():
    root, control, cfg = resolve('2026-11-02-p100-1080ti-x8-x8')
    stamp = time.strftime('%Y%m%d-%H%M%S')
    ident = 'quick-context-' + stamp
    bench.configure(root, control)
    bench.RESULTS = root/'results'/ident
    bench.CONFIGS = root/'configs/private'/ident
    bench.STATE = root/'state'/(ident+'.json')
    bench.RESULTS.mkdir()
    bench.CONFIGS.mkdir()
    # A separate exclusive lock, also used by any subsequent invocation of this script.
    lock = open(root/'state/quick-context.lock', 'a+')
    import msvcrt
    lock.seek(0)
    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1', 8080)) == 0:
            raise RuntimeError('Port 8080 occupied; refusing to start or stop anything')
    state = {'purpose': 'One-off 128K versus 256K capacity check, not a tuning campaign',
             'phase': 'running', 'runner_pid': os.getpid(), 'runs': {},
             'results': str(bench.RESULTS)}
    bench.checkpoint = lambda s: bench.save(bench.STATE, s)
    bench.save(bench.CONFIGS/'baseline.json', cfg)
    help_result = subprocess.run([cfg['exe'], '--help'], capture_output=True, text=True)
    (bench.RESULTS/'installed-help.txt').write_text(help_result.stdout+help_result.stderr)
    hardware = subprocess.run(['nvidia-smi', '-q'], capture_output=True, text=True)
    (bench.RESULTS/'hardware-before.txt').write_text(hardware.stdout+hardware.stderr)
    bench.save(bench.RESULTS/'provenance.json', {
        'engine': cfg['exe'], 'engine_sha256': hashlib.sha256(Path(cfg['exe']).read_bytes()).hexdigest(),
        'control': str(control), 'model': cfg['model_name'], 'gpu': cfg['gpu'],
        'layer_split': cfg['layer_split'], 'changed_argument_only': '--max-context',
        'contexts': [131072, 262144], 'kv_resident': 32768,
        'workload': str(bench.WORKLOAD), 'sanity': 'not requested; no long-context validation',
        'source_profile_sha256': hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
    })
    bench.checkpoint(state)
    print('Results:', bench.RESULTS, flush=True)
    try:
        for context in (131072, 262144):
            item = {'id': f'ctx-{context}', 'env': {}, 'args': ['--max-context', str(context)]}
            bench.run_one(item, state)
            print(json.dumps(state['runs'][item['id']]), flush=True)
            if state['runs'][item['id']]['phase'] != 'complete':
                state['phase'] = 'paused-on-error'
                break
        else:
            state['phase'] = 'complete'
    except BaseException:
        state['phase'] = 'interrupted-review-required'
        raise
    finally:
        bench.checkpoint(state)
        bench.save(bench.RESULTS/'summary.json', state)
        lock.close()


if __name__ == '__main__':
    main()
