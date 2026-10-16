"""Undo only recorded061 storage/interface/identity seams."""
import json
from pathlib import Path
def undo(name,text):
 from inverse069 import undo as back069
 text=back069(name,text)
 for before,after in reversed(json.loads((Path(__file__).parent/'EDITS061.json').read_bytes()).get(name,[])):
  if after not in text:raise ValueError('missing061 inverse '+name)
  text=text.replace(after,before)
 return text
