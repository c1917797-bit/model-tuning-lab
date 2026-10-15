"""Invert collection-policy statements only, retaining old failed R2 source."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
def undo(name,text):
 d=json.loads((P/'COLLECTION_REPAIR3_INVERSE.json').read_bytes())
 if name not in d['edits']:return text
 for before,after in reversed(d['edits'][name]):
  if text.count(after)!=1:raise ValueError('unique collection-only inverse '+name)
  text=text.replace(after,before,1)
 old=(P/'fixtures_repair3'/name).read_bytes()
 if hashlib.sha256(old).hexdigest()!=d['baseline_sha256'][name]or text.encode()!=old:raise ValueError('undeclared R2 source/math/input/controller change '+name)
 return text
def verify():
 d=json.loads((P/'COLLECTION_REPAIR3_INVERSE.json').read_bytes())
 for name in d['edits']:undo(name,(P/name).read_text(encoding='utf8'))
 return True
