"""Isolated, sequential diagnostic arms; errors pause, never retry incomplete runs.
Usage: run.py reference36 split24 ...; no arguments is read-only status.
A completed run is skipped. --finish closes campaign only after report review.
"""
import copy, csv, hashlib, json, msvcrt, os, pathlib, re, socket, subprocess, sys, threading, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
sys.path.insert(0,str(REPO/'tools'))
import benchmark as bm
STATE=ROOT/'state/queue-state.json'
ARMS={
 'reference36-v2':{'split':36},
 'split24-v2':{'split':24},
 'split24-pipeline':{'split':24,'args':['--pipeline-windows','2']},
 'split24-downws':{'split':24,'env':{'STRATA_DOWN_WS':'1'}},
 'split24-pin0':{'split':24,'env':{'STRATA_ARENA_PIN_GIB':'0'}},
 'split24-pipeline-stage0':{'split':24,'args':['--pipeline-windows','2'],'env':{'STRATA_MTP_STAGE0':'1'}},
 'split24-pipeline-stage0-pin0':{'split':24,'args':['--pipeline-windows','2'],'env':{'STRATA_MTP_STAGE0':'1','STRATA_ARENA_PIN_GIB':'0'}},
 'confirm-candidate-a':{'split':24,'args':['--pipeline-windows','2'],'env':{'STRATA_MTP_STAGE0':'0'}},
 'confirm-reference':{'split':36,'sanity':True},
 'confirm-candidate-b':{'split':24,'args':['--pipeline-windows','2'],'env':{'STRATA_MTP_STAGE0':'0'},'sanity':True},
}
GPU_FIELDS='timestamp,index,uuid,temperature.gpu,clocks.sm,power.draw,utilization.gpu,memory.used,memory.free,pcie.link.gen.current,pcie.link.width.current,clocks_event_reasons.sw_thermal_slowdown,clocks_event_reasons.hw_thermal_slowdown'

def checkpoint(state):
    current=state.get('current')
    if current and state['runs'].get(current,{}).get('phase')=='benchmark-running':
        arm=ARMS[current]
        text=(ROOT/f'results/{current}.engine.log').read_text(encoding='utf-8',errors='replace')
        command=next((line for line in text.splitlines() if 'engine started:' in line),'')
        if 'control-vector' in command or 'cvec' in command or f"--layer-split {arm['split']} " not in command:
            raise RuntimeError('Effective engine command differs from planned arm; refusing benchmark')
        if '--pipeline-windows' in arm.get('args',[]) and '--pipeline-windows 2' not in command:
            raise RuntimeError('Pipeline option absent from effective command')
    state['updated']=time.strftime('%Y-%m-%d %H:%M:%S')
    bm.save(STATE,state)
    lines=['# Dual P100 tuning — live results','','All main arms: IQ3_S, 256K, int8 KV, full experts, no projection.','','| Run | Phase | Decode | Prefill |','|---|---|---:|---:|']
    for name,r in state['runs'].items():
        m=r.get('metrics',{}); lines.append(f"| {name} | {r['phase']} | {m.get('decode','—')} | {m.get('prefill','—')} |")
    (ROOT/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    manifest=bm.load(ROOT/'manifest.json'); manifest.update(status=state['phase'],completed_benchmarks=sum(r['phase']=='complete' for r in state['runs'].values()),rejected_configurations=sum(r['phase'] in ('invalid','failed','sanity-failed') for r in state['runs'].values()))
    bm.save(ROOT/'manifest.json',manifest)

def verify_frozen():
    frozen=bm.load(ROOT/'results/frozen-inputs.json')
    if hashlib.sha256((ROOT/'configs/private/baseline.json').read_bytes()).hexdigest()!=frozen['baseline_sha256']: raise RuntimeError('Baseline changed')
    for row in frozen['files']:
        if hashlib.sha256(pathlib.Path(row['path']).read_bytes()).hexdigest()!=row['sha256']:raise RuntimeError('Input changed: '+row['path'])
    for row in frozen['model_files']:
        st=pathlib.Path(row['path']).stat()
        if (st.st_size,st.st_mtime_ns)!=(row['size'],row['mtime_ns']):raise RuntimeError('Model changed: '+row['path'])
    raw=subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_model.current,pcie.link.gen.current,pcie.link.width.current','--format=csv,noheader,nounits'],text=True)
    rows=[[x.strip() for x in line.split(',')] for line in raw.strip().splitlines()]
    if rows!=[['Tesla P100-PCIE-16GB','TCC','3','8']]*2:raise RuntimeError('Hardware/topology changed: '+raw)

def idle():
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',8080))==0:raise RuntimeError('Port 8080 occupied; stop verified user server explicitly, no automatic kill')
    command='Get-CimInstance Win32_Process | Where-Object { $_.Name -match "^strata.*\\.exe$|^betterbench" -or ($_.Name -match "^python.*\\.exe$" -and $_.CommandLine -match "serve.server|server.py|strata_control.runtime|scripts[\\\\/](run|quick|continue).py") } | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json'
    raw=subprocess.check_output(['powershell.exe','-NoProfile','-Command',command],text=True).strip()
    rows=json.loads(raw) if raw else [];rows=[rows] if isinstance(rows,dict) else rows
    if any(row['ProcessId']!=os.getpid() for row in rows):raise RuntimeError('Competing process found; nothing killed')

def make_config(label,arm):
    cfg=json.loads((ROOT/'configs/private/baseline.json').read_text())
    cfg['layer_split']=str(arm['split'])
    cfg['args'][cfg['args'].index('--layer-split')+1]=str(arm['split'])
    cfg['args']+=arm.get('args',[]); cfg['env'].update(arm.get('env',{}))
    cfg['log']=str(ROOT/f'results/{label}.engine.log')
    assert cfg['args'][cfg['args'].index('--max-context')+1]=='262144'
    assert cfg['env']['STRATA_ROUTE_PRIOR']==cfg['env']['STRATA_ROUTE_TAIL_SKIP']=='0'
    assert not any('cvec' in a or 'control-vector' in a for a in cfg['args'])
    return cfg

def inspect(label,arm,state):
    r=state['runs'][label]
    if r['phase']!='complete' or not r['metrics']['valid']:raise RuntimeError('Incomplete benchmark: '+label+': '+r.get('error',r['phase']))
    text=(ROOT/f'results/{label}.engine.log').read_text(encoding='utf-8',errors='replace')
    for required in ('session is up (engine 0.1.59)','draft layer loaded','KV streaming: 32768 of 262144 cells',f"layers 0-{arm['split']-1} (CUDA0), {arm['split']}-47 (CUDA1)"):
        if required not in text:raise RuntimeError('Missing actual setting: '+required)
    if re.search(r'non-finite logits|fatal\s*:|out of memory|engine stopped unexpectedly',text,re.I):raise RuntimeError('Engine error requires review')
    if text.count('engine started:')!=1:raise RuntimeError('Unexpected restart/fallback')
    command=next(line for line in text.splitlines() if 'engine started:' in line)
    if 'control-vector' in command or 'cvec' in command:raise RuntimeError('Projection contaminated comparison')
    health=bm.load(ROOT/f'results/{label}.health.json')
    if health.get('max_context')!=262144:raise RuntimeError('Actual context changed')
    with (ROOT/f'results/{label}.hardware.csv').open() as f:rows=list(csv.DictReader(f,skipinitialspace=True))
    summary={}
    for card in ('0','1'):
        samples=[row for row in rows if row.get('index')==card]
        if not samples:raise RuntimeError('Missing GPU telemetry')
        maximum=max(float(row['temperature.gpu']) for row in samples)
        thermal=sum(row['clocks_event_reasons.sw_thermal_slowdown']=='Active' or row['clocks_event_reasons.hw_thermal_slowdown']=='Active' for row in samples)
        if maximum>=85 or thermal:raise RuntimeError('Thermal condition invalid')
        summary[card]={'max_temp_c':maximum,'min_free_mib':min(float(row['memory.free [MiB]'].split()[0]) for row in samples),'thermal_active_samples':thermal}
    r['hardware']=summary
    r['reviewed']=True
    bm.save(ROOT/f'results/{label}.summary.json',r)

class ProcessTools:
    """Expand the shared smoke hook without modifying repository shared mechanics."""
    def __init__(self,state):self.state=state
    def __getattr__(self,name):return getattr(subprocess,name)
    def run(self,cmd,*args,**kwargs):
        if isinstance(cmd,list) and len(cmd)>1 and pathlib.Path(cmd[1])==REPO/'tools/sanity.py':
            cmd=[cmd[0],str(ROOT/'scripts/sanity_combo.py'),*cmd[2:]]
            kwargs.pop('timeout',None)
            p=subprocess.Popen(cmd,*args,**kwargs)
            self.state['runs'][self.state['current']]['sanity_pid']=p.pid;checkpoint(self.state)
            try:return subprocess.CompletedProcess(cmd,p.wait(timeout=10800))
            finally:
                if p.poll() is None:
                    subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    p.wait(timeout=30)
        return subprocess.run(cmd,*args,**kwargs)

def main():
    state=bm.load(STATE)
    if not sys.argv[1:]:print(json.dumps(state,indent=2));return
    if state['phase']=='complete':print('Campaign complete; no work started');return
    if state['phase'] in ('error','running') or any(r['phase'] not in ('complete','invalid') or not r.get('reviewed') for r in state['runs'].values()):raise RuntimeError('Ambiguous/error run requires explicit review; refusing restart')
    labels=sys.argv[1:]
    for label in labels:
        if label not in ARMS:raise RuntimeError('Unknown arm: '+label)
    with open(ROOT/'state/runner.lock','a+b') as lock:
        lock.write(b'0');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        baseline=bm.load(ROOT/'configs/private/baseline.json')
        bm.configure(ROOT,baseline['cwd']);bm.checkpoint=checkpoint
        original_load=bm.load;original_process=bm.subprocess;active={}
        bm.subprocess=ProcessTools(state)
        bm.load=lambda p:copy.deepcopy(active['cfg']) if pathlib.Path(p)==ROOT/'configs/private/baseline.json' else original_load(p)
        try:
            for label in labels:
                if label in state['runs']:
                    if state['runs'][label]['phase'] in ('complete','invalid') and state['runs'][label].get('reviewed'):continue
                    raise RuntimeError('Incomplete existing attempt')
                if (ROOT/'state/STOP').exists():state.update(phase='paused',current=None);checkpoint(state);return
                idle();verify_frozen()
                if list((ROOT/'results').glob(label+'.*')):raise RuntimeError('Orphan evidence requires review')
                arm=ARMS[label]; active['cfg']=make_config(label,arm)
                bm.save(ROOT/f'results/{label}.definition.json',arm)
                state.update(phase='running',current=label,supervisor_pid=os.getpid());checkpoint(state)
                with open(ROOT/f'results/{label}.hardware.csv','x') as f:
                    sampler=subprocess.Popen(['nvidia-smi','--query-gpu='+GPU_FIELDS,'--format=csv','--loop=2'],stdout=f,stderr=subprocess.STDOUT)
                    try:bm.run_one({'id':label,'args':[],'env':{},'sanity':arm.get('sanity',False)},state)
                    finally:
                        if sampler.poll() is None:sampler.terminate()
                        sampler.wait(timeout=15)
                inspect(label,arm,state);state.update(phase='paused',current=None);checkpoint(state)
                print(label,json.dumps(state['runs'][label]['metrics']),flush=True)
        except BaseException as error:
            state.update(phase='error',error=str(error));checkpoint(state);raise
        finally:bm.load=original_load;bm.subprocess=original_process
if __name__=='__main__':main()
