"""One above-128K recall smoke; no generated code is executed."""
import hashlib
import json
from pathlib import Path
import random
import re
import sys
import time
import urllib.request

cfg = json.loads(Path(sys.argv[1]).read_text())
output = Path(sys.argv[2])
sys.path.insert(0, str(Path(cfg['cwd']) / 'tools'))
import strata_tokenizer as ST
p = Path(cfg['tokenizer'])
vocab = json.loads((p / 'vocab.json').read_text(encoding='utf-8'))
tokens = [None] * len(vocab)
for t, i in vocab.items():
    tokens[i] = t
meta = json.loads((p / 'tokenizer.json').read_text())
tok = ST.Tokenizer(tokens, (p / 'merges.txt').read_text(encoding='utf-8').split('\n'), json.loads((p / 'token_type.json').read_text()), meta.get('pre') or 'qwen35', meta.get('special_ids') or None)
rng = random.Random(78572)
words = 'module value context index branch cache state result token window thread buffer memory request response function class method static input output'.split()
ids = tok.encode(' '.join(rng.choices(words, k=300000)))
depth = 230000
if len(ids) < depth:
    raise RuntimeError('Insufficient tokenizer-generated filler')
expected = {'KEY_1': 'ALDER-628', 'KEY_2': 'ASPEN-419', 'KEY_3': 'WILLOW-853'}
pieces = []
prev = 0
for i, fraction in enumerate((.1, .5, .9), 1):
    at = int(depth * fraction)
    pieces += [tok.decode(ids[prev:at]), f'\nThe recorded value of KEY_{i} is {expected[f"KEY_{i}"]}.\n']
    prev = at
pieces.append(tok.decode(ids[prev:depth]))
prompt = 'Document retrieval sanity check. Return only the three recorded KEY values as a JSON object.\n' + ''.join(pieces) + '\nReturn exactly a JSON object with keys KEY_1, KEY_2, KEY_3 and their recorded values.'
n = len(tok.encode(prompt))
if not 131072 < n < 258000:
    raise RuntimeError('Unexpected actual content token count')
record = dict(name='recall-above-128k', input_content_tokens=n, expected=expected, prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), passed=False)
output.write_text(json.dumps(dict(checks=[record], passed=0, total=1), indent=2))
start = time.monotonic()
try:
    body = dict(model=cfg['model_name'], messages=[dict(role='user', content=prompt)], temperature=0, max_tokens=1024)
    req = urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions', data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + cfg['api_key'], 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=7200) as response:
        result = json.load(response)
    record['response'] = result
    text = result['choices'][0]['message'].get('content') or ''
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip())
    actual = result.get('usage', {}).get('prompt_tokens', 0)
    record['passed'] = json.loads(text) == expected and actual > 131072 and abs(actual - n) < 1024
except Exception as error:
    record['error'] = str(error)
record['elapsed_s'] = time.monotonic() - start
output.write_text(json.dumps(dict(checks=[record], passed=int(record['passed']), total=1), indent=2), encoding='utf-8')
print('Above-128K recall:', record['passed'], 'content tokens:', n, flush=True)
raise SystemExit(0 if record['passed'] else 1)
