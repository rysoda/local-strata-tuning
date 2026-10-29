"""Small functional/recall checks, not a quality benchmark; never execute model-generated code.
Run with Strata Control's Python while our server is loaded: sanity.py CONFIG OUTPUT.
"""
import json, os, pathlib, random, re, sys, time, urllib.request
cfg=json.loads(pathlib.Path(sys.argv[1]).read_text())
out=pathlib.Path(sys.argv[2])
records=[]

def save():
    out.write_text(json.dumps(dict(checks=records,passed=sum(r.get('passed',False) for r in records),total=len(records)),indent=2),encoding='utf-8')

def chat(name,prompt,expected=None,tools=None,validator=None):
    body=dict(model=cfg['model_name'],messages=[{'role':'user','content':prompt}],temperature=0,max_tokens=1024)
    if tools: body['tools']=tools
    rec=dict(name=name,expected=expected,started=time.strftime('%Y-%m-%d %H:%M:%S'))
    start=time.monotonic()
    try:
        req=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+cfg['api_key'],'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=1200) as r: result=json.load(r)
        rec['response']=result
        msg=result['choices'][0]['message']
        if validator:
            rec['passed']=validator(msg)
        else:
            text=(msg.get('content') or '').strip()
            text=re.sub(r'^```(?:json)?\s*|\s*```$','',text)
            rec['passed']=json.loads(text)==expected
    except Exception as e: rec.update(passed=False,error=str(e))
    rec['elapsed_s']=time.monotonic()-start
    records.append(rec); save()
    print(name,rec['passed'],flush=True)

chat('stable-unique','Implement stable unique mentally for [3,1,3,2,1,4,2]. Return only a JSON object with key result containing the output list.',{'result':[3,1,2,4]})
chat('python-alias-trace','What are a, b and c after this Python runs? a=[1,2]; b=a[:]; c=a; c.append(3). Return only JSON with keys a,b,c.',{'a':[1,2,3],'b':[1,2],'c':[1,2,3]})
chat('binary-search-trace','For the sorted list [1,3,3,3,8], return the bisect_left and bisect_right insertion indexes for 3. Output only JSON with keys left and right.',{'left':1,'right':4})
def tool_ok(msg):
    calls=msg.get('tool_calls',[])
    return len(calls)==1 and calls[0]['function']['name']=='lookup_issue' and json.loads(calls[0]['function']['arguments'])=={'issue_id':42}
chat('tool-call','Use lookup_issue to retrieve issue 42. Do not invent its contents; make the tool call now.',tools=[{'type':'function','function':{'name':'lookup_issue','description':'Retrieve an issue by numeric ID.','parameters':{'type':'object','properties':{'issue_id':{'type':'integer'}},'required':['issue_id']}}}],validator=tool_ok)

# Use the installed tokenizer, not a word-count approximation. Do not load target weights.
control=pathlib.Path(os.environ['LOCALAPPDATA'])/'Strata/components/control/0.1.51'
sys.path.insert(0,str(control/'tools'))
import strata_tokenizer as ST
tpath=pathlib.Path(cfg['tokenizer'])
vocab=json.loads((tpath/'vocab.json').read_text(encoding='utf-8'))
tokens=[None]*len(vocab)
for t,i in vocab.items(): tokens[i]=t
meta=json.loads((tpath/'tokenizer.json').read_text())
tok=ST.Tokenizer(tokens,(tpath/'merges.txt').read_text(encoding='utf-8').split('\n'),json.loads((tpath/'token_type.json').read_text()),meta.get('pre') or 'qwen35',meta.get('special_ids') or None)
rng=random.Random(781)
words='module value context index branch cache state result token window thread buffer memory request response function class method static input output'.split()
filler=' '.join(rng.choices(words,k=150000))
ids=tok.encode(filler)
for depth in (32000,119000):
    pieces=[]; prev=0
    expected={f'KEY_{i}':v for i,v in enumerate(('CEDAR-731','MAPLE-284','BIRCH-956'),1)}
    for index,fraction in enumerate((.1,.5,.9),1):
        at=int(depth*fraction)
        pieces.append(tok.decode(ids[prev:at])); pieces.append(f'\nThe recorded value of KEY_{index} is {expected[f"KEY_{index}"]}.\n'); prev=at
    pieces.append(tok.decode(ids[prev:depth]))
    prompt='Document retrieval sanity check. Read the records below; return only the three recorded KEY values as a JSON object.\n'+''.join(pieces)+'\nReturn exactly a JSON object with keys KEY_1, KEY_2, KEY_3 and their recorded values.'
    n=len(tok.encode(prompt))
    chat('recall-'+str(depth),prompt,expected)
    records[-1]['input_content_tokens']=n; save()
