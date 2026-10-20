"""Greedy tree selection restricted to nodes actually admitted by the scheduler."""
from acceptance import Decision
from model_entry import need

def decide(owner,tokens,target_next,scheduled_nodes,*,remaining_output_tokens):
 need(type(scheduled_nodes)is int and 1<=scheduled_nodes<=3,'one to three actual target rows')
 need(type(remaining_output_tokens)is int and remaining_output_tokens>=1,'actual positive remaining native output budget')
 need(len(tokens)==3 and tokens[1]!=tokens[2]and len(target_next)==scheduled_nodes and
      all(type(x)is int and x>=0 for x in(*tokens,*target_next)),'actual target IDs and distinct MTP children')
 terminal=0
 if remaining_output_tokens>=2:
  if scheduled_nodes>=2 and target_next[0]==tokens[1]:terminal=1
  elif scheduled_nodes>=3 and target_next[0]==tokens[2]:terminal=2
 accepted=()if terminal==0 else(terminal,)
 path=(0,)+accepted;bonus=target_next[terminal]
 emitted=tuple(tokens[n]for n in accepted)+(bonus,)
 return Decision(owner.request,owner.generation,owner.slot,0,terminal,path,accepted,emitted,bonus,False)

def native_compaction_order(scheduled_nodes,terminal):
 need(type(scheduled_nodes)is int and 1<=scheduled_nodes<=3 and type(terminal)is int and
      0<=terminal<scheduled_nodes,'only actual admitted terminal')
 return (0,2,1)if terminal==2 else tuple(range(scheduled_nodes))


