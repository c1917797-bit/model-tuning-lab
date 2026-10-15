"""Independent packed-C1 receipt/order audit; not tensor or quality proof."""
import math
from collections import defaultdict

def audit_packed_c1(events,workers,*,manifest_sha256,linear_layers,requests,enabled=True,
                    skipped_body_tokens=16376,state_passes=3,seed_mode=None,head_geometry=None):
    if type(state_passes)is not int or state_passes not in (2,3):
        raise ValueError('frozen state-pass count required')
    if state_passes==2 and seed_mode!='actual_prefix_terminal':
        raise ValueError('two-pass route requires actual prefix seed mode')
    layers=set(linear_layers);wanted=set(requests)
    if (set(workers)!=set(range(4)) or len(set(workers.values()))!=4
            or len(layers)!=48 or not wanted or len(wanted)!=len(requests)):
        raise ValueError("exact four workers,48 layers and unique target requests required")
    if any(type(p)is not int or p<=0 for p in workers.values()):
        raise ValueError("independently verified PID map required")
    if any(not isinstance(s,str) or not s for s in layers|wanted):
        raise ValueError("nonempty layer/request identities required")
    installs=[e for e in events if e.get("event")=="compact_hypic_hooks_installed"]
    if len(installs)!=4 or {e.get("pid") for e in installs}!=set(workers.values()):
        raise ValueError("exact four activations required")
    for e in installs:
        if (e.get("manifest_sha256")!=manifest_sha256 or e.get("default_disabled")is not True
                or e.get("c1_packed_wave")is not enabled):
            raise ValueError("explicit source-bound packed flag required")
        if enabled and any(e.get(k)is not True for k in (
                "native_decode_batch","c1_layer_completion_barrier","c1_layer_shadow_validation")):
            raise ValueError("packed canary requires all three controls")
    new_kinds={"c1_packed_wave_prepared","c1_packed_wave_shadow_checked"}
    if not enabled:
        if any(e.get("event") in new_kinds for e in events):
            raise ValueError("packed execution marker in disabled control")
        return {"packed_disabled_verified":True,"workers":workers}
    public=defaultdict(set);generation={};prepared={};gates={};commits=defaultdict(dict);shadows=defaultdict(dict)
    kinds=new_kinds|{"compact_public_state_published","c1_layer_precommit_validated",
                      "compact_gdn_body_composed","mixed_native_gdn_completed"}
    def members(value):
        if (not isinstance(value,list) or not 1<=len(value)<=32 or len(set(value))!=len(value)
                or any(not isinstance(x,str) or not x for x in value)):
            raise ValueError("bounded exact request membership required")
        return set(value)
    for index,e in enumerate(events):
        kind=e.get("event")
        if kind not in kinds:continue
        rank=e.get("rank");layer=e.get("layer")
        if (type(rank)is not int or rank not in workers or e.get("pid")!=workers[rank]
                or e.get("manifest_sha256")!=manifest_sha256 or layer not in layers):
            raise ValueError("worker/source/expected layer mismatch")
        if kind=="compact_public_state_published":
            if type(e.get('generation'))is not int or e['generation']<1:
                raise ValueError('exact public material generation required')
            public[rank].add(layer);generation[(rank,layer)]=e['generation'];continue
        if type(e.get("step"))is not int or e["step"]<0:raise ValueError("exact step required")
        key=(rank,e["step"],layer)
        if kind=="c1_packed_wave_prepared":
            group=members(e.get("requests"))
            if head_geometry is not None:
                actual=e.get('head_geometry')
                if (not isinstance(actual,dict) or set(actual)!=set(head_geometry)
                        or any(type(actual[k])is not type(v) or actual[k]!=v
                               for k,v in head_geometry.items())):
                    raise ValueError('source-bound native grouped head geometry required')
            if key in prepared:raise ValueError("duplicate packed preparation")
            n=e.get("windows");tokens=e.get("packed_tokens")
            if (type(n)is not int or not len(group)<=n<=2*len(group)
                    or type(tokens)is not int or not n<=tokens<=40960
                    or type(e.get("shared_wy_preparations"))is not int or e["shared_wy_preparations"]!=1
                    or type(e.get("state_passes"))is not int or e["state_passes"]!=state_passes
                    or seed_mode is not None and e.get('seed_mode')!=seed_mode
                    or e.get("actual_slot_commit")!="not_started"):
                raise ValueError("complete packed preparation geometry/call stages required")
            prepared[key]=(index,e,group)
        elif kind=="c1_packed_wave_shadow_checked":
            rid=e.get("request_id");members(e.get("group_requests"))
            if not isinstance(rid,str) or not rid or rid in shadows[key]:
                raise ValueError("duplicate/invalid packed shadow request")
            metrics=e.get("metrics",[])
            if (e.get("passed")is not True or e.get("atol")!=.01 or e.get("rtol")!=.003
                    or e.get("private_buffers")is not True or e.get("actual_slot_commit")!="not_started"
                    or len(metrics)!=3 or {m.get("tensor") for m in metrics}!={"output","state","conv"}):
                raise ValueError("frozen full-private shadow required")
            for m in metrics:
                if m.get("passed")is not True or any(
                    type(m.get(k))not in (int,float) or not math.isfinite(m[k]) or m[k]<0
                    for k in ("max_abs","rms","max_scaled")) or m["max_scaled"]>1:
                    raise ValueError("nonfinite/failed shadow residual")
            shadows[key][rid]=(index,e)
        elif kind=="c1_layer_precommit_validated":
            group=members(e.get("requests"))
            if (key in gates or e.get("finite")is not True or e.get("actual_slot_commit")!="not_started"
                    or type(e.get("tensors"))is not int or not 3<=e["tensors"]<=3*len(group)):
                raise ValueError("complete all-request finite gate required")
            gates[key]=(index,e,group)
        else:
            rid=e.get("request_id")
            if (not isinstance(rid,str) or not rid or rid in commits[key]
                    or e.get("finite")is not True or type(e.get("slot"))is not int or e["slot"]<0):
                raise ValueError("duplicate/nonfinite or invalid actual slot receipt")
            commits[key][rid]=(index,e)
            if kind=='compact_gdn_body_composed' and (
                    (rank,layer) not in generation or e.get('generation')!=generation[(rank,layer)]):
                raise ValueError('hot commit not bound to preceding current public generation')
    if set(gates)!=set(commits):raise ValueError("finite gate/completed group mismatch")
    coverage=defaultdict(set);multi_shadow=defaultdict(set)
    for key,(gate_index,gate,group) in gates.items():
        if group!=set(commits[key]) or any(i<=gate_index for i,e in commits[key].values()):
            raise ValueError("actual commit before complete exact finite gate")
        slots=[e["slot"] for _,e in commits[key].values()]
        if len(slots)!=len(set(slots)):raise ValueError("actual state slot alias")
        for rid,(index,e) in commits[key].items():
            if e["event"]=="compact_gdn_body_composed":
                if e.get("skipped_body_tokens")!=skipped_body_tokens:raise ValueError("hot body size drift")
                if key not in prepared or rid not in prepared[key][2]:
                    raise ValueError("hot commit without packed preparation")
                if rid in wanted:coverage[(key[0],rid)].add(key[2])
    for key,(index,e,group) in prepared.items():
        if key not in gates or not group<=gates[key][2] or index>=gates[key][0]:
            raise ValueError("packed preparation not before exact finite gate")
    for key,entries in shadows.items():
        if key not in prepared or set(entries)!=prepared[key][2]:
            raise ValueError("partial shadow group or no completed packed preparation")
        for rid,(index,e) in entries.items():
            if (set(e["group_requests"])!=prepared[key][2] or index>=prepared[key][0]
                    or rid not in commits[key]):
                raise ValueError("shadow request/group/order mismatch")
        hot=[rid for rid in entries if commits[key][rid][1]["event"]=="compact_gdn_body_composed"]
        if len(hot)>=2:multi_shadow[key[0]].add(key[2])
    for rank in range(4):
        if public[rank]!=layers or multi_shadow[rank]!=layers:
            raise ValueError("all48 public layers and multi-hot serialized shadows required per rank")
        if any(coverage[(rank,rid)]!=layers for rid in wanted):
            raise ValueError("every target request must prove packed hot path on all48layers")
    return {"packed_c1_verified":True,"workers":workers,"requests":len(wanted),
            "packed_groups":len(prepared),"shadow_requests":sum(map(len,shadows.values())),
            "multi_hot_shadow_layers":{rank:len(multi_shadow[rank]) for rank in workers},
            "scope":"source-bound packed call-stage/serial-shadow/private precommit receipts; raw tensors, physical mapping, transport, release, performance and task quality separate"}
