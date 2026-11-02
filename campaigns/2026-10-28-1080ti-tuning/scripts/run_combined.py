from pathlib import Path
import sys
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
"""Run reviewed combinations after the initial queue has stopped; same exact benchmark."""
import json, msvcrt, os, pathlib, time
import tune
ROOT=tune.ROOT

def items():
    def item(id,args=None,env=None,family='combined'):
        return dict(id=id,args=args or [],env=env or {},family=family)
    core=['--kv-resident','20480','--host-core','last','--pool-tasks','36']
    adaptive=core+['--adapt-every','1']
    return [
        item('short-read-0',['--short-read','0'],family='short-read'),
        item('head-alias-compatible',['--short-read','0','--prefill-head-alias']),
        item('combined-resource',core),
        item('combined-adaptive',adaptive,{'STRATA_PCIE_BALANCE':'1'}),
        item('combined-lookup',adaptive+['--lookup-chain','2'],{'STRATA_PCIE_BALANCE':'1'}),
        item('combined-draft',adaptive+['--suffix-draft','0','--mtp-draft-vocab',str(tune.CONTROL/'data/draft_vocab_en.bin'),'--mtp-q4','all'],{'STRATA_PCIE_BALANCE':'1'}),
        item('quality-reference-postcombined',family='reference'),
    ]

def report(state, manifest):
    late=state['runs'].get('quality-reference-repeat',{}).get('metrics',{})
    post=state['runs'].get('quality-reference-postcombined',{}).get('metrics',{})
    lines=['# Combined-stage results','','Same requested BetterBench workload and target model as stage 1. Median tokens/s. The late unchanged reference is the main comparison because cache allocation drift affected the first reference.','', '| Run | State | Decode | Prefill | Decode vs late reference | Prefill vs late reference |','|---|---|---:|---:|---:|---:|']
    for id in ['quality-reference','quality-reference-repeat']+[x['id'] for x in manifest]:
        r=state['runs'].get(id,{})
        m=r.get('metrics',{})
        d,p=m.get('decode'),m.get('prefill')
        dd=(d/late['decode']-1)*100 if d and late.get('decode') else None
        pd=(p/late['prefill']-1)*100 if p and late.get('prefill') else None
        lines.append('| '+' | '.join([id,r.get('phase','pending'),f'{d:.2f}' if d else '—',f'{p:.2f}' if p else '—',f'{dd:+.1f}%' if dd is not None else '—',f'{pd:+.1f}%' if pd is not None else '—'])+' |')
    lines+=['','## Rationale','','- `short-read-0` isolates the prerequisite; `head-alias-compatible` adds head lending. The failed single head-alias startup remains in the original table.','- Resource core: KV residency 20480 + host last + tasks 36.','- Adaptive core adds interval 1 and PCIe balance.','- Lookup arm adds verified prompt lookup; draft arm instead tests verified-only smaller/quantized drafter and suffix-off. Target weights and int8 KV never change.','- All speed gains remain provisional until confirmation and correctness checks. No significance claims from five unpaired code samples.','',f"Updated {time.strftime('%Y-%m-%d %H:%M:%S')}; phase {state.get('phase')}."]
    (ROOT/'COMBINED_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def main():
    # Wait for the supervised late reference. A lock also prevents two benchmark queues.
    while True:
        state=tune.load(tune.STATE)
        if state.get('phase')=='tuning-complete':
            print('Tuning already complete. See FINAL_REPORT.md; no processes started.')
            return
        if state.get('phase') in ('singles-complete-review-required','combined-complete-review-required'): break
        if state.get('phase') in ('paused-on-error','paused'): raise SystemExit('Initial queue requires review')
        time.sleep(10)
    lock=open(tune.STATE_DIR/'queue.lock','a+b'); lock.seek(0)
    for _ in range(12):
        try: msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1); break
        except OSError: time.sleep(5)
    else: raise SystemExit('Queue lock still owned')
    path=ROOT/'combined-experiments.json'
    manifest=tune.load(path) if path.exists() else items()
    if not path.exists(): tune.save(path,manifest)
    for item in manifest:
        state=tune.load(tune.STATE)
        id=item['id']; old=state['runs'].get(id,{})
        if old.get('phase') in ('complete','failed','invalid'): continue
        if old.get('server_pid'): raise SystemExit('Ambiguous interrupted experiment; inspect process ownership')
        if (ROOT/'state/STOP').exists(): state['phase']='paused'; tune.checkpoint(state); report(state,manifest); return
        state.update(phase='combined-parameter-tests',current=id,runner_pid=os.getpid())
        tune.checkpoint(state); report(state,manifest)
        tune.run_one(item,state); report(state,manifest)
        if state['runs'][id]['phase']!='complete':
            state['phase']='paused-on-error'; tune.checkpoint(state); report(state,manifest); return
    state.update(phase='combined-complete-review-required',current=None)
    tune.checkpoint(state); report(state,manifest)

if __name__=='__main__': main()
