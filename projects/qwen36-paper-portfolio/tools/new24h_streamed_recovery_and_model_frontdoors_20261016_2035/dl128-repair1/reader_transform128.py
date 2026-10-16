"""Change only typed recovery provenance joins; retain all101 domain predicates."""
import hashlib,json
from pathlib import Path
def transform(data):
 spec=json.loads((Path(__file__).parent/'READER_EDITS128.json').read_bytes())
 if len(data)!=spec['original_bytes']or hashlib.sha256(data).hexdigest()!=spec['original_sha256']:raise ValueError('exact original101R5 reader')
 text=data.decode('utf8')
 for old,new in spec['edits']:
  if text.count(old)!=1:raise ValueError('exact typed provenance replacement')
  text=text.replace(old,new)
 compile(text,'<recovered101reader128>','exec')
 if inverse(text)!=data:raise ValueError('whole original reader inverse')
 return text
def inverse(text):
 spec=json.loads((Path(__file__).parent/'READER_EDITS128.json').read_bytes())
 for old,new in reversed(spec['edits']):
  if text.count(new)!=1:raise ValueError('exact inverse multiplicity')
  text=text.replace(new,old)
 return text.encode('utf8')
