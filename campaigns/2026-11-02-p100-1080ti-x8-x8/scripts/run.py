"""Independent x8/x8 comparison. Resume completed runs; STOP-GPU-X8 pauses between runs."""
import json, os, pathlib, subprocess, threading, time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools import gpu_topology as gc
from tools import benchmark as tune
ROOT=pathlib.Path(__file__).resolve().parents[1]
gc.configure(ROOT, tune.LOCAL/'components/control/0.1.55')
STATE=ROOT/'state/gpu-x8-state.json'
RUNS=[
 dict(id='x8-p100-only',gpu=0,label='P100 only'),
 dict(id='x8-1080-only',gpu=1,label='1080 Ti only'),
 dict(id='x8-dual-p100',gpu=[1,0],label='Auto split; P100 Main'),
 dict(id='x8-dual-1080',gpu=[0,1],label='Auto split; 1080 Ti Main'),
 dict(id='x8-pipeline-p100',gpu=[1,0],label='P100 Main; pipeline windows 2',args=['--pipeline-windows','2']),
 dict(id='x8-pipeline-1080',gpu=[0,1],label='1080 Ti Main; pipeline windows 2',args=['--pipeline-windows','2']),
 dict(id='x8-trim-32',gpu=[0,1],split='32',label='P100 layers 0-31; 1080 Ti 32-47; trim',args=['--trim-stage-weights']),
 dict(id='x8-trim-24',gpu=[0,1],split='24',label='Equal layers; 1080 Ti Main; trim',args=['--trim-stage-weights']),
 dict(id='x8-safe-p100',gpu=[1,0],label='P100 Main; later reserve 1600 MiB',args=['--vram-reserve-later-mib','1600']),
 dict(id='x8-stage0-p100',gpu=[1,0],label='P100 Main; pipeline 2; draft on first; reserve 1600',args=['--pipeline-windows','2','--vram-reserve-later-mib','1600'],env={'STRATA_MTP_STAGE0':'1'}),
 dict(id='x8-stage0-1080',gpu=[0,1],label='1080 Main; pipeline 2; draft on first; reserve 1600',args=['--pipeline-windows','2','--vram-reserve-later-mib','1600'],env={'STRATA_MTP_STAGE0':'1'}),
 dict(id='x8-peer-p100',gpu=[0,1],label='P100 primary; 1080 expert peer; peer reserve 1600',args=['--peer-device','1','--peer-reserve-mib','1600']),
 dict(id='x8-prefill-pipe',gpu=[1,0],label='P100 Main; balanced prompt chunks; reserve 1600',args=['--prefill-pipe','1','--vram-reserve-later-mib','1600']),
 dict(id='x8-trim-32-safe',gpu=[0,1],split='32',label='P100 32 / 1080 16; trim; later reserve 1600',args=['--trim-stage-weights','--vram-reserve-later-mib','1600']),
 dict(id='x8-trim-p100-safe',gpu=[1,0],split='16',label='1080 16 / P100 32; trim; later reserve 1600',args=['--trim-stage-weights','--vram-reserve-later-mib','1600']),
 dict(id='x8-final-1',gpu=[0,1],split='32',label='Selected safe trim32; confirmation + recall',args=['--trim-stage-weights','--vram-reserve-later-mib','1600'],sanity=True),
 dict(id='x8-p100-reference',gpu=0,label='P100 only; nearby reference + recall',sanity=True),
 dict(id='x8-final-2',gpu=[0,1],split='32',label='Selected safe trim32; second confirmation',args=['--trim-stage-weights','--vram-reserve-later-mib','1600']),
]
def checkpoint(state):
 tune.save(STATE,state)
 lines=['# PCIe x8/x8 GPU experiments','','Engine/control 0.1.55; GPU 0 P100 16GB TCC, GPU 1 GTX 1080 Ti 11GB WDDM. Both measured PCIe 3 x8. Earlier x16/x4 results in ../2026-11-01-p100-1080ti-x16-x4/RESULTS.md are historical, not references.','','Same IQ3_S model, 131072 context, int8 KV, 32768 KV residency, full routing; requested BetterBench quick code decode and 16K-target prefill, no concurrency. Five decode/eight prefill samples per run; medians tok/s. Thermal throttling can confound comparisons.','','| Run | Placement | State | Decode | Prefill |','|---|---|---|---:|---:|']
 for item in RUNS:
  r=state.get('runs',{}).get(item['id'],{}); m=r.get('metrics',{})
  lines.append('| '+' | '.join([item['id'],item['label'],r.get('phase','pending'),f"{m['decode']:.2f}" if m.get('decode') else '—',f"{m['prefill']:.2f}" if m.get('prefill') else '—'])+' |')
 lines += ['',f"Checkpoint: {state.get('phase')}; current {state.get('current')}; {time.strftime('%Y-%m-%d %H:%M:%S')}",'','## Rationale','','Test single cards and both Main orders first. Pipeline windows overlaps speculative work without dropping target experts. Two explicit splits plus dense-weight trimming test compute balance versus expert-cache capacity. Follow-ups test safer VRAM reserve, explicit stage-0 draft placement (not default on installed CUDA), an expert peer instead of layer splitting, and balanced prompt chunks. No model/precision/context reduction. Current online docs describe newer versions: installed --help and startup logs determine actual support. See NOTES.md for reviewed failures and recovery decisions.','','Research: [layer split](https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md), [expert helper alternative](https://github.com/Niko1221/Strata/blob/main/docs/SECOND_GPU.md). Layer splits transfer stage activations via pinned host RAM and do not require NVLink/P2P. Helper caches add per-layer round trips and are not the first choice for two capable GPUs.','','Raw artifacts: results/x8-*. Private configs contain credentials; do not publish. Detailed telemetry in results/gpu-x8-telemetry.csv includes GPU IDs, clocks, thermal throttle flags, link widths. Resume from repository root: python campaigns/2026-11-02-p100-1080ti-x8-x8/scripts/run.py; pause: create campaign state/STOP-GPU-X8. Original tuning queue/install profiles untouched.']
 (ROOT/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
def monitor(stop):
 fields='index,uuid,temperature.gpu,utilization.gpu,memory.used,clocks.sm,power.draw,clocks_event_reasons.hw_thermal_slowdown,clocks_event_reasons.sw_thermal_slowdown,pcie.link.gen.current,pcie.link.width.current'
 with open(ROOT/'results/gpu-x8-telemetry.csv','a') as f:
  f.write('timestamp,run,'+fields+'\n'); f.flush()
  while not stop.is_set():
   try:
    s=subprocess.check_output(['nvidia-smi','--query-gpu='+fields,'--format=csv,noheader,nounits'],text=True,timeout=10)
    for row in s.strip().splitlines(): f.write(time.strftime('%Y-%m-%d %H:%M:%S')+','+str(gc.current.get('id','idle'))+','+row+'\n')
    f.flush()
   except Exception as e: print('telemetry:',e,flush=True)
   stop.wait(5)
def main():
 # Reuse the ownership checks and independent runner lock; never resume the historical queue.
 # Use a separate pause flag and lock for the new topology.
 import msvcrt, socket
 lock=open(ROOT/'state/gpu-x8.lock','a+b'); lock.write(b'0'); lock.flush(); lock.seek(0); msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
 state=tune.load(STATE) if STATE.exists() else {'runs':{}}
 if state.get('phase')=='gpu-tuning-complete':
  lock.close()
  print('x8/x8 tuning complete. See REPORT.md; no processes started.'); return
 with socket.socket() as s:
  if s.connect_ex(('127.0.0.1',8080))==0: raise RuntimeError('8080 occupied; no existing server stopped')
 tune.CONTROL=gc.CONTROL; tune.load=gc.load; tune.checkpoint=checkpoint
 state['runner_pid']=os.getpid()
 stop=threading.Event(); t=threading.Thread(target=monitor,args=(stop,),daemon=True); t.start()
 try:
  for item in RUNS:
   r=state['runs'].get(item['id'],{})
   if r.get('phase')=='complete' or r.get('reviewed_skip'): continue
   if r: raise RuntimeError('Inspect interrupted/failed run: '+item['id'])
   if (ROOT/'state/STOP-GPU-X8').exists(): state['phase']='paused'; checkpoint(state); return
   gc.current.clear(); gc.current.update(item)
   state.update(phase='running',current=item['id']); checkpoint(state)
   tune.run_one(dict(id=item['id'],args=item.get('args',[]),env=item.get('env',{}),sanity=item.get('sanity',False)),state)
   if state['runs'][item['id']]['phase']!='complete': state['phase']='paused-on-error'; checkpoint(state); return
  state.update(phase='screening-complete-review-required',current=None); checkpoint(state)
 finally: stop.set(); t.join(15)
if __name__=='__main__': main()
