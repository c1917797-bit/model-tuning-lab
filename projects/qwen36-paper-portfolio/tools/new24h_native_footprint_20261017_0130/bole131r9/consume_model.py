"""Owned Devices[] consumer: four actual ranks, original component gates only."""
import argparse,json,sys,traceback
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import independent_model as I
import identity_oracle as O
import oracle112


PROFILE=dict(endpoint='/v1/completions',prompt_count=1,n=1,beam_search=False,streaming_input=False)


def vocabulary_join(t,vocabulary):
 C.need(len(vocabulary)==4,'exact four actual native MTP vocabulary shards')
 policies=[v['policy']for v in vocabulary];C.need(all(p==policies[0]for p in policies),'all4 exact native vocabulary policy/source')
 policy=policies[0];C.need(policy['lmhead_tp']is False and type(policy['reduce_sample'])is bool,'actual source-proved common native vocabulary domain')
 actual=t.cat([v['local']for v in vocabulary],dim=-1)[:,:policy['vocab_size']]if policy['reduce_sample']else vocabulary[0]['local']
 C.need(actual.dtype==t.float32 and actual.shape==(1,policy['vocab_size'])and bool(t.isfinite(actual).all()),'independently assembled actual TP4 first MTP vocabulary')
 for v in vocabulary:
  C.need(I.bits(t,v['global_logits'],actual)and I.bits(t,v['target'],vocabulary[0]['target'])and
         v['tokens']==vocabulary[0]['tokens'],'all4 actual global vocabulary/logit/tree identity')
  chosen=v['children'];C.need(chosen.shape==(1,2)and chosen.dtype==t.int64 and int(chosen[0,0])!=int(chosen[0,1]),'two distinct actual MTP top candidates')
  values=actual.gather(1,chosen).sort(descending=True).values
  C.need(t.equal(values,t.topk(actual,2,dim=-1).values),'independent actual global MTP top2 values (no invented stable tie order)')
 return True


def identity_join(sr,bundle):
 http=C.obj(bundle['http']);C.need(http['source']==sr and [r['label']for r in http['rows']]==['tree','retirement-barrier'],'actual two bounded HTTP requests')
 tree=http['rows'][0];response=C.obj(tree['response'])
 events=[C.obj(r)for r in bundle['journal']]
 C.need(all(e['schema']=='bole.actual-identity-journal/v1'and e['source']==sr for e in events),'same-source actual identity journal')
 assignments=[e['event']for e in events if e['role']=='frontend'and e['kind']=='assignment'and e['event']['before_request_id']==response['id']+'-0']
 C.need(len(assignments)==1,'one original actual InputProcessor assignment')
 frontend=bundle['frontend_binding']
 C.need(frontend['guest']==assignments[0]['identity']and frontend['NSpid'][-1]==frontend['guest']['pid']and
        frontend['owned_cid']in frontend['host']['cgroup']and
        frontend['host']['start_ticks']==frontend['guest']['start_ticks'],'independently owned actual frontend identity binding')
 passed,assigned=O.validate_assignment(response['id'],PROFILE,assignments[0])
 C.need(response['id']==O.expected_server_id(tree['header'],None),'actual response/header join')
 snapshots={r['pid']:r for r in bundle['snapshots']};bindings={};traces=[]
 for rank in range(4):
  rows=[e['event']for e in events if e['role']=='rank%d'%rank and e['kind']=='worker_update']
  C.need(rows and all(e['rank']==rank for e in rows),'all4 actual worker journals')
  identity=rows[0]['identity'];snapshot=snapshots.get(identity['pid'])
  C.need(snapshot is not None and snapshot['source_ref']==sr and snapshot['allow_hf32']is False,'same actual native source/precision snapshot worker')
  rest=snapshot['proc_stat'][snapshot['proc_stat'].rfind(')')+2:].split()
  C.need(identity==dict(pid=snapshot['pid'],start_ticks=int(rest[19]),cgroup=snapshot['cgroup']),'exact guest PID/start/cgroup snapshot join')
  actual=[b for b in bundle['host_bindings']if b['guest']==snapshot]
  C.need(len(actual)==1 and actual[0]['host']['physical']in(4,5,6,7),'actual owned host/NSpid snapshot authority')
  bindings[rank]=identity;traces.append(dict(schema='vllm023.actual-worker-retirement/v1',rank=rank,identity=identity,events=rows))
 C.need(len({x['pid']for x in bindings.values()})==4 and {b['host']['physical']for b in bundle['host_bindings']}=={4,5,6,7},'distinct all4 owned actual workers')
 O.validate_worker_retirement(assigned,traces,bindings)
 return assigned,bindings


def run(t,sr,bundle_ref,out):
 m=C.obj(sr);C.need(m['prepared_only']is False and m['whole_numerical_qualification']is False,'source-bound diagnostic only')
 C.need(m['root']==str(P),'actual deployed independent consumer source root')
 for reference in m['files'].values():C.checked(reference)
 bundle=C.obj(bundle_ref);C.need(bundle['source']==sr,'exact source-bound host input ledger')
 assigned,bindings=identity_join(sr,bundle);reports=[];rows=[];vocabulary=[]
 C.need(len(bundle['ranks'])==4,'all4 exact capture refs')
 for expected,pair in enumerate(bundle['ranks']):
  C.need(pair['receipt']['path']==str(Path(m['model_receipt_root'])/('BOLE-TREE-RANK-%d.json'%expected))and
         pair['raw']['path']==str(Path(m['model_receipt_root'])/('BOLE-TREE-RANK-%d.pt'%expected)),
         'exact genuine worker capture filenames in sole declared owned leaf')
  receipt=C.obj(pair['receipt']);C.need(receipt['source']==sr and receipt['rank']==expected and receipt['primary']is None and receipt['raw']==pair['raw'],'actual source/rank/raw/firstfault receipt')
  rest=receipt['stat'][receipt['stat'].rfind(')')+2:].split()
  C.need(dict(pid=receipt['pid'],start_ticks=int(rest[19]),cgroup=receipt['cgroup'])==bindings[expected],
         'capture and independent owned worker PID/start/cgroup identity')
  exported=t.load(C.checked(pair['raw']),map_location='cpu',weights_only=False)
  C.need(exported['schema']=='bole.model-diagnostic-primitives/v1'and
         0<=exported['logical_tensor_bytes']<=exported['cap_bytes']==2**30,'actual bounded primitive-only diagnostic export')
  raw=exported['payload']
  C.need(raw['source']==sr and raw['rank']==expected and raw['request']['request']==assigned,'actual assigned engine ID, not predicted HTTP ID')
  vocabulary.append(dict(policy=raw['native_logits_policy'],local=raw['genuine_MTP']['first_local_logits'].clone(),
   global_logits=raw['genuine_MTP']['first_logits'].clone(),children=raw['genuine_MTP']['children'].clone(),
   tokens=raw['tree_context']['tokens'],target=raw['staged']['actual_target_logits'].clone()))
  observation=raw['actual_native_prefill_input']
  C.need(observation['sources']=={k:m['runtime_sources'][k]for k in('runner','base_runner','qwen35','qwen_next')},'actual native-input source join')
  report,vectors=I.consume(t,raw,oracle112)
  path=out/('VECTORS-rank%d.pt'%expected)
  with path.open('xb')as f:t.save(vectors,f)
  C.need(path.stat().st_size<=2**30,'bounded complete numerical difference vectors')
  vector_ref=C.ref(path);r=C.write(out/('RANK-%d.json'%expected),dict(source=sr,receipt=pair['receipt'],raw=pair['raw'],report=report,vectors=vector_ref))
  reports.append(r);rows.append(report);del raw,vectors,exported
 vocabulary_join(t,vocabulary)
 result=dict(schema='bole.actual-model-three-node-four-rank-diagnostic/v1',source=sr,inputs=bundle_ref,ranks=reports,
  diagnostic_complete=True,component_checks_pass=all(x['component_checks_pass']for x in rows),
  actual_all4_retirement=True,actual64_layers_per_rank=True,whole_numerical_qualified=False,whole_numerical_threshold=None,
  independent_actual_MTP_TP4_vocabulary_join=True,
  scheduler_committed=False,model_ready=False,performance_ready=False,task_ready=False,
  scope='C1/131/native-MTP-root+two-siblings/selected-request-cache-stage-and-restore')
 C.write(out/'ATTRIBUTION.json',result)
 C.need(result['component_checks_pass'],'original component mathematical gates failed; all actual metrics/vectors preserved')
 return result


def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--inputs-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 import os
 C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','actual owned Devices[] consumer')
 import torch
 C.need(not list(Path('/dev').glob('davinci[0-9]*')),'no device nodes in independent CPU consumer')
 try:run(torch,json.loads(a.source_ref),json.loads(a.inputs_ref),a.output)
 except BaseException as e:C.write(a.output/'FAILURE.json',dict(primary=repr(e),traceback=traceback.format_exc()));raise
 return 0


if __name__=='__main__':raise SystemExit(main())
