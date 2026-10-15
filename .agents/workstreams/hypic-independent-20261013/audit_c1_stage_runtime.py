"""Independent link of one selected-head sample to actual failed receipts."""
import json,re,math
from pathlib import Path
from audit_c1_stage_capture import audit_capture

LAYER="language_model.model.layers.0.linear_attn"

def audit_runtime_capture(events,host_raw,*,manifest_sha256):
    captures=[(i,e) for i,e in enumerate(events) if e.get("event")=="c1_first_divergence_capture"]
    if len(captures)!=1:raise ValueError("exactly one bounded failed capture receipt required")
    index,e=captures[0]
    if (e.get("rank")!=0 or type(e.get("rank"))is not int or e.get("layer")!=LAYER
            or type(e.get("step"))is not int or e["step"]<0
            or e.get("manifest_sha256")!=manifest_sha256
            or e.get("actual_slot_commit")!="not_started"
            or e.get("complete")is False or type(e.get("pid"))is not int):
        raise ValueError("source-bound rank0/layer0/precommit capture receipt required")
    installs=[x for x in events if x.get("event")=="compact_hypic_hooks_installed"]
    if (len(installs)!=4 or len({x.get("pid") for x in installs})!=4
            or e["pid"] not in {x.get("pid") for x in installs}
            or any(x.get("manifest_sha256")!=manifest_sha256
                   or x.get("c1_first_divergence")is not True
                   or x.get("c1_packed_wave")is not True for x in installs)):
        raise ValueError("four explicit source-bound diagnostic worker installations required")
    public=[x for x in events[:index] if x.get("event")=="compact_public_state_published"
            and x.get("rank")==0 and x.get("layer")==LAYER]
    if not public:raise ValueError("preceding rank0 public material required")
    public=public[-1]
    if public.get("pid")!=e["pid"] or public.get("manifest_sha256")!=manifest_sha256:
        raise ValueError("independent rank/PID/source association mismatch")
    failures=[x for x in events[:index] if x.get("event")=="c1_packed_wave_shadow_checked"
        and (x.get("rank"),x.get("pid"),x.get("step"),x.get("layer"),x.get("request_id"))==
            (0,e["pid"],e["step"],LAYER,e.get("request_id")) and x.get("passed")is False]
    if len(failures)!=1:raise ValueError("exact preceding actual failed shadow required")
    failure=failures[0]
    selections=[x for x in events[:events.index(failure)]
        if x.get('event')=='c1_first_divergence_selection' and
        (x.get('rank'),x.get('pid'),x.get('step'),x.get('layer'))==(0,e['pid'],e['step'],LAYER)]
    if len(selections)!=1:raise ValueError("exact preceding selection decision required")
    selection=selections[0];excluded=selection.get('excluded_native_one')
    if (selection.get('eligible')is not True or selection.get('reason')is not None
            or selection.get('manifest_sha256')!=manifest_sha256
            or selection.get('actual_slot_commit')!='not_started'
            or selection.get('hot_request_ids')!=failure.get('group_requests')
            or selection.get('selected_request_id')!=e.get('request_id')
            or selection.get('active_windows')!=4 or type(selection.get('active_windows'))is not int
            or not isinstance(excluded,list) or len(set(excluded))!=len(excluded)
            or set(excluded)&set(failure.get('group_requests',[]))
            or type(selection.get('total_entries'))is not int
            or selection['total_entries']!=2+len(excluded)
            or type(selection.get('packed_tokens'))is not int
            or not 4<=selection['packed_tokens']<=12000):
        raise ValueError("frozen mixed-native1/hot selection receipt mismatch")
    if excluded:
        native=[x for x in events[:events.index(selection)]
            if x.get('event')=='native_decode_batch_completed' and
            (x.get('rank'),x.get('pid'),x.get('step'),x.get('layer'))==(0,e['pid'],e['step'],LAYER)]
        if (len(native)!=1 or set(native[0].get('requests',[]))!=set(excluded)
                or native[0].get('rows')!=len(excluded)
                or native[0].get('manifest_sha256')!=manifest_sha256
                or native[0].get('private_buffers')is not True
                or native[0].get('actual_slot_commit')!='deferred'):
            raise ValueError("independent native1 exclusion proof required")
    if (failure.get("manifest_sha256")!=manifest_sha256
            or failure.get("actual_slot_commit")!="not_started"
            or failure.get("private_buffers")is not True
            or (failure.get("atol"),failure.get("rtol"))!=(.01,.003)
            or not 1<=len(failure.get("group_requests",[]))<=2):
        raise ValueError("frozen private failed shadow group required")
    forbidden={"compact_gdn_body_composed","mixed_native_gdn_completed","c1_layer_precommit_validated"}
    if any(x.get("event") in forbidden and
        (x.get("rank"),x.get("pid"),x.get("step"),x.get("layer"))==(0,e["pid"],e["step"],LAYER)
        for x in events):
        raise ValueError("actual gate/commit in failed layer-step")
    container=Path(e.get("root",""))
    try:relative=container.relative_to("/scratch")
    except ValueError:raise ValueError("exact scratch capture root required")
    if relative.parts!=("diagnostics","c1-stage-rank0-step"+str(e["step"])):
        raise ValueError("exact owned capture path required")
    raw=Path(host_raw).resolve();root=raw/relative
    if root.resolve().parent!=(raw/"diagnostics").resolve():
        raise ValueError("capture escaped raw root")
    mp=root/"manifest.json"
    if mp.is_symlink() or not mp.is_file() or mp.stat().st_size>1024*1024:
        raise ValueError("bounded regular capture manifest required")
    m=json.loads(mp.read_text());identity=m.get("identity",{})
    rid=e.get("request_id")
    if (identity.get("rank"),identity.get("pid"),identity.get("step"),identity.get("layer"),
            identity.get("manifest_sha256"),identity.get("requests"))!=(
            0,e["pid"],e["step"],LAYER,manifest_sha256,[rid]):
        raise ValueError("exact sampled request/source/worker/step identity required")
    policy=identity.get("head_policy","head0")
    heads=identity.get("head_indices",{})
    if policy=="head0":
        if heads!={"key":0,"query":0,"value":0}:raise ValueError("legacy head0 required")
    elif policy=="max_state_residual":
        vh=heads.get("value")
        if (type(vh)is not int or not 0<=vh<12
                or heads!={"query":vh//3,"key":vh//3,"value":vh}
                or e.get("head_policy")!=policy
                or any(x.get("c1_first_divergence_head_policy")!=policy for x in installs)):
            raise ValueError("explicit residual policy and canonical4/12 grouped-head mapping required")
    else:raise ValueError("unknown sampled head policy")
    if (identity.get("key_width")!=128 or identity.get("value_width")!=128
            or identity.get("generations")!={rid:public.get("generation")}
            or rid not in failure["group_requests"]):
        raise ValueError("selected head width/current producer generation/group mismatch")
    coordinates=e.get("coordinates",{});c=coordinates.get(rid,{})
    if (set(coordinates)!=set(failure["group_requests"])
            or type(c.get("slot"))is not int or c["slot"]<0
            or type(c.get("has_initial"))is not bool or c["has_initial"]is not True
            or type(c.get("body_start"))is not int or type(c.get("body_end"))is not int
            or not 0<=c["body_start"]<c["body_end"]<=32768
            or c["body_end"]-c["body_start"]!=16376):
        raise ValueError("actual slot/continuation/body coordinates required")
    if (type(public.get("generation"))is not int or public["generation"]<1
            or identity.get("tokens_sha256")!={rid:public.get("tokens_sha256")}
            or not re.fullmatch("[0-9a-f]{64}",public.get("tokens_sha256",""))
            or any(type(v)is not int for v in heads.values())):
        raise ValueError("exact token/generation/head association required")
    metrics={x.get("tensor"):x for x in failure.get("metrics",[])}
    if (set(metrics)!={"output","state","conv"} or metrics["state"].get("passed")is not False
            or metrics["output"].get("passed")is not True or metrics["conv"].get("passed")is not True
            or not math.isfinite(metrics["state"].get("max_scaled",float("nan")))
            or metrics["state"]["max_scaled"]<=1):
        raise ValueError("actual frozen state-only failed shadow required")
    generic=audit_capture(root,expected_identity=identity,
                          manifest_sha256=e.get("capture_manifest_sha256",""))
    records={(x["side"],x["stage"],x["window"]):x for x in m["records"]}
    stages=(("inputs","prefix"),("inputs","suffix"),("prefix_terminal","prefix"),
            ("cached_composition","body"),("suffix_seed","suffix"),("final","suffix"))
    if set(records)!={(side,stage,window) for side in ("packed","serial") for stage,window in stages}:
        raise ValueError("complete exact paired prefix/body/suffix stage set required")
    lengths={}
    for side in ("packed","serial"):
        for window in ("prefix","suffix"):
            record=records[(side,"inputs",window)]
            n=record["source_end"]-record["source_start"];lengths[(side,window)]=n
            expected={"q":[n,128],"k":[n,128],"v":[n,128],"g":[n],"beta":[n],"initial":[128,128]}
            if any(record["tensors"][k]["shape"]!=shape for k,shape in expected.items()):
                raise ValueError("actual128-dimensional sampled head input geometry required")
        if sum(lengths[(side,w)] for w in ("prefix","suffix"))>12000:
            raise ValueError("selected live row bound")
        for stage,window in stages[2:]:
            record=records[(side,stage,window)]
            if window=="body":
                if (record["source_start"],record["source_end"])!=(c["body_start"],c["body_end"]):
                    raise ValueError("cached body coordinate mismatch")
            else:
                ref=records[(side,"inputs",window)]
                if (record["source_start"],record["source_end"])!=(ref["source_start"],ref["source_end"]):
                    raise ValueError("state/input stage coordinate mismatch")
            for name,meta in record["tensors"].items():
                shape=([lengths[(side,"suffix")],128] if name=="output"
                       else [3,2560] if name=="conv" else [128,128])
                if meta["shape"]!=shape:raise ValueError("sampled state/output/conv geometry")
    branches=e.get("branches",[])
    if len(branches)!=4:raise ValueError("four actual branch receipts required")
    prefix_policy=installs[0].get("c1_short_prefix_terminal_policy","chunk64")
    if any(x.get("c1_short_prefix_terminal_policy","chunk64")!=prefix_policy for x in installs):
        raise ValueError("worker prefix-terminal policy mismatch")
    prefix_route_audit=None
    if prefix_policy=="canonical_recurrent_le64":
        from audit_c1_short_prefix import audit_prefix_routes
        prefix_route_audit=audit_prefix_routes(events,manifest_sha256=manifest_sha256)
        candidates=[x for x in events[:index] if x.get("event")=="c1_prefix_terminal_route"
            and (x.get("rank"),x.get("pid"),x.get("step"),x.get("layer"),x.get("request_id"))==
                (0,e["pid"],e["step"],LAYER,rid)]
        record=records[("packed","inputs","prefix")]
        if (len(candidates)!=1 or
                (candidates[0]["source_start"],candidates[0]["source_end"])!=
                    (record["source_start"],record["source_end"])):
            raise ValueError("sampled prefix inputs lack exact producing terminal route")
    elif prefix_policy!="chunk64":raise ValueError("unknown actual prefix terminal policy")
    seen=set()
    for branch in branches:
        key=(branch.get("side"),branch.get("window"))
        if key in seen or key not in lengths or branch.get("request_id")!=rid:
            raise ValueError("actual branch coordinate duplication/mismatch")
        seen.add(key)
        expected=("official_chunk64" if key[0]=="packed" or lengths[key]>64
                  else "independent_recurrent_le64")
        if prefix_policy=="canonical_recurrent_le64" and key==("packed","prefix") and lengths[key]<=64:
            expected="independent_recurrent_le64"
        if branch.get("branch")!=expected:raise ValueError("actual kernel branch mismatch")

    if e.get("records")!=len(m["records"]) or e.get("payload_bytes")!=m["payload_bytes"]:
        raise ValueError("sealed capture receipt accounting mismatch")
    import numpy as np
    from audit_c1_stage_capture import sampled_head_fp64_recurrence
    def tensor(side,stage,window,name):
        meta=records[(side,stage,window)]["tensors"][name]
        return np.load(root/meta["file"],allow_pickle=False).astype(np.float64)
    def residual(actual,reference):
        d=np.abs(actual-reference);scaled=d/(.01+.003*np.abs(reference))
        return dict(max_abs=float(d.max()),max_scaled=float(scaled.max()),
                    rms=float(np.sqrt(np.mean(d*d))),within_frozen_tolerance=bool(np.all(scaled<=1)))
    selected_point=None
    if policy=="max_state_residual":
        selected=identity.get("head_selection",{})
        if selected!=e.get("head_selection"):
            raise ValueError("sealed/runtime head selection mismatch")
        ki=selected.get("key_coordinate");vi=selected.get("value_coordinate")
        maximum=metrics["state"]["max_scaled"]
        if (type(ki)is not int or type(vi)is not int or not 0<=ki<128 or not 0<=vi<128
                or selected.get("value_head")!=heads["value"]
                or (selected.get("atol"),selected.get("rtol"))!=(.01,.003)
                or selected.get("reported_max_scaled")!=maximum
                or selected.get("selected_max_scaled")!=maximum):
            raise ValueError("exact failed-head coordinate and reported maximum required")
        actual=tensor("packed","final","suffix","state")
        reference=tensor("serial","final","suffix","state")
        point=float(abs(actual[ki,vi]-reference[ki,vi])/(.01+.003*abs(reference[ki,vi])))
        if point<=1 or not math.isclose(point,maximum,rel_tol=2e-6,abs_tol=2e-6):
            raise ValueError("independent sampled coordinate does not match reported failed maximum")
        selected_point=dict(value_head=heads["value"],key_coordinate=ki,value_coordinate=vi,
            independently_recomputed_scaled_residual=point,reported_max_scaled=maximum,
            scope="sampled point agrees with runtime maximum; not independent global argmax")
    internal=[];oracles=[]
    for side in ("packed","serial"):
        prefix=tensor(side,"prefix_terminal","prefix","state")
        transition=tensor(side,"cached_composition","body","transition")
        zero=tensor(side,"cached_composition","body","zero_state")
        composed=tensor(side,"cached_composition","body","state")
        seed=tensor(side,"suffix_seed","suffix","state")
        incoming=tensor(side,"inputs","suffix","initial")
        for stage,actual,reference in (
                ("cached_T_H_plus_S",composed,transition@prefix+zero),
                ("suffix_seed_copy",seed,composed),("actual_suffix_input",incoming,seed)):
            internal.append(dict(side=side,stage=stage,**residual(actual,reference)))
        for window in ("prefix","suffix"):
            values=[tensor(side,"inputs",window,name) for name in ("q","k","v","g","beta","initial")]
            _,reference=sampled_head_fp64_recurrence(*values)
            actual=tensor(side,"prefix_terminal","prefix","state") if window=="prefix" else tensor(side,"final","suffix","state")
            oracles.append(dict(side=side,window=window,**residual(actual,reference),
                scope="independent captured-input FP64 math reference; not BF16 bitwise requirement"))
    return dict(capture_link_verified=True,identity=identity,coordinates=coordinates,
                internal_state_checks=internal,fp64_captured_input_references=oracles,
                selected_failed_point=selected_point,prefix_route_audit=prefix_route_audit,
                tensor_audit=generic,scope="source-bound sampled selected-head failed-request diagnostic only; full run, physical isolation/release, quality and performance separate")

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--raw-root',required=True)
    parser.add_argument('--manifest-sha256',required=True);args=parser.parse_args()
    raw=Path(args.raw_root);events=[]
    for path in sorted((raw/'diagnostics').glob('compact-worker-*.jsonl')):
        if path.is_symlink() or not path.is_file():raise ValueError('regular worker journal required')
        events.extend(json.loads(line) for line in path.read_text().splitlines())
    print(json.dumps(audit_runtime_capture(events,raw,manifest_sha256=args.manifest_sha256)))
