"""Final independent source/ACK/HTTP/actual-retirement join. No new numerics.

Full numerical consumption already occurred in the owned Devices[] process;
this finalizer audits its durable receipts and actual all4 worker retirement.
Released successful raw frames are deliberately unavailable for replay.
"""
import argparse,json,os,sys
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import g2_contract as G2
import g1_contract as G1
import g2_channel as CH
CM=None


def identity_join(sr, bundle):
    """Consume original actual identity semantics twice, then enforce lifecycle order."""
    http = C.obj(bundle["http"])
    C.need(http["schema"] == G1.HTTP_SCHEMA and http["source"] == sr
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
        C.need(len(rows) <= max(512,2*G2.MAX_OUTPUT+32) and sum(r["bytes"] for r, _ in rows) <= 8 * 2**20
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
        _, actual = CM.O.validate_assignment(response["id"], CM.PROFILE, matches[0])
        C.need(response["id"] == CM.O.expected_server_id(row["header"], None),
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
        CM.O.validate_worker_retirement(rid, traces, bindings)
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
                   "no two live G2 request owners in a C1 worker")
    return assigned, bindings



def owned_channel(m,sr,cr):
    ch=CH.contract(C,sr,cr)
    for role in('consumer','model'):
        owner=C.obj(ch[role+'_owner_ref']);inspection=C.obj(ch[role+'_inspect'])
        rows=json.loads(inspection['stdout']);C.need(len(rows)==1,'one complete actual inspected container')
        actual=rows[0];h=actual['HostConfig'];cfg=actual['Config']
        cpu=role=='consumer';budget=1 if cpu else 3
        C.need(actual['Id']==owner['cid']and actual['Image']==owner['image']and
            cfg['Image']==owner['image']and actual['Name']=='/'+owner['name']and
            owner['source']==sr and actual['State']['Running']and actual['State']['Pid']>0 and
            cfg['Labels']['model-tuning-lab.source-manifest-sha256']==sr['sha256']and
            h['Memory']==h['MemorySwap']==(8 if cpu else 32)*2**30 and
            h['NanoCpus']==budget*10**9 and h['CpusetCpus']==('145'if cpu else'0,1,2')and
            h['ReadonlyRootfs']is True and not h.get('Tmpfs')and h['NetworkMode']=='none',
            'actual owned immutable image/source/CPU/memory/isolation profile')
        mounts={x['Destination']:[x['Source'],x['RW']]for x in actual['Mounts']}
        C.need(mounts==owner['mounts'],'complete independently reopened exact mount closure')
        devices=h.get('Devices')or[]
        C.need(len(devices)==(0 if cpu else 7),'actual consumer Devices[] and model exact physical4..7/control7')
        if cpu:
            C.need(mounts[m['root']]==[m['root'],False]and
                mounts[m['model_receipt_root']]==[m['model_receipt_root'],False]and
                all(not rw or source==m['stream_channel_root']for source,rw in mounts.values()),
                'consumer reads source/full model receipts and writes only exact owned nested channel')
        else:
            actualmap={v['PathOnHost']:v['PathInContainer']for v in devices}
            expected={'/dev/davinci%d'%p:'/dev/davinci%d'%i for i,p in enumerate((4,5,6,7))}
            expected.update({'/dev/'+n:'/dev/'+n for n in('davinci_manager','devmm_svm','hisi_hdc')})
            C.need(actualmap==expected,'only exact owned physical4..7 map')
    life=ch['consumer_lifetime'];identity=ch['actual_consumer_identity']
    C.need(life['guest']==identity and life['NSpid'][-1]==identity['pid']and
        life['host']['start_ticks']==identity['start_ticks']and
        life['owned_cid']in life['host']['cgroup']and ch['consumer_cpu_view']['effective_cpus']==[145]and
        ch['consumer_cpu_view']['effective_capacity']==1,'actual independent consumer PID/start/cgroup/quota')
    return ch


def finalize(t,sr,bundle):
    global CM
    import identity_oracle as O
    CM=SimpleNamespace(O=O,PROFILE=dict(endpoint='/v1/completions',prompt_count=1,n=1,beam_search=False,streaming_input=False))
    m=C.obj(sr)
    C.need(bundle['schema']=='bole.actual-stream-final-inputs/v2'and bundle['source']==sr and
        C.ref(__file__)==m['files']['g2_finalize.py']and C.ref(O.__file__)==m['files']['identity_oracle.py'],
        'exact independent G2 finalizer/source/original identity oracle')
    import command_contract
    commands=command_contract.validate(C,sr,m)
    for r in(*m['files'].values(),*m['runtime_sources'].values(),*m['dependencies']):C.checked(r)
    cr=bundle['channel'];channel=owned_channel(m,sr,cr);root=Path(channel['root'])
    exit_ref=C.ref(root/'STREAM_CONSUMER_EXIT.json');exit=C.obj(exit_ref)
    C.need(exit['schema']=='bole.actual-stream-consumer-exit/v2'and exit['source']==sr and
        exit['channel_ref']==cr and exit['consumer_source']==m['stream_consumer_source']and
        exit['identity']==channel['actual_consumer_identity']and exit['primary']is None and
        exit['completed']is True and exit['source_unchanged']is True and
        exit['successful_raw_replay_available']is False and exit['timing_is_formal']is False,
        'actual exact independent numerical process exit, unchanged sources and complete coverage')
    C.need(all(v['schema']=='dense.native-worker-snapshot/v090'and v['native_core']is v['native_inverse']is True and
        v['source_ref']==sr and v['allow_hf32']is False for v in bundle['snapshots']),
        'all4 actual native class/HF32OFF restoration snapshots after native barrier')
    assigned,bindings=identity_join(sr,bundle)
    C.need(bindings==dict(enumerate(channel['actual_worker_identities'])),'same actual all4 channel and journal workers')
    completed=exit['requests'];C.need(len(completed)==4 and all(len(v)==2 for v in completed),'all4 both real requests consumed')
    inputs=C.obj(bundle['http']);budget=G2.MAX_OUTPUT;reports=[];all_acks=[]
    for ordinal,(row,count)in enumerate(zip(inputs['rows'],(budget,budget,1))):
        response=C.obj(row['response']);request=row['request']
        C.need(row['header']=='bole-g2-131-'+row['label']and request==dict(
            model='qwen36-mxr-eager',prompt=completed[0][0]['prefix_token_ids'],max_tokens=count,
            temperature=0,top_p=1,n=1,stream=False,ignore_eos=True,return_token_ids=True)and
            row['http_status']==200 and len(response['choices'])==1 and
            response['usage']['prompt_tokens']==131 and response['usage']['completion_tokens']==count and
            len(response['choices'][0]['token_ids'])==count,
            'actual complete deterministic token-ID HTTP protocol')
        if ordinal<2:
            for rank in range(4):
                v=completed[rank][ordinal]
                C.need(v['request']==assigned[ordinal]and v['generation']==ordinal+1 and
                    v['output_token_ids']==response['choices'][0]['token_ids']and
                    2<=v['steps']<=budget-1 and v['processed_tokens']==budget-1 and
                    v['next_counter_ACKs']==v['steps']-1 and v['component_checks_pass']is True,
                    'entire HTTP emitted stream joins every consumed step and actual final retirement')
    for rank,entry in enumerate(bundle['ranks']):
        receipt=C.obj(entry['receipt']);C.need(receipt['schema']=='bole.actual-worker-stream-receipt/v2'and
            receipt['source']==sr and receipt['rank']==rank and receipt['primary']is None and
            receipt['retained_unACK_raw']==[]and receipt['raw']==entry['raw']and
            receipt['pid']==bindings[rank]['pid'],'actual completed rank metadata export and no pending raw')
        exported=t.load(C.checked(entry['raw']),map_location='cpu',weights_only=False)
        C.need(exported['logical_tensor_bytes']==0,'final rank output contains only bounded metadata')
        raw=exported['payload'];events=raw['stream_events'];previous=None;coverage=[];per_acks=[]
        expected=[]
        for ordinal,item in enumerate(completed[rank]):
            expected += ['open']+['step']*item['steps']+['retire']
        expected+=['close']
        C.need(raw['schema']==G1.RAW_SCHEMA and raw['source']==sr and raw['rank']==rank and
            raw['source_after']==m['files']and raw['runtime_sources_after']==m['runtime_sources']and
            raw['primary']is None and raw['stream_channel_ref']==cr and
            [e['kind']for e in events]==expected and len(events)==exit['actual_frame_batches']and
            len(raw['requests'])==2,'complete retained source-frozen per-rank event chain')
        for sequence,event in enumerate(events):
            manifest=C.obj(event['manifest']);ack=C.obj(event['ack']);release=C.obj(event['release'])
            C.need(sequence==event['sequence']==manifest['sequence']and manifest['rank']==rank and
                manifest['kind']==event['kind']and manifest['source']==sr and manifest['channel_ref']==cr and
                manifest['nonce']==channel['nonce']and manifest['previous_ack']==previous and
                event['coverage']==manifest['coverage'],'exact contiguous source-bound complete event coverage')
            CH.validate_ack(ack,manifest,consumer_source=m['stream_consumer_source'],channel_ref=cr,previous_ack=previous)
            C.need(release==dict(schema='bole.actual-stream-frame-release/v2',source=sr,rank=rank,
                sequence=sequence,manifest=event['manifest'],ack=event['ack'],raw=manifest['raw'],
                released_after_successful_ACK=True,successful_raw_replay_available=False)and
                not Path(manifest['raw']['path']).exists(),'successful raw released only behind exact durable successful oracle ACK')
            coverage.append(manifest['coverage']);per_acks.append(event['ack']);previous=event['ack']
        import g2_coverage
        coverage_proof=g2_coverage.audit(events,completed[rank],raw['requests'])
        all_acks+=per_acks
        C.need(len(raw['requests'])==2 and all(raw['requests'][i]['output_token_ids']==completed[rank][i]['output_token_ids']and
            raw['requests'][i]['request']['request']==assigned[i]and
            raw['requests'][i]['retirement']['final_ack_by_retirement_pending']is True for i in range(2)),
            'final pending publications closed by actual identity-journal retirement, never invented next ingress')
        # Reopen every retained observer/calibration/journal Ref and include final
        # consumer exit/worker metadata, rather than trusting an early byte count.
        evidence={r['path']:r for r in receipt['evidence_refs']}
        evidence.update({str(p):C.ref(p)for p in root.glob('*.json')if 'RANK-'not in p.name})
        evidence.update({entry['receipt']['path']:entry['receipt'],entry['raw']['path']:entry['raw']})
        for r in evidence.values():C.checked(r)
        used=sum(r['bytes']for r in evidence.values())
        C.need(used<=G2.METADATA_CAP and not list(root.glob('FRAME-RANK-%d-*.pt'%rank)),
            'actual complete final per-rank calibration/journal/ACK/exit/summary bytes within64MiB and1GiB')
        observed=[x['observation']for x in completed[rank]]
        reuse=dict(GDN=observed[0]['GDN_slots']==observed[1]['GDN_slots'],
            FA=observed[0]['FA_pages']==observed[1]['FA_pages'])
        reports.append(dict(rank=rank,requests=completed[rank],all_frames_consumed=True,
            final_metadata_bytes=used,slot_reuse_observed=reuse,coverage_proof=coverage_proof))
    C.need({r['path']for r in all_acks}=={r['path']for r in exit['ACKs']}and len(all_acks)==len(exit['ACKs']),
        'actual numerical process ACK set exactly covers all4 complete worker event chains')
    return dict(schema='bole.actual-G2-stream-attribution/v2',source=sr,scope=G2.SCOPE,
        consumer_exit=exit_ref,channel=cr,commands=commands,ranks=reports,
        service_complete=True,completed_request_count=2,component_checks_pass=True,
        scheduler_committed_independently=True,all4_worker_retirement_verified=True,
        every_frame_independently_consumed=True,successful_raw_replay_available=False,
        physical_allocation_growth_proven=False,normal_EOS_qualified=False,
        native_AR_token_identity_compared=False,model_ready=False,task_ready=False,
        performance_ready=False,formal_success=False,timing_is_formal=False)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--inputs-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    C.need(os.environ.get(G2.FLAG)=='1'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and
        not list(Path('/dev').glob('davinci[0-9]*')),'explicit actual Devices[] finalizer')
    import torch
    value=finalize(torch,json.loads(a.source_ref),C.obj(json.loads(a.inputs_ref)))
    reference=C.write(a.output/'ATTRIBUTION.json',value);print(json.dumps(reference));return 0


if __name__=='__main__':raise SystemExit(main())
