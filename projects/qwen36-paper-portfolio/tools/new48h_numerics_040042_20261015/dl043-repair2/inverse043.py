"""Exact textual inverse of declared thin source edits, not numerical evidence."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
def verify(name):
 d=json.loads((P/'DELTA043.json').read_text(encoding='utf8'));s=(P/name).read_text(encoding='utf8')
 for a,b in reversed(d['edits'][name]):
  if b not in s:raise AssertionError('inverse seam missing '+name)
  s=s.replace(b,a)
 s=s.replace(d['new_root'],d['old_root'])
 original=(P/'fixtures043'/name).read_text(encoding='utf8')
 if s!=original:raise AssertionError('undeclared source difference '+name)
 return True
