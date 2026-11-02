import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
"""Small resumable GPU topology comparison; does not touch old tuning state/profiles."""
import copy, json, msvcrt, os, pathlib, socket, sys, time
from tools import benchmark as tune
from tools import gpu_topology as gc
ROOT=pathlib.Path(__file__).resolve().parents[1]
STATE=ROOT/'state/gpu-comparison-state.json'
CONTROL=tune.LOCAL/'components/control/0.1.55'
RUNS=[
 dict(id='gpu-p100-only',gpu=0,label='P100 alone (x16)'),
 dict(id='gpu-1080-only',gpu=1,label='1080 Ti alone (x4)'),
 dict(id='gpu-dual-p100-main',gpu=[1,0],label='Both; P100 main; auto split'),
 dict(id='gpu-dual-1080-main',gpu=[0,1],label='Both; 1080 Ti main; auto split'),
 dict(id='gpu-dual-p100-confirm',gpu=[1,0],label='Both; P100 main; repeat'),
 dict(id='gpu-dual-1080-confirm',gpu=[0,1],label='Both; 1080 Ti main; repeat',sanity=True),
]
gc.configure(ROOT, CONTROL)
_original_load=tune.read_json
current=gc.current
load=gc.load

def checkpoint(state):
    tune.save(STATE,state)
    text=['# P100 + GTX 1080 Ti topology comparison','','Current engine/control 0.1.55 throughout. Same IQ3_S weights, 131072 context, int8 KV, 32768 residency, full expert routing and previously selected speed settings. GPU 0 = P100 PCIe 3 x16 (TCC); GPU 1 = 1080 Ti PCIe 3 x4 (WDDM display).','','Requested BetterBench quick code decode + 16K-target prefill, no concurrency. Medians in tokens/s; 5 code / 8 prefill samples. Screening, not significance or comprehensive quality proof. Old results are not directly comparable across engine/hardware changes.','','| Run | Placement | State | Decode | Prefill |','|---|---|---|---:|---:|']
    for item in RUNS:
        r=state['runs'].get(item['id'],{}); m=r.get('metrics',{})
        text.append('| '+' | '.join([item['id'],item['label'],r.get('phase','pending'),f"{m['decode']:.2f}" if m.get('decode') else '—',f"{m['prefill']:.2f}" if m.get('prefill') else '—'])+' |')
    text+=['',f"Checkpoint: {state.get('phase')}; current {state.get('current')}; {time.strftime('%Y-%m-%d %H:%M:%S')}",'','Artifacts: `results/gpu-*.{json,engine.log,server.log,bench.log,gpu.csv}`. Private profiles in `configs/private/gpu-*.json` contain credentials. Resume from repository root: `python campaigns/2026-11-01-p100-1080ti-x16-x4/scripts/run.py`. Campaign `state/STOP-GPU` pauses between runs.','', 'Research: https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md . Main is the last stage and holds head/MTP; test both orders because P100 has more VRAM/HBM bandwidth/native FP16, while 1080 Ti has different compute and a slower host link. No approximate routing, lower precision, or unrelated parameter sweep.']
    (ROOT/'RESULTS.md').write_text('\n'.join(text)+'\n',encoding='utf-8')

def main():
    state=_original_load(STATE) if STATE.exists() else {'runs':{}}
    if state.get('phase')=='screening-complete-review-required' and all(state['runs'].get(item['id'],{}).get('phase')=='complete' for item in RUNS):
        print('Historical x16/x4 campaign complete. See RESULTS.md; no processes started.'); return
    lock=open(ROOT/'state/gpu-comparison.lock','a+b'); lock.write(b'0'); lock.flush(); lock.seek(0)
    msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    state=_original_load(STATE) if STATE.exists() else {'runs':{}}
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',8080))==0: raise RuntimeError('Port 8080 occupied; will not stop existing server')
    tune.CONTROL=CONTROL; tune.load=load; tune.checkpoint=checkpoint
    state['runner_pid']=os.getpid()
    for item in RUNS:
        r=state['runs'].get(item['id'],{})
        if r.get('phase')=='complete': continue
        if r: raise RuntimeError('Inspect interrupted/failed run before retrying: '+item['id'])
        if (ROOT/'state/STOP-GPU').exists(): state['phase']='paused'; checkpoint(state); return
        current.clear(); current.update(item)
        state.update(phase='gpu-comparison-running',current=item['id']); checkpoint(state)
        tune.run_one(dict(id=item['id'],args=item.get('args',[]),env=item.get('env',{}),sanity=item.get('sanity',False)),state)
        if state['runs'][item['id']]['phase']!='complete':
            state['phase']='paused-on-error'; checkpoint(state); return
    state.update(phase='screening-complete-review-required',current=None); checkpoint(state)

if __name__=='__main__': main()
