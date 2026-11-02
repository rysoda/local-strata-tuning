"""Original single-card campaign supervisor. Completed queues exit without inference."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools import benchmark as engine
import json, msvcrt, os, pathlib, time
ROOT = pathlib.Path(__file__).resolve().parents[1]
engine.configure(ROOT, engine.LOCAL/'components/control/0.1.51')
RESULTS, CONFIGS, STATE_DIR, STATE, CONTROL = engine.RESULTS, engine.CONFIGS, engine.STATE_DIR, engine.STATE, engine.CONTROL
load, save, summarize, stop_server = engine.load, engine.save, engine.summarize, engine.stop_server

def run_one(item, state):
    engine.checkpoint = checkpoint
    engine.run_one(item, state)

def render(state):
    entries = [('baseline',{})] + [(x['id'],x) for x in load(ROOT/'experiments.json')]
    if (ROOT/'combined-experiments.json').exists():
        entries += [(x['id'],x) for x in load(ROOT/'combined-experiments.json')]
    ref = state.get('runs',{}).get('quality-reference',{}).get('metrics',{})
    text = ['# Tuning results','', 'Live checkpoint. Speeds are tokens/s, medians. Five sampled decode passes are provisional; not significance or quality proof. All experiment deltas use the quality reference, NOT the approximate original baseline.','', '| Run | State | Code decode | 16K prefill | Decode delta | Prefill delta | Usage |','|---|---|---:|---:|---:|---:|---|']
    for id, item in entries:
        r = state.get('runs',{}).get(id,{})
        m = r.get('metrics',{})
        dec, pp = m.get('decode'), m.get('prefill')
        dd = (dec/ref['decode']-1)*100 if dec and ref.get('decode') else None
        pd = (pp/ref['prefill']-1)*100 if pp and ref.get('prefill') else None
        mark = 'pending'
        if m:
            mark = 'invalid' if not m.get('valid') else 'reference' if item.get('family')=='reference' else 'baseline only' if id=='baseline' else 'not selected'
            if id!='baseline' and item.get('family')!='reference' and m.get('valid') and dd is not None and pd is not None:
                if (dd>3 and pd>-10) or (pd>5 and dd>-3): mark='provisional gain; confirm'
        final=state.get('final_selection')
        if final:
            if id in final['single_components']: mark='USE (combined-confirmed)'
            elif id in final['confirmation_ids']: mark='recommended combination'
            elif item.get('family')=='reference': mark='reference'
            elif id=='baseline': mark='approximate original baseline only'
            elif r.get('phase')=='failed': mark='incompatible; see log'
            elif m: mark='not selected after combined review'
        vals=[id,r.get('phase','pending'),f'{dec:.2f}' if dec else '—',f'{pp:.2f}' if pp else '—',f'{dd:+.1f}%' if dd is not None else '—',f'{pd:+.1f}%' if pd is not None else '—',mark]
        text.append('| '+' | '.join(vals)+' |')
    text += ['', '## Checkpoint', '', f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"Queue phase: {state.get('phase')}; current: {state.get('current','none')}", '', 'Each run has `results/<id>.json`, `.html`, `.engine.log`, `.server.log`, `.bench.log`, and `configs/private/<id>.json`. See `TUNING_PLAN.md` for interpretation and exclusions.', '', '## Combined stage', '', 'See `STAGE1_REVIEW.md` and `COMBINED_RESULTS.md` for late-reference comparisons, combination rationale and status. Initial-reference deltas above are screening only; auto-sized cache/chunk drift confounds them.']
    if state.get('final_selection'):
        text += ['', '## Final decision', '', 'Completed. See `FINAL_REPORT.md` for the final nearby-reference comparison and `configs/private/recommended.json` / repository `launchers/Run-1080Ti.cmd` for the ready-to-run profile. Initial-reference deltas in this table are NOT the final claimed gain. Only tasks 36, adaptation interval 1 and PCIe balance are retained as speed changes; approximate routing is disabled.']
    (ROOT/'RESULTS.md').write_text('\n'.join(text)+'\n',encoding='utf-8')

def checkpoint(state):
    save(STATE,state)
    render(state)

def main():
    lock=open(STATE_DIR/'queue.lock','a+b'); lock.seek(0); lock.write(b'0'); lock.flush(); lock.seek(0)
    try: msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    except OSError: raise SystemExit('Another tuning runner owns the lock')
    state=load(STATE) if STATE.exists() else {'runs':{}}
    if state.get('phase')=='tuning-complete':
        lock.close()
        print('Tuning already complete. See FINAL_REPORT.md; no processes started.')
        return
    state.update(phase='waiting-for-baseline',runner_pid=os.getpid())
    checkpoint(state)
    while True:
        baseline=load(STATE_DIR/'baseline.status.json')
        if baseline['phase']=='complete': break
        if baseline['phase']=='failed': raise RuntimeError('Baseline failed; inspect before continuing')
        if (STATE_DIR/'STOP').exists(): state['phase']='paused'; checkpoint(state); return
        time.sleep(10)
    m=summarize(RESULTS/'baseline.json')
    state['runs']['baseline']={'phase':'complete' if m['valid'] else 'invalid','metrics':m}
    checkpoint(state)
    if not m['valid']: raise RuntimeError('Baseline missing successful measurements; inspect before continuing')
    stop_server(load(STATE_DIR/'baseline.process.json')['server_pid'])
    # Do not compete with any server still listening on the benchmark port.
    import socket
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',8080))==0: raise RuntimeError('Port 8080 still occupied; no experiment started')
    for item in load(ROOT/'experiments.json'):
        id=item['id']
        old=state['runs'].get(id,{})
        if old.get('phase') in ('complete','invalid','failed'): continue
        if old.get('server_pid'): raise RuntimeError(f'Interrupted experiment {id}: inspect recorded processes before resuming')
        if (STATE_DIR/'STOP').exists(): state['phase']='paused'; checkpoint(state); return
        state.update(phase='single-parameter-tests',current=id)
        checkpoint(state)
        run_one(item,state)
        if state['runs'][id]['phase']!='complete':
            state['phase']='paused-on-error'; checkpoint(state); return
    state.update(phase='singles-complete-review-required',current=None)
    checkpoint(state)

if __name__=='__main__': main()
