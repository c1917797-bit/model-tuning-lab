"""Reverse declared source/identity seams; not a numerical qualification."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
def undo(name,text):
 edits=json.loads((P/'EDITS052.json').read_bytes()).get(name,[])
 for before,after in reversed(edits):
  if after not in text:raise ValueError('missing declared052 inverse seam '+name)
  text=text.replace(after,before)
 return text
