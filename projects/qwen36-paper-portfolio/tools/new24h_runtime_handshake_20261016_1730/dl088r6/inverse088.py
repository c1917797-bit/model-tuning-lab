import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
def verify(name):
 rows=json.loads((P/'INVERSE088.json').read_bytes());row=next(r for r in rows if r['file']==name)
 s=(P/name).read_text();append=row['appended_exact']
 if append:
  if not s.endswith(append):raise ValueError('exact appended wrapper')
  s=s[:-len(append)]
 for e in reversed(row['edits']):
  if s.count(e['new'])!=1:raise ValueError('exact inverse seam')
  s=s.replace(e['new'],e['old'])
 root=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())['root']
 oldroot='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-split-scale-numeric-new24h-v1-069-repair1'
 s=s.replace(root,oldroot)
 if hashlib.sha256(s.encode()).hexdigest()!=row['original']['sha256']:raise ValueError('undeclared source difference')
 return True
