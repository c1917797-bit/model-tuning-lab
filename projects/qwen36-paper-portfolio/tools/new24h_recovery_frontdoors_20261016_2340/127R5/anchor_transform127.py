"""Exact-source, reversible PID-only anchor hydration optimization."""
import hashlib

ORIGINAL_SHA = '3822ea42c24ccd788eb858fc8a7e948d4e2a8c10824802ae261c74055fc6e898'
ORIGINAL_BYTES = 7119
EDITS = (
 ("previous={};ledgers={};anchors={}", "previous={};ledgers={};anchors={};anchor_pids={}"),
 ("previous[batch]=D.initial_anchor(t,anchor,sr,r,m,batch)",
  "previous[batch]=D.initial_anchor(t,anchor,sr,r,m,batch);anchor_pids[batch]=json.loads(json.dumps(anchor['pid'],allow_nan=False))"),
 ("raw(anchors[batch])['pid']", "anchor_pids[batch]"),
)

def transform(data):
 if len(data)!=ORIGINAL_BYTES or hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA:
  raise ValueError('exact reviewed original consumer required')
 text=data.decode('utf-8')
 for ordinal,(old,new) in enumerate(EDITS):
  if text.count(old)!=(2 if ordinal==2 else 1):
   raise ValueError('exact anchor edit multiplicity')
  text=text.replace(old,new)
 compiled=compile(text,'<anchor-consumer127>','exec')
 if inverse(text)!=data:raise ValueError('whole-body exact inverse')
 return text,compiled

def inverse(text):
 # Remove the assignment before replacing its shared lookup spelling.
 for ordinal in (1,2,0):
  old,new=EDITS[ordinal];text=text.replace(new,old)
 return text.encode('utf-8')
