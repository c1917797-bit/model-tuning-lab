import json
from pathlib import Path
def undo(name,text):
 from inverse069repair1 import undo as back
 text=back(name,text)
 for a,b in reversed(json.loads((Path(__file__).parent/'EDITS069.json').read_bytes()).get(name,[])):
  if b not in text:raise ValueError('missing069 inverse '+name)
  text=text.replace(b,a)
 return text
