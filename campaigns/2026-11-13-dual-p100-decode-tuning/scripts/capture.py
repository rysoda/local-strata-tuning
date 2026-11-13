"""Read-only provenance capture; never starts/stops an inference server."""
import copy, hashlib, json, os, pathlib, subprocess, sys, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
sys.path.insert(0,str(REPO/'tools'))
import benchmark as bm
local=pathlib.Path(os.environ['LOCALAPPDATA'])/'Strata'
cfg=bm.load(local/'launch/iq3_s-128k.json')
private=ROOT/'configs/private'
bm.save(private/'original-installed.json',cfg)
startup=pathlib.Path(os.environ['APPDATA'])/'Microsoft/Windows/Start Menu/Programs/Startup/strata-start.bat'
(private/'original-startup.bat').write_bytes(startup.read_bytes())
engine=local/'components/engine/0.1.59-windows-x86_64-cuda-cuda12/strata.exe'
control=local/'components/control/0.1.57'
for name,cmd in [('engine-help',[str(engine),'--help']),('hardware',['nvidia-smi','-q']),('cpu-ram-os',['powershell.exe','-NoProfile','-Command','Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | Format-List; Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory | Format-List; Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,LastBootUpTime | Format-List']),('processes',['powershell.exe','-NoProfile','-Command','Get-CimInstance Win32_Process | Where-Object { $_.Name -match "strata|python|betterbench" } | Select-Object ProcessId,Name,CommandLine | Format-List'])]:
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
    (ROOT/f'results/{name}.txt').write_text(p.stdout+p.stderr,encoding='utf-8')
for route in ('health','metrics'):
    bm.save(ROOT/f'results/original.{route}.json',bm.request('/'+route,cfg))
(rootlog:=ROOT/'results/original-startup.engine.log').write_bytes((local/'launch/iq3_s-128k.engine.log').read_bytes())
for doc in ('SETTINGS.md','OLDER_GPUS.md','MULTI_GPU.md','SPLIT_ENGINE.md','DETAILS.md'):
    url='https://raw.githubusercontent.com/Niko1221/Strata/v0.2.13/docs/'+doc
    with urllib.request.urlopen(url,timeout=45) as response: data=response.read()
    (ROOT/'results'/('upstream-v0.2.13-'+doc)).write_bytes(data)
base=copy.deepcopy(cfg)
# Keep original diagnostic separate. No projection is used in the tuning comparison.
a=base['args']
for flag,count in [('--control-vector-scaled',1),('--control-vector-layer-range',2),('--cvec-mode',1),('--cvec-dir',1)]:
    if flag in a:
        at=a.index(flag);del a[at:at+count+1]
base.update(exe=str(engine),cwd=str(control),host='127.0.0.1',parallel=1,gpu=[0,1],gpu_order='as_given',layer_split='36',split_engine='off')
base['env'].update(STRATA_ROUTE_PRIOR='0',STRATA_ROUTE_TAIL_SKIP='0')
base['log']=str(ROOT/'results/reference.engine.log')
bm.save(private/'baseline.json',base)
# Pin executable/server/workload hashes; model files are size/mtime checked without rereading 80GB.
files=[engine,control/'serve/server.py',control/'strata.py',bm.BB,bm.WORKLOAD,pathlib.Path(a[a.index('--expert-profile')+1])]
models=[pathlib.Path(a[a.index(flag)+1]) for flag in ('--native','--ple-gguf')]
models+=list(pathlib.Path(a[a.index('--pack')+1]).glob('*'))
models+=list(pathlib.Path(a[a.index('--mtp')+1]).glob('*'))
models=[p for p in models if p.is_file()]
frozen={'files':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files], 'model_files':[{'path':str(p),'size':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in models], 'baseline_sha256':hashlib.sha256((private/'baseline.json').read_bytes()).hexdigest()}
bm.save(ROOT/'results/frozen-inputs.json',frozen)
print('Captured original settings, health, hardware, current release docs; baseline isolated and projection-free.')
print('Installed binary option strings:',{k:k.encode() in engine.read_bytes() for k in ('STRATA_DOWN_WS','STRATA_PATTN_SM60','STRATA_MMQ_WS','STRATA_ARENA_PIN_GIB','STRATA_ADAPT_FETCH')})
