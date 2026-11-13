"""One-time reviewed correction; preserve all previous attempts, never rerun their IDs."""
import hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parents[1]/'tools'))
import benchmark as bm
state_path=ROOT/'state/queue-state.json'
state=bm.load(state_path)
if state.get('error')!='Missing actual setting: layers 0-23 (CUDA0), 24-47 (CUDA1)':raise RuntimeError('Unexpected state; no change')
(ROOT/'results/override-recovery.initial-state.json').write_bytes(state_path.read_bytes())
base_path=ROOT/'configs/private/baseline.json'
(ROOT/'configs/private/baseline-before-override-review.json').write_bytes(base_path.read_bytes())
frozen_path=ROOT/'results/frozen-inputs.json'
(ROOT/'results/frozen-inputs-before-override-review.json').write_bytes(frozen_path.read_bytes())
base=bm.load(base_path)
for key in ('user_args','args_written','args_derived','launch_set'):base.pop(key,None)
bm.save(base_path,base)
frozen=bm.load(frozen_path);frozen['baseline_sha256']=hashlib.sha256(base_path.read_bytes()).hexdigest();bm.save(frozen_path,frozen)
for rid in ('reference36','split24'):
    r=state['runs'][rid];r.update(phase='invalid',reviewed=True,review_note='Excluded: stale user_args reintroduced projection and 36/12. Raw samples/logs preserved; no claimed setting comparison.')
state.update(phase='paused',current=None,recovery='2026-11-13 reviewed user_args override; sanitized isolated baseline, new IDs reference36-v2/split24-v2; original installed profile unchanged')
state.pop('error',None);bm.save(state_path,state)
print('Preserved excluded attempts; sanitized baseline and re-froze it after explicit review.')
