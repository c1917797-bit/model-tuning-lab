import json
from pathlib import Path
def undo(name,text):
 row=json.loads((Path(__file__).parent/'EDITS069_REPAIR1.json').read_bytes()).get(name)
 if row is None:return text
 if text!=row['after']:raise ValueError('exact repair1 source drift '+name)
 return row['before']
