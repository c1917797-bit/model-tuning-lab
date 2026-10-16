"""Greedy inclusive-root tree contract; not the linear Ascend sampler.
The root is a real scheduled input. A bonus output is NOT a processed input.
"""
from dataclasses import dataclass

def need(v,s):
    if not v:raise ValueError(s)

@dataclass(frozen=True)
class Decision:
    request_id:str
    generation:int
    slot:int
    root:int
    terminal:object
    processed_nodes:tuple
    accepted_draft_nodes:tuple
    emitted_tokens:tuple
    bonus_token:object
    cancelled:bool

def policy_check(policy):
    expected=dict(temperature=0,top_p=1,min_p=0,repetition_penalty=1,frequency_penalty=0,presence_penalty=0,grammar=False,custom_logits_processors=False)
    need(policy==expected,'only explicit neutral deterministic greedy policy; stochastic/path processors pending')

def select(tree,target_next_tokens,actual_root_tokens,*,policy,cancelled=()):
    policy_check(policy);tree.validate(node_budget=4096,max_depth=8,topk=4)
    need(len(target_next_tokens)==len(tree.tokens)and all(type(v)is int and v>=0 for v in target_next_tokens),'one validated target next-token result per node')
    need(len(actual_root_tokens)==len(tree.request_ids),'actual scheduled root inputs per request')
    need(set(cancelled)<=set(tree.request_ids),'only explicit cancelled live request IDs')
    decisions=[]
    for r,request in enumerate(tree.request_ids):
        begin,end=tree.offsets[r:r+2];roots=[n for n in range(begin,end)if tree.parents[n]==-1]
        need(len(roots)==1,'inclusive-root worker adapter requires exactly one mandatory root, not forest')
        root=roots[0];need(tree.tokens[root]==actual_root_tokens[r],'real scheduled root token does not match tree')
        children={n:{}for n in range(begin,end)}
        for node in range(begin,end):
            parent=tree.parents[node]
            if parent!=-1:
                need(tree.tokens[node]not in children[parent],'duplicate sibling token has ambiguous cache path')
                children[parent][tree.tokens[node]]=node
        if request in cancelled:
            decisions.append(Decision(request,tree.generations[r],tree.committed_slots[r],root,None,(),(),(),None,True));continue
        terminal=root;accepted=[]
        while target_next_tokens[terminal]in children[terminal]:
            terminal=children[terminal][target_next_tokens[terminal]];accepted.append(terminal)
        path=tree.path(terminal);bonus=target_next_tokens[terminal]
        emitted=tuple(tree.tokens[n]for n in accepted)+(bonus,)
        need(len(path)==len(emitted)==len(accepted)+1,'cache advancement includes root, output includes bonus, never process bonus twice')
        decisions.append(Decision(request,tree.generations[r],tree.committed_slots[r],root,terminal,path,tuple(accepted),emitted,bonus,False))
    return tuple(decisions)

def from_logits(t,tree,logits,node_ids,actual_root_tokens,*,policy,cancelled=()):
    need(logits.ndim==2 and logits.shape[0]==len(tree.tokens)and logits.dtype==t.float32,'actual target FP32 per-node logits')
    need(len(node_ids)==len(tree.tokens)and set(node_ids)==set(range(len(tree.tokens))),'exact once actual node-to-logit-row join')
    # Must occur BEFORE existing Ascend sampler nan_to_num. No fabricated
    # success from sanitized target logits is permitted.
    need(bool(t.isfinite(logits).all()),'raw target logits nonfinite before sampler')
    by_node=[None]*len(node_ids)
    for row,node in enumerate(node_ids):by_node[node]=int(logits[row].argmax().item())
    return select(tree,by_node,actual_root_tokens,policy=policy,cancelled=cancelled)

def scheduler_projection(tree,decisions):
    rows=[]
    for r,d in enumerate(decisions):
        if d.cancelled:rows.append(dict(request_id=d.request_id,cancelled=True,processed_delta=0,emitted_tokens=[]));continue
        scheduled=tree.offsets[r+1]-tree.offsets[r];drafts=scheduled-1;accepted=len(d.accepted_draft_nodes);rejected=drafts-accepted
        need(scheduled-rejected==len(d.processed_nodes),'same actual scheduler subtraction identity')
        rows.append(dict(request_id=d.request_id,generation=d.generation,slot=d.slot,scheduled_target_nodes=scheduled,scheduled_drafts_for_accounting_only=drafts,accepted_drafts=accepted,rejected_nodes=rejected,processed_delta=scheduled-rejected,emitted_tokens=list(d.emitted_tokens),bonus_is_not_processed=True))
    return rows
