import json, os, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
control = pathlib.Path(os.environ['LOCALAPPDATA'])/'Strata/components/control/0.1.51'
items = []
def add(id, family, flag=None, value=None, env=None):
    args = [] if flag is None else [flag] + ([] if value is None else [str(value)])
    items.append(dict(id=id, family=family, args=args, env=env or {}))
add('quality-reference', 'reference')
add('ple-mmap', 'ple', '--ple-io', 'mmap')
add('reserve-1400', 'reserve', '--vram-reserve-mib', 1400)
add('kv-resident-20480', 'kv', '--kv-resident', 20480)
for v in ('last','sibling'): add('host-'+v,'host','--host-core',v)
for v in (4,3): add('workers-'+str(v),'workers','--pool-workers',v)
for v in (36,72): add('tasks-'+str(v),'tasks','--pool-tasks',v)
for v in (0.15,0.40): add('pcie-'+str(v),'pcie','--pcie-frac',v)
add('pcie-balance','pcie',env={'STRATA_PCIE_BALANCE':'1'})
for v in (3,5): add('spec-'+str(v),'spec','--spec',v)
for v in (0.3,0.7): add('confidence-'+str(v),'confidence','--spec-min-p',v)
add('lookup-chain-2','lookup','--lookup-chain',2)
add('suffix-off','suffix','--suffix-draft',0)
add('draft-english','draft-vocab','--mtp-draft-vocab',control/'data/draft_vocab_en.bin')
add('draft-q4','draft-quant','--mtp-q4','all')
for v in (1,8): add('adapt-every-'+str(v),'adapt-every','--adapt-every',v)
for v in (48,160): add('adapt-swaps-'+str(v),'adapt-swaps','--adapt-swaps',v)
add('adapt-decay-09','adapt-decay','--adapt-decay',0.9)
add('adapt-async','adapt-mode','--adapt-async',1)
add('adapt-overlap','adapt-mode',env={'STRATA_ADAPT_OVERLAP':'1'})
for v in (4096,2048): add('prefill-'+str(v),'prefill','--prefill',v)
add('head-alias','head-alias','--prefill-head-alias')
# Late reference quantifies drift; it is not an extra parameter.
add('quality-reference-repeat','reference')
path = root/'experiments.json'
if path.exists(): raise SystemExit('Refusing to overwrite existing experiment manifest')
path.write_text(json.dumps(items, indent=2))
print(len(items), 'experiments written')
