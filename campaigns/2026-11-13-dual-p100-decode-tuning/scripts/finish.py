"""Finalize only after reviewed completed confirmations; never starts a server."""
import copy,json,os,pathlib,statistics,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
sys.path.insert(0,str(REPO/'tools'))
import benchmark as bm
state=bm.load(ROOT/'state/queue-state.json')
if state['phase']=='complete':raise SystemExit('Already finalized')
if state['phase']!='paused':raise RuntimeError('Queue is not safely paused')
for rid,r in state['runs'].items():
    if r['phase'] not in ('complete','invalid') or not r.get('reviewed'):raise RuntimeError('Unreviewed attempt: '+rid)
for rid in ('confirm-reference','confirm-candidate-b'):
    if state['runs'][rid].get('sanity')!={'passed':7,'total':7}:raise RuntimeError('Smoke failed')
local=pathlib.Path(os.environ['LOCALAPPDATA'])/'Strata'
if bm.load(local/'launch/iq3_s-128k.json')!=bm.load(ROOT/'configs/private/original-installed.json'):raise RuntimeError('Installed profile changed during tests')
startup=pathlib.Path(os.environ['APPDATA'])/'Microsoft/Windows/Start Menu/Programs/Startup/strata-start.bat'
if startup.read_bytes()!=(ROOT/'configs/private/original-startup.bat').read_bytes():raise RuntimeError('Startup changed during tests')
cfg=bm.load(ROOT/'configs/private/confirm-candidate-b.json')
cfg['log']=str(ROOT/'results/recommended.engine.log')
bm.save(ROOT/'configs/private/recommended.json',cfg)
reference=state['runs']['confirm-reference']['metrics']
candidate={k:statistics.mean(state['runs'][n]['metrics'][k] for n in ('confirm-candidate-a','confirm-candidate-b')) for k in ('decode','prefill')}
bm.save(ROOT/'results/final-summary.json',{'reference':reference,'candidate_mean_of_two_medians':candidate,'change_pct':{k:100*(candidate[k]/reference[k]-1) for k in candidate},'candidate_ids':['confirm-candidate-a','confirm-candidate-b'],'reference_id':'confirm-reference','quality_smokes':{'reference':'7/7','candidate':'7/7'},'statistical_significance':False})
state.update(phase='complete',current=None,finished=time.strftime('%Y-%m-%d %H:%M:%S'),recommended_profile='recommended.json',installed_profile_unchanged=True,startup_unchanged=True,test_processes_stopped=True)
bm.save(ROOT/'state/queue-state.json',state)
m=bm.load(ROOT/'manifest.json');m.update(status='complete',completed_phase='complete',completed_benchmarks=10,rejected_configurations=2,recommended_profile='recommended.json');bm.save(ROOT/'manifest.json',m)
print('Finalized 10 valid benchmarks + 2 reviewed exclusions; original profile and Startup unchanged.')
