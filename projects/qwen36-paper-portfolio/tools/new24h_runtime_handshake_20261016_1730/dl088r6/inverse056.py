"""Reverse only new24h source/identity/authorization seams."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
def undo(name,text):
 from inverse061 import undo as back061
 text=back061(name,text)
 for a,b in reversed(json.loads((P/'EDITS056.json').read_bytes()).get(name,[])):
  if b not in text:raise ValueError('missing056 inverse seam '+name)
  text=text.replace(b,a)
 return text
def through052(name,text):
 from inverse052 import undo as old
 return old(name,undo(name,text))
