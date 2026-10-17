"""Host-only tree topology contract. No tensor/backend or BOLE math implementation.

Node positions use committed_length + depth, with first uncommitted nodes at
depth zero. The actual proposer/target-root convention must be adapted and
proved explicitly; this module never guesses it from a linear draft count.
"""
from dataclasses import dataclass
def need(v,s):
 if not v:raise ValueError(s)
def integer(v):return type(v)is int
@dataclass(frozen=True)
class Tree:
 request_ids:tuple
 generations:tuple
 committed_slots:tuple
 committed_lengths:tuple
 offsets:tuple
 parents:tuple
 tokens:tuple
 depths:tuple
 positions:tuple
 def validate(self,*,node_budget,max_depth=8,topk=4):
  b=len(self.request_ids);t=len(self.tokens)
  need(b>0 and all(type(q)is str and q for q in self.request_ids)and len(set(zip(self.request_ids,self.generations)))==b,'nonempty unique actual request generations')
  need(all(len(v)==b for v in(self.generations,self.committed_slots,self.committed_lengths)),'request metadata joins')
  need(all(integer(q)and q>=0 for v in(self.generations,self.committed_slots,self.committed_lengths)for q in v),'typed live request state')
  need(len(set(self.committed_slots))==b,'no two request owners share committed slot')
  need(integer(node_budget)and 0<t<=node_budget and integer(max_depth)and max_depth>0 and integer(topk)and topk>0,'explicit batch-wide tree budget')
  need(len(self.offsets)==b+1 and self.offsets[0]==0 and self.offsets[-1]==t and all(integer(q)for q in self.offsets)and all(a<c for a,c in zip(self.offsets,self.offsets[1:])),'nonempty request tree segments')
  need(all(len(v)==t for v in(self.parents,self.depths,self.positions))and all(integer(q)and q>=0 for q in self.tokens),'exact node fields')
  for r in range(b):
   start,end=self.offsets[r:r+2];children={}
   for i in range(start,end):
    p=self.parents[i];d=self.depths[i];pos=self.positions[i]
    need(integer(p)and(p==-1 or start<=p<i),'parent before child within same request; no sibling flattening')
    need(integer(d)and d==(0 if p==-1 else self.depths[p]+1)and d<max_depth,'parent-derived exact bounded depth')
    need(integer(pos)and pos==self.committed_lengths[r]+d,'branch positions follow depth, not flattened node ordinal')
    children[p]=children.get(p,0)+1;need(children[p]<=topk,'actual bounded branch fanout')
  return self
 def path(self,node):
  need(integer(node)and 0<=node<len(self.tokens),'actual selected node')
  out=[]
  while node!=-1:out.append(node);node=self.parents[node]
  return tuple(reversed(out))
 def ancestor_allow(self):
  """Canonical True=allowed. CANN mask polarity/layout is NOT inferred."""
  return tuple(tuple(j in self.path(i)for j in range(len(self.tokens)))for i in range(len(self.tokens)))
 def commit_path(self,request_index,node,*,actual_generation,actual_slot):
  r=request_index;need(integer(r)and 0<=r<len(self.request_ids),'request row')
  need(actual_generation==self.generations[r]and actual_slot==self.committed_slots[r],'stale generation or reused slot')
  if node is None:return ()
  need(self.offsets[r]<=node<self.offsets[r+1],'selected node belongs to request')
  return self.path(node)
 def conv_input_history(self,node,prefix_tail,node_inputs,width):
  """Reference GATHER only, not a conv/math oracle. Projected inputs stay raw."""
  need(integer(width)and width>=1 and len(prefix_tail)==width-1 and len(node_inputs)==len(self.tokens),'complete convolution pre-tree tail and every node input')
  history=tuple(prefix_tail)+tuple(node_inputs[j]for j in self.path(node))
  return history[-width:]
