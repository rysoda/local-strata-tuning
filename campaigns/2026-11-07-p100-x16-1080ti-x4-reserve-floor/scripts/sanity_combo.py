"""Standard functional/tool/recall checks plus one above-128K recall smoke."""
import json
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
repo = here.parents[2]
config, output = Path(sys.argv[1]), Path(sys.argv[2])
standard = output.with_suffix('.standard.json')
long = output.with_suffix('.256k.json')
code = subprocess.run([sys.executable, str(repo / 'tools/sanity.py'), str(config), str(standard)]).returncode
records = json.loads(standard.read_text())['checks'] if standard.exists() else []
if code == 0:
    code = subprocess.run([sys.executable, str(here / 'sanity256.py'), str(config), str(long)]).returncode
    if long.exists():
        records += json.loads(long.read_text())['checks']
passed = sum(bool(r.get('passed')) for r in records)
output.write_text(json.dumps(dict(checks=records, passed=passed, total=len(records)), indent=2), encoding='utf-8')
raise SystemExit(0 if code == 0 and passed == 7 and len(records) == 7 else 1)
