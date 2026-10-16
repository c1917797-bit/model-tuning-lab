"""Exact anchor-optimized original plus invocation-local completed audit reuse."""
import hashlib
from anchor_transform127 import transform as anchors,inverse as undo_anchors
EDITS=(
 ('previous={};ledgers={};anchors={};anchor_pids={}', 'previous={};ledgers={};anchors={};anchor_pids={};memo=_memo_factory127r4(t,R,PRE,A,raw,checked,m,r)'),
 ("checked_side=A.audit(t,R,PRE,raw(side_ref),overflow=side_ref['path']in overflow)","checked_side=memo.initial(side_ref,overflow=side_ref['path']in overflow)"),
 ("  for batch in(1,16):", "  memo.seal_initial(r['actual_sidecar_records'])\n  for batch in(1,16):"),
 ("side=raw(cap['actual_sidecar043']);v=A.audit(t,R,PRE,side)","v=memo.mixed(cap['actual_sidecar043'])"),
 (" out=Path(a.output);", " memo.finish()\n out=Path(a.output);"),
)
def transform(raw):
 text,_=anchors(raw)
 for old,new in EDITS:
  if text.count(old)!=1:raise ValueError('one exact audit reuse seam')
  text=text.replace(old,new)
 if inverse(text)!=raw:raise ValueError('whole mathematical body inverse')
 return text
def inverse(text):
 for old,new in reversed(EDITS):
  if text.count(new)!=1:raise ValueError('one exact audit reuse inverse')
  text=text.replace(new,old)
 return undo_anchors(text)
class Memo:
 def __init__(self,t,R,PRE,A,raw,checked,m,r):
  import copy,json
  self.copy,self.key=copy.deepcopy,lambda q:json.dumps(q,sort_keys=True,separators=(',',':'))
  self.raw,self.checked=raw,checked;self.modules=(R,PRE,A);self.functions=(R.advance,R.restore,PRE.evaluate,PRE.bits,A.audit)
  self.audit=lambda s,**kw:A.audit(t,R,PRE,s,**kw)
  self.source_context=tuple(self.key(m['files'][n])for n in('oracle.py','precast.py','sidecar_audit.py','direct_round.py'))
  self.m=m;self.r=r;self.results={};self.inventory={self.key(q):q for q in r['actual_sidecar_records']};self.sealed=False
  if len(self.inventory)!=len(r['actual_sidecar_records']):raise ValueError('all unique original sidecar inventory')
  for n in('oracle.py','precast.py','sidecar_audit.py','direct_round.py'):checked(m['files'][n])
 def identity(self):
  R,PRE,A=self.modules
  if self.functions!=(R.advance,R.restore,PRE.evaluate,PRE.bits,A.audit)or self.source_context!=tuple(self.key(self.m['files'][n])for n in('oracle.py','precast.py','sidecar_audit.py','direct_round.py')):raise ValueError('fixed invocation audit mathematics')
 def initial(self,q,*,overflow):
  if self.sealed or type(overflow)is not bool or self.key(q)not in self.inventory:raise ValueError('initial exact sidecar role')
  self.identity();self.checked(q);key=(self.key(q),overflow)
  if key in self.results:raise ValueError('one complete initial audit per sidecar')
  value=self.audit(self.raw(q),overflow=overflow);self.results[key]=self.copy(value);return value
 def seal_initial(self,refs):
  if {self.key(q)for q in refs}!=set(self.inventory)or len(self.results)!=len(refs):raise ValueError('all unique initial mathematical audits complete')
  if not all(v['passed']is True for v in self.results.values()):raise ValueError('all initial audits must pass before role reuse')
  self.sealed=True
 def mixed(self,q):
  self.identity();self.checked(q)
  if not self.sealed or self.key(q)not in self.inventory or(self.key(q),False)not in self.results:raise ValueError('exact original nonoverflow mixed-role association')
  return self.copy(self.results[(self.key(q),False)])
 def finish(self):
  self.identity();self.results.clear()
