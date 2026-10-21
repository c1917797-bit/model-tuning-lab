"""Independent CPU-only two-request actual native AR/BOLE token identity smoke.

Does not infer global FA precision alignment, task accuracy or performance.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0,str(_Path(__file__).resolve().parent))
import pair_contract as C

def identity_join(sr, bundle, http_schema, oracle):
    """Consume original actual identity semantics twice, then enforce lifecycle order."""
    http = C.obj(bundle["http"])
    C.need(http["schema"] == http_schema and http["source"] == sr
           and [r["label"] for r in http["rows"]]
           == ["tree-1", "tree-2", "retirement-barrier"],
           "exact ordered actual two-request HTTP ledger")
    refs = bundle["journal"]
    C.need(len(refs) == len({r["path"] for r in refs}), "unique actual journal refs")
    events = [C.obj(r) for r in refs]
    C.need(all(e["schema"] == "bole.actual-identity-journal/v1"
               and e["source"] == sr and e["role"] in
               ("frontend", "rank0", "rank1", "rank2", "rank3")
               and e["kind"] == ("assignment" if e["role"] == "frontend"
                                  else "worker_update") for e in events),
           "all actual journals have exact source, process role and event kind")
    root = Path(C.obj(sr)["model_receipt_root"])
    by_role = {}
    for ref, event in zip(refs, events):
        role = event["role"]
        by_role.setdefault(role, []).append((ref, event))
    C.need(set(by_role) == {"frontend", "rank0", "rank1", "rank2", "rank3"},
           "all five actual process journals")
    for role, rows in by_role.items():
        rows.sort(key=lambda pair: pair[0]["path"])
        C.need(len(rows) <= 512 and sum(r["bytes"] for r, _ in rows) <= 8 * 2**20
               and [r["path"] for r, _ in rows] == [str(root / (
                   "IDENTITY-%s-%06d.json" % (role, i + 1))) for i in range(len(rows))],
               "complete contiguous bounded exclusive process journal")
    frontend = bundle["frontend_binding"]
    C.need(frontend["NSpid"][-1] == frontend["guest"]["pid"]
           and frontend["owned_cid"] in frontend["host"]["cgroup"]
           and frontend["host"]["start_ticks"] == frontend["guest"]["start_ticks"],
           "independently owned frontend namespace/process binding")
    assigned = []
    for row in http["rows"][:2]:
        response = C.obj(row["response"])
        matches = [e["event"] for _, e in by_role["frontend"]
                   if e["event"]["before_request_id"] == response["id"] + "-0"]
        C.need(len(matches) == 1 and matches[0]["identity"] == frontend["guest"],
               "each real assignment belongs to the same independently bound frontend")
        _, actual = oracle.validate_assignment(response["id"], C.PROFILE, matches[0])
        C.need(response["id"] == oracle.expected_server_id(row["header"], None),
               "real response/header/assignment chain")
        assigned.append(actual)
    C.need(len(set(assigned)) == 2, "distinct actual assigned engine request IDs")
    snapshots = bundle["snapshots"]
    C.need(len(snapshots) == 4 and len({r["pid"] for r in snapshots}) == 4
           and len(bundle["host_bindings"]) == 4, "exact four actual owned snapshots/bindings")
    snapshots = {r["pid"]: r for r in snapshots}
    bindings, traces, ordered = {}, [], []
    for rank in range(4):
        rows = [e["event"] for _, e in by_role["rank%d" % rank]]
        identity = rows[0]["identity"]
        snapshot = snapshots.get(identity["pid"])
        C.need(snapshot is not None and snapshot["source_ref"] == sr
               and snapshot["allow_hf32"] is False, "same native source/HF32OFF actual worker")
        rest = snapshot["proc_stat"][snapshot["proc_stat"].rfind(")") + 2:].split()
        C.need(identity == dict(pid=snapshot["pid"], start_ticks=int(rest[19]),
                               cgroup=snapshot["cgroup"]),
               "actual worker PID/start/cgroup snapshot chain")
        actual = [b for b in bundle["host_bindings"] if b["guest"] == snapshot]
        C.need(len(actual) == 1 and actual[0]["host"]["physical"] in (4, 5, 6, 7),
               "actual owned host/NSpid authority")
        bindings[rank] = identity
        traces.append(dict(schema="vllm023.actual-worker-retirement/v1",
                           rank=rank, identity=identity, events=rows))
        ordered.append(rows)
    C.need(len({b["pid"] for b in bindings.values()}) == 4 and
           {b["host"]["physical"] for b in bundle["host_bindings"]} == {4, 5, 6, 7},
           "distinct all4 actual workers on the declared physical cards")
    for rid in assigned:
        oracle.validate_worker_retirement(rid, traces, bindings)
    for rows in ordered:
        first_end = [e["seq"] for e in rows if assigned[0] in e["finished_req_ids"]]
        second_start = [e["seq"] for e in rows if assigned[1] in e["new_req_ids"]]
        first_start = [e["seq"] for e in rows if assigned[0] in e["new_req_ids"]]
        C.need(len(first_end) == len(second_start) == len(first_start) == 1
               and first_start[0] < first_end[0] <= second_start[0],
               "first actual request retired before second native ingress; same update may remove then add")
        for e in rows:
            C.need(len(set(assigned).intersection(e["requests_after"])) <= 1
                   and len(set(assigned).intersection(e["batch_after"])) <= 1,
                   "no two live G1 request owners in a C1 worker")
    return assigned, bindings

def same_bits(t, a, b, reason):
    C.need(a.shape==b.shape and a.dtype==b.dtype and
           t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8)), reason)


def tensor_bytes(t,x):
    if isinstance(x,t.Tensor):
        C.need(x.device.type=='cpu' and x.is_contiguous(),'CPU primitive capture tensors')
        return x.numel()*x.element_size()
    if x is None or type(x)in(str,int,float,bool):return 0
    if type(x)in(list,tuple):return sum(tensor_bytes(t,v)for v in x)
    C.need(type(x)is dict and all(type(k)in(str,int)for k in x),'only original primitive capture values')
    return sum(tensor_bytes(t,v)for v in x.values())


def assemble(t, locals_, policy):
    C.need(len(locals_)==4 and policy['lmhead_tp']is False and type(policy['reduce_sample'])is bool
           and type(policy['vocab_size'])is int and policy['vocab_size']>1,'actual supported TP4 vocabulary policy')
    first=locals_[0]
    C.need(all(x.ndim==2 and x.shape==first.shape and x.shape[0]==1 and x.shape[1]>1
               and x.dtype==first.dtype and x.dtype in(t.bfloat16,t.float32)
               and bool(t.isfinite(x).all())for x in locals_), 'original finite actual TP vocabulary operands')
    if policy['reduce_sample']:
        value=t.cat([x.float()for x in locals_],dim=-1)[:,:policy['vocab_size']]
    else:
        value=first.float()
        for x in locals_:same_bits(t,x,first,'actual full-vocabulary replicas agree')
    C.need(value.shape==(1,policy['vocab_size']), 'complete untrimmed actual target vocabulary')
    for x in locals_:
        if x.dtype==t.bfloat16:same_bits(t,x.float().to(t.bfloat16),x,'exact native vocabulary promotion roundtrip')
    return value


def actual_native_fa(t, frame):
    C.need(frame['schema']=='bole.actual-production-native-FA-frame/v1'
           and frame['ordinal']==1 and frame['prefix_length']==131
           and frame['precision_intervention']is False
           and frame['private_dense_FP16_control_used']is False
           and frame['production_globally_qualified']is False
           and len(frame['kernel'])==1, 'actual observed native decode FA, separate from private FP16 proof')
    q,k,v,output=(frame[x]for x in('query','key','value','output'))
    C.need(q.shape==output.shape==(1,6,256) and k.shape==v.shape==(132,1,256)
           and q.dtype==k.dtype==v.dtype==output.dtype==t.bfloat16
           and all(bool(t.isfinite(x).all())for x in(q,k,v,output)),
           'original actual native BF16 q1/KV132 boundary')
    for name,current in(('key','current_key'),('value','current_value')):
        same_bits(t,frame[name][-1:],frame[current],'current native write belongs to actual post-RoPE operands')
    physical=frame['request_physical_blocks'];table=frame['kernel_table']
    C.need(physical and all(type(p)is int and p>=0 for p in physical)
           and table==[p*12+j for p in physical for j in range(12)]
           and len(set(table))==len(table)
           and frame['slot_mapping']==[table[131//128]*128+131%128],
           'actual native physical1536→kernel128 ownership and current write')
    kernel=frame['kernel'][0];kw=kernel['explicit_kwargs'];name=kernel['name']
    C.need(kernel['original_called_exactly_once']is True and kernel['precision_intervention']is False
           and kernel['omitted_defaults_resolved']is False
           and name in('_npu_paged_attention','npu_fused_infer_attention_score'),
           'actual lower PA or FIA route with original explicit arguments; no invented defaults')
    expected_names=('key_cache','value_cache')if name=='_npu_paged_attention'else('key','value')
    expected_cache=[]
    for ident in frame['cache_identities']:
        C.need(ident['shape'][1:]==[128,1,256] and ident['dtype']=='torch.bfloat16',
               'actual native paged ND cache geometry')
        expected_cache.append(dict(ident,shape=ident['shape'][:2]+[256],stride=ident['stride'][:2]+[1]))
    C.need(frame['FIA_cache_view_identities']==expected_cache,
           'independent exact native _get_fia_params page flattening view')
    selected=frame['cache_identities']if name=='_npu_paged_attention'else expected_cache
    for key,ident in zip(expected_names,selected):
        actual=kw[key]['tensor_identity']
        if name=='_npu_paged_attention':
            C.need(actual==ident, 'actual lower native PA arena identity')
        else:
            C.need(actual['shape']==ident['shape']and actual['dtype']==ident['dtype']
                   and actual['device']==ident['device']
                   and actual['stride']==[128*256,256,1],
                   'actual native FIA contiguous page view/copy ABI; no assumed pointer alias')
    same_bits(t,kernel['actual_owned_key'],k,'actual lower owned key prefix equals original native cache')
    same_bits(t,kernel['actual_owned_value'],v,'actual lower owned value prefix equals original native cache')
    if name=='_npu_paged_attention':
        C.need(kw['num_heads']==6 and kw['num_kv_heads']==1 and kw['scale_value']==256**-.5,
               'actual PA6/KV1/D256 scaling')
        C.need(kw['context_lens'].tolist()==[132], 'actual original PA context length')
    else:
        C.need(kw['input_layout']=='TND' and kw['num_heads']==6 and kw['num_key_value_heads']==1
               and kw['scale']==256**-.5 and kw['block_size']==128 and kw['sparse_mode']==3
               and kw['actual_seq_lengths']==[1] and kw['actual_seq_lengths_kv']==[132],
               'actual original native TND paged causal FIA arguments')
        mask=kw['atten_mask']
        C.need(mask.dtype==t.int8 and mask.ndim==2 and tuple(mask.shape)==(2048,2048)
               and mask.is_contiguous()and mask.stride()==(2048,1)and mask.storage_offset()==0
               and t.equal(mask,t.triu(t.ones((2048,2048),dtype=t.int8,device='cpu'),diagonal=1)),
               'exact actual full int8 upper2048 template; q1 right-down sees all132 keys')
    table_tensor=kw['block_table']
    C.need(table_tensor.ndim==2 and table_tensor.shape[0]==1
           and table_tensor[0,:len(table)].tolist()==table, 'actual lower native block table values')
    same_bits(t,kernel['output'].reshape(1,6,256),output,'actual lower result equals native published FA result')
    metrics={}
    for label,dtype in(('FP32',t.float32),('FP64',t.float64)):
        values=[]
        for h in range(6):
            scores=k[:,0].to(dtype).mv(q[0,h].to(dtype))*(256**-.5)
            probability=(scores-scores.max()).exp();probability/=probability.sum()
            values.append(v[:,0].to(dtype).T.mv(probability))
        truth=t.stack(values).unsqueeze(0)
        error=(output.double()-truth.double()).abs()
        metrics[label]=dict(pointwise_pass=bool((error<=.001+.01*truth.double().abs()).all()),
                            peak_abs=float(error.max()))
    return dict(layer=frame['layer'],route=name,checks=metrics,
        actual_original_native_BF16_observed=True,
        actual_schema_family=kernel['actual_schema_family'],omitted_defaults_resolved=False,
        native_paged_FA_scope='actual C1/131/q1 frames only',
        private_FP16_qualification_imported=False,global_FA_alignment_qualified=False)


def compare_tokens(ar,on):
    C.need(len(ar)==len(on)==2,'two actual completed request comparisons')
    rows=[]
    for generation,(a,b)in enumerate(zip(ar,on),1):
        C.need(type(a)is list and type(b)is list and len(a)==len(b)==2
               and all(type(x)is int and x>=0 for x in a+b), 'exact actual returned output IDs')
        mismatch=next((i for i,(x,y)in enumerate(zip(a,b))if x!=y),None)
        rows.append(dict(generation=generation,native_AR_token_ids=a,BOLE_token_ids=b,
                         token_identity_pass=mismatch is None,first_mismatch_ordinal=mismatch,
                         matching_prefix_tokens=2 if mismatch is None else mismatch))
    return rows


def http_tokens(source_ref,bundle,schema,header_prefix,frozen):
    value=C.obj(bundle['http'])
    C.need(value['source']==source_ref and value['schema']==schema
           and _http_provenance(C,source_ref,bundle,value,schema,header_prefix,frozen,_SAVED_METADATA)
           and [r['label']for r in value['rows']]==['tree-1','tree-2','retirement-barrier'],
           'exact source and frozen same-input collection ledger')
    result=[]
    for row,count in zip(value['rows'],(2,2,1)):
        p=row['request'];r=C.obj(row['response'])
        C.need(row['header']==header_prefix+row['label'] and row['http_status']==200
               and p['prompt']==frozen['token_ids'] and p['max_tokens']==count
               and p['temperature']==0 and p['top_p']==1 and p['n']==1
               and p['stream']is False and p['ignore_eos']is True and p['return_token_ids']is True
               and r['id']=='cmpl-'+row['header'] and 'error'not in r
               and r['usage']['prompt_tokens']==131 and r['usage']['completion_tokens']==count
               and len(r['choices'])==1,'actual deterministic completed HTTP smoke')
        choice=r['choices'][0]
        C.need(choice['finish_reason']=='length' and type(choice['token_ids'])is list
               and len(choice['token_ids'])==count and all(type(x)is int and x>=0 for x in choice['token_ids']),
               'actual returned IDs; deliberate budget termination, no EOS claim')
        if count==2:result.append(choice['token_ids'])
    return result


def image_and_common(pair,ar,on,m):
    inspections=[C.obj(x['docker_inspect_ref'])for x in(ar,on)]
    C.need(all(type(x)is list and len(x)==1 for x in inspections),'actual single-container inspect arrays')
    images=[x[0]['Image']for x in inspections]
    C.need(images[0]==images[1]==m['expected_image_id'] and images[0].startswith('sha256:'),
           'same exact actually observed image ID, not mutable tags')
    argv=[C.obj(x['server_command_ref'])['argv']for x in(ar,on)]
    C.need(argv[0]==C.native_argv(argv[1])==m['native_server_argv'],
           'same common actual argv, only explicitly declared MTP/BOLE algorithm difference')
    on_source=C.obj(m['BOLE_source_ref'])
    for key,reference in m['runtime_sources'].items():
        C.need(on_source['runtime_sources'][key]==reference,'same installed runtime source '+key)
    C.need(ar['model_manifest_ref']==on['model_manifest_ref']==m['model_manifest_ref'],
           'same source-bound actual model/tokenizer manifest')
    manifest=C.obj(m['model_manifest_ref'])
    C.need(manifest['schema']=='bole.actual-model-tokenizer-file-manifest/v1'
           and manifest['files'] and manifest['model_root']=='/models/Qwen3.6-27B',
           'actual fixed loaded model/tokenizer files')
    for reference in manifest['files']:C.checked(reference)
    profiles=[C.obj(x['launch_profile_ref'])for x in(ar,on)]
    for variant,bundle,profile in zip(('native_AR','BOLE'),(ar,on),profiles):
        identities=[bundle['frontend_binding']['guest']]
        host=bundle['frontend_binding']['host']
        if all(k in host for k in('pid','start_ticks','cgroup')):
            identities.append({k:host[k]for k in('pid','start_ticks','cgroup')})
        C.need(profile['schema']=='bole.actual-pair-launch-profile/v1'
               and profile['source']==pair['source']and profile['variant']==variant
               and profile['identity']in identities
               and profile['collector']==m['files']['launch_profile.py']
               and profile['credential_values_retained']is False
               and profile['plugin_effect_classification_performed']is False,
               'actual owned frontend launch environment, with no plugin-classification claim')
    C.need(profiles[0]['common_environment']==profiles[1]['common_environment'],
           'same actual recorded framework common optimization environment')
    C.need(set(profiles[0]['plugins'])=={'ascend','bole_native_ar_pair'}
           and set(profiles[1]['plugins'])=={'ascend','dense_opportunity090',
               'bole_mtp_load_receipt111','bole_three_node131'},'explicit separate observer/algorithm plugin profiles')
    return dict(actual_image_id=images[0],installed_runtime_sources_equal=True,
                common_argv_equal_after_declared_delta=True,
                actual_common_framework_environment_equal=True,
                actual_plugin_profiles=[p['plugins']for p in profiles],
                common_plugin_effects_independently_reviewed=False,
                declared_algorithm_delta=dict(native_AR=dict(BOLE=False,speculative_config=None),
                    BOLE=dict(BOLE=True,speculative_config=dict(method='mtp',num_speculative_tokens=8))),
                same_kernel_route_assumed=False)


def run(t,sr,bundle_ref,output):
    m=C.source(sr)
    C.need(C.ref(__file__)==_SAVED_METADATA['files']['derived_math_consumer.py'] and output.is_absolute() and output.is_dir()
           and str(output)==_SAVED_METADATA['consumer_output_root']
           and not any(p.is_symlink()for p in(output,*output.parents)), 'exact owned pair consumer leaf')
    pair=C.obj(bundle_ref)
    C.need(pair['schema']=='bole.actual-native-ar-bole-pair-inputs/v1' and pair['source']==sr
           and pair['scope']==C.SCOPE, 'bounded source-bound actual pair input ledger')
    ar,on=(C.obj(pair[k])for k in('native_AR','BOLE'))
    C.need(ar['schema']=='bole.actual-four-rank-native-ar-inputs/v1'
           and ar['source']==sr and on['source']==m['BOLE_source_ref'], 'actual variant source references')
    common=image_and_common(pair,ar,on,m)
    oracle=C.load(m['files']['identity_oracle.py'],'_native_ar_pair_original_identity_oracle')
    assigned,bindings=identity_join(sr,ar,C.AR_HTTP,oracle)
    on_assigned,on_bindings=identity_join(m['BOLE_source_ref'],on,
        'bole.actual-c1-two-request-service-HTTP/v1',oracle)
    frozen=dict(C.obj(pair['inputs_ref']),reference=pair['inputs_ref'])
    C.need(len(frozen['token_ids'])==131 and frozen['source']==m['BOLE_source_ref']
           and frozen['input_tokens']==131 and frozen['tokenizer']=='/models/Qwen3.6-27B'
           and frozen['data_generated_by_actual_tokenizer']is True,
           'same source-bound original actual131-token tokenizer input')
    ar_tokens=http_tokens(sr,ar,C.AR_HTTP,'bole-native-ar-131-',frozen)
    on_tokens=http_tokens(m['BOLE_source_ref'],on,'bole.actual-c1-two-request-service-HTTP/v1','bole-g1-131-',frozen)
    # Re-run the source-bound full qualified G1 CPU gate in a separate process so
    # its short helper module names cannot collide with this independent packet.
    on_source=C.obj(m['BOLE_source_ref']);consumer_ref=on_source['files']['consume_service.py']
    C.checked(consumer_ref)
    gate=output/'BOLE-INDEPENDENT-GATE';gate.mkdir()
    env=dict(os.environ,ASCEND_RT_VISIBLE_DEVICES='',TORCH_DEVICE_BACKEND_AUTOLOAD='0')
    completed=subprocess.run([sys.executable,'-I','-B',consumer_ref['path'],'--execute',
        '--source-ref',json.dumps(m['BOLE_source_ref']),'--inputs-ref',json.dumps(pair['BOLE']),
        '--output',str(gate)],env=env,capture_output=True,text=True,timeout=900)
    C.need(completed.returncode==0,'original BOLE independent gate failed: '+completed.stderr[-4000:])
    on_gate_ref=C.ref(gate/'ATTRIBUTION.json');on_gate=C.obj(on_gate_ref)
    C.need(on_gate['source']==m['BOLE_source_ref'] and on_gate['service_complete']is True
           and on_gate['completed_request_count']==2 and on_gate['component_checks_pass']is True
           and on_gate['scheduler_committed_independently']is True and on_gate['model_ready']is False,
           'original complete actual BOLE source, maths, calibration, lifecycle and HTTP joins')
    C.need(len(ar['ranks'])==len(on['ranks'])==4,'actual four rank evidence pairs')
    raws=[];budget=[]
    for rank,(capture,on_capture)in enumerate(zip(ar['ranks'],on['ranks'])):
        receipt=C.obj(capture['receipt']);root=Path(m['model_receipt_root'])
        C.need(capture['raw']['path']==str(root/('NATIVE-AR-RANK-%d.pt'%rank))
               and capture['receipt']['path']==str(root/('NATIVE-AR-RANK-%d.json'%rank))
               and receipt['schema']=='bole.actual-native-ar-worker-receipt/v1'
               and receipt['source']==sr and receipt['rank']==rank and receipt['primary']is None
               and receipt['raw']==capture['raw'],'actual native AR worker capture')
        rest=receipt['stat'][receipt['stat'].rfind(')')+2:].split()
        C.need(dict(pid=receipt['pid'],start_ticks=int(rest[19]),cgroup=receipt['cgroup'])==bindings[rank],
               'native AR capture and actual owned process identity')
        exported=t.load(C.checked(capture['raw']),map_location='cpu',weights_only=False);raw=exported['payload']
        logical=tensor_bytes(t,raw)
        C.need(exported['schema']=='bole.model-diagnostic-primitives/v1' and exported['cap_bytes']==C.CAP
               and logical==exported['logical_tensor_bytes']==receipt['logical_tensor_bytes']
               and logical+64*2**20<=C.CAP and raw['schema']==C.AR_RAW and raw['source']==sr
               and raw['rank']==rank and raw['primary']is None and raw['native_AR']is True
               and raw['speculative_config']is None and raw['precision_intervention']is False
               and raw['private_dense_FP16_control_used']is False and raw['model_ready']is False
               and raw['source_after']==m['files'] and raw['runtime_sources_after']==m['runtime_sources']
               and len(raw['requests'])==2,'actual unchanged-source native AR primitives and budget')
        on_receipt=C.obj(on_capture['receipt'])
        all_refs=[capture['raw'],capture['receipt'],on_capture['raw'],on_capture['receipt'],
                  *on_receipt['rank_evidence_refs']]
        C.need(len(ar['snapshot_refs'])==4,'four actual native AR load snapshots')
        snapshot_ref=ar['snapshot_refs'][rank];snapshot=C.obj(snapshot_ref)
        C.need(snapshot_ref['path']==str(root/('NATIVE-AR-SNAPSHOT-RANK-%d.json'%rank))
               and snapshot in ar['snapshots']and snapshot['rank']==rank
               and snapshot['actual_allow_hf32']is False
               and snapshot['registry']['counts']==dict(gdn=48,fa=16),
               'actual original native AR full model load and HF32OFF snapshot')
        all_refs.extend([snapshot_ref,pair['native_AR'],pair['BOLE'],bundle_ref,pair['inputs_ref']])
        for bundle in(ar,on):
            all_refs.extend(r for r in bundle['journal']if Path(r['path']).name.startswith('IDENTITY-rank%d-'%rank))
            all_refs.extend(bundle[key]for key in('http','docker_inspect_ref','server_command_ref','launch_profile_ref'))
            all_refs.extend(row['response']for row in C.obj(bundle['http'])['rows'])
        unique={}
        for reference in all_refs:
            C.checked(reference)
            if reference['path']in unique:C.need(unique[reference['path']]==reference,'consistent exact shared evidence ref')
            unique[reference['path']]=reference
        charged=sum(r['bytes']for r in unique.values())
        C.need(charged<=C.CAP+2**20,'combined actual AR+BOLE rank raw/calibration/journal evidence within original1GiB plus headers')
        budget.append(dict(rank=rank,combined_retained_bytes=charged,cap_bytes=C.CAP,header_allowance=2**20))
        raws.append(raw)
    policies=[r['native_policy']for r in raws]
    C.need(all(p==policies[0]for p in policies) and policies[0]['proposer_source']==m['runtime_sources']['proposer'],
           'same actual source-bound native vocabulary policy all4')
    rank_reports=[[]for _ in range(4)]
    for generation in(1,2):
        requests=[r['requests'][generation-1]for r in raws]
        for rank,item in enumerate(requests):
            C.need(item['request']==assigned[generation-1] and item['generation']==generation
                   and type(item['request_object_id'])is int and item['request_object_id']>0
                   and item['prompt_token_ids']==frozen['token_ids'] and len(item['samples'])==2,
                   'actual assigned native request, fresh generation and same input')
            if generation==2:C.need(item['request_object_id']!=raws[rank]['requests'][0]['request_object_id'],
                                   'distinct strongly retained actual native request objects')
        for ordinal in(0,1):
            samples=[r['samples'][ordinal]for r in requests]
            logits=assemble(t,[s['local_logits']for s in samples],policies[0])
            greedy=int(logits[0].argmax())
            for rank,(item,sample)in enumerate(zip(requests,samples)):
                before=[]if ordinal==0 else ar_tokens[generation-1][:1]
                C.need(sample['ordinal']==ordinal and sample['request']==item['request']
                       and sample['request_object_id']==item['request_object_id']
                       and sample['computed_tokens']==(0 if ordinal==0 else 131)
                       and sample['output_tokens_before']==before,'actual sequential native AR CPU/history owner')
                expected_policy=dict(n=1,temperature=0,top_p=1,min_p=0,repetition_penalty=1,
                    frequency_penalty=0,presence_penalty=0,max_tokens=2,min_tokens=0,ignore_eos=True)
                policy=sample['policy']
                C.need(all(policy[k]==v for k,v in expected_policy.items())and policy['top_k']in(0,-1)
                       and all(policy[k]is True for k in('all_greedy','no_penalties','no_thinking_budget')),
                       'actual neutral native AR policy before original sampling')
                same_bits(t,sample['head']['local_logits'],sample['local_logits'],'actual native unsanitized head→sample logits')
                same_bits(t,sample['head']['hidden'],sample['last_hidden'],'actual native final hidden→head operand')
                C.need(sample['sampler_token_ids'].shape==(1,1)
                       and int(sample['sampler_token_ids'][0,0])==greedy==ar_tokens[generation-1][ordinal],
                       'independent full TP vocabulary argmax equals actual native sampler and HTTP token')
                actual=sample['native_output'];stream=ar_tokens[generation-1][:ordinal+1]
                C.need(actual['req_ids']==[item['request']]and actual['sampled_token_ids']==[[greedy]]
                       and actual['request_output_tokens_after']==stream
                       and actual['num_tokens_no_spec_after']==132+ordinal,'actual native one-token bookkeeping output')
                native_input=sample['input'];expected=frozen['token_ids']if ordinal==0 else before
                C.need(native_input['actual_token_ids'].tolist()==native_input['actual_CPU_token_ids']==expected
                       and native_input['request_prompt_token_ids']==frozen['token_ids']
                       and native_input['request_id']==item['request']and native_input['no_mm_features']is True
                       and native_input['no_soft_prompt']is True
                       and native_input['sources']=={k:m['runtime_sources'][k]for k in('runner','base_runner','qwen35','qwen_next')},
                       'actual native GPU/CPU/request inputs')
                if native_input['actual_input_mode']=='native-text-embeddings':
                    same_bits(t,native_input['actual_native_embeddings'],native_input['independent_token_embeddings'],
                              'actual native embeddings equal original token lookup')
                positions=sample['positions'];linear=list(range(131))if ordinal==0 else[131]
                C.need(positions.dtype==t.int64 and positions.tolist()==(linear if positions.ndim==1 else[linear]*3),
                       'actual sequential native AR positions')
        for rank,item in enumerate(requests):
            retirement=item['retirement']
            C.need(retirement==dict(request=item['request'],request_object_id=item['request_object_id'],
                   generation=generation,actual_output_token_ids=ar_tokens[generation-1],native_removed=True),
                   'actual native AR retirement linked to exact outputs and strong owner')
            frames=item['FA']
            C.need(len(frames)==16 and {f['layer']for f in frames}==set(range(3,64,4))
                   and all(f['request']==item['request']and f['request_object_id']==item['request_object_id']
                           and f['generation']==generation for f in frames),'all16 actual native decode FA operands')
            rank_reports[rank].append(dict(generation=generation,request=item['request'],
                actual_native_greedy_and_HTTP_join=True,FA=[actual_native_fa(t,f)for f in frames]))
    comparisons=compare_tokens(ar_tokens,on_tokens)
    numeric=all(metric['pointwise_pass']for rank in rank_reports for item in rank for frame in item['FA']
                for metric in frame['checks'].values())
    identity_pass=all(r['token_identity_pass']for r in comparisons)
    refs=[C.write(output/('RANK-%d.json'%rank),dict(source=sr,requests=report,budget=budget[rank]))
          for rank,report in enumerate(rank_reports)]
    result=dict(schema='bole.actual-native-ar-bole-token-pair-independent/v1',source=sr,inputs=bundle_ref,
        scope=C.SCOPE,common=common,comparisons=comparisons,ranks=refs,BOLE_independent_gate=on_gate_ref,
        native_AR_full_TP_greedy_verified=True,all_actual_worker_retirements_verified=True,
        native_AR_actual_PA_FIA_pointwise_pass=bool(numeric),token_identity_pass=identity_pass,
        native_AR_reference_smoke_pass=bool(identity_pass and numeric),
        bounded_pair_pass=False,matched_common_plugin_effects_gate_pending=True,
        actual_kernel_routes=sorted({f['route']for r in rank_reports for q in r for f in q['FA']}),
        private_dense_FP16_proof_is_production_native_proof=False,
        global_FA_precision_alignment_qualified=False,long_output_qualified=False,normal_EOS_qualified=False,
        model_ready=False,task_ready=False,performance_ready=False,formal_success=False)
    C.write(output/'ATTRIBUTION.json',result)
    C.need(identity_pass,'actual native AR/BOLE token identities differ; first mismatch retained')
    C.need(numeric,'actual original native paged FA frame exceeds original pointwise bound')
    return result


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--inputs-ref');p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    C.need(a.source_ref and a.inputs_ref and a.output,'explicit owned actual pair inputs/output')
    C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='' and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'
           and not list(Path('/dev').glob('davinci[0-9]*')),'owned Devices[] CPU consumer')
    import torch
    run(torch,json.loads(a.source_ref),json.loads(a.inputs_ref),a.output);return 0


if __name__=='__main__':raise SystemExit(main())
