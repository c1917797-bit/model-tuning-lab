"""Default-OFF V7 production-boundary repeatability consumer; no model qualification."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import types

WS=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
SOURCE=WS/'bound-reduction-ON-v7-startup_20261022T215000Z/SOURCE_BOUND.json'
OUTPUT=Path('/opt/host/vnf/austinov/run-bole-reduction-ON-v7-startup_20261022T215000Z')
BUILDER_REF=dict(path=str(WS/'reduction_admission_prepare_v5_20261022T200000Z/consumer_handoff_prepare/build_actual_handoff.py'),
    bytes=11557,sha256='899ca26611a3ec232a8c90f284e8c384a786bc7250abb9537238cd9ff9d9dbeb')
SHORT_NAMES=('bole_performance_profile','short_state_digest','compare_state_digest','performance_client_consumer')
SHORT_PINS={
 'bole_performance_profile':(4979,'f1ffb4485d8963c06eab882f6c2d8b5700de74025b9663cc705e5df5c88c67f8'),
 'short_state_digest':(11410,'21d95e3cec1b90260229a4fa156981e48bbdaa9a7d466a230c63fbf4d9099ec8'),
 'compare_state_digest':(8418,'a7bdff799d6bc214b69e2da69d3bb8d78ee19dd73c30ef48a22317b27064c826'),
 'performance_client_consumer':(898,'4f517b88ae20ac837955c8c5d1d9e8f9d49ee85d80a349899cded41ba4318c5a')}


def need(v,s):
    if not v:raise ValueError(s)


def builder():
    # The original complete parser/capture/readset code is executed unchanged.
    p=Path(BUILDER_REF['path']);raw=p.read_bytes()
    need(len(raw)==BUILDER_REF['bytes'] and hashlib.sha256(raw).hexdigest()==BUILDER_REF['sha256'],
         'exact original actual handoff builder bytes')
    m=types.ModuleType('_v6_exact_actual_handoff');m.__file__=str(p)
    exec(compile(raw,str(p),'exec'),m.__dict__)
    # Explicit new source/output operands only, no semantic capture-code change.
    m.SOURCE=SOURCE;m.OUTPUT=OUTPUT
    return m


class OriginalC:
    def __init__(self,B,rs):self.B=B;self.rs=rs
    @staticmethod
    def need(v,s):need(v,s)
    def ref(self,p):return self.rs.actual(p,4*2**20)[0]
    def obj(self,r):return self.rs.obj(r,4*2**20)


def module(B,rs,m,name):
    need(name not in sys.modules,'isolated exact source-owned short consumer import '+name)
    ref=m['files'][name+'.py'];raw=rs.include(ref,128*1024,True)
    need((ref['bytes'],ref['sha256'])==SHORT_PINS[name] and
         Path(ref['path'])==Path(m['root'])/(name+'.py'),
         'unchanged original reviewed short-stage semantics and own source path')
    obj=types.ModuleType(name);obj.__file__=ref['path'];sys.modules[name]=obj
    try:exec(compile(raw,ref['path'],'exec'),obj.__dict__)
    except BaseException:
        sys.modules.pop(name,None);raise
    need(B.reference(obj.__file__,128*1024)==ref,'actual loaded short consumer source')
    return obj


def stage_join(B,rs,source_ref,m,host_result_ref):
    need(B.typed(host_result_ref)==OUTPUT/'RESULT.json','exact actual V6 host result operand')
    host=rs.obj(host_result_ref,8*2**20)
    need(host['source']==source_ref and host['primary']is None and
         host['formal_performance']is False and host['candidate_qualification']is False,
         'completed real host result; no numeric/performance promotion')
    loaded=[]
    try:
        for name in SHORT_NAMES:loaded.append(module(B,rs,m,name))
        actual=loaded[-1].consume(C=OriginalC(B,rs),source=source_ref,manifest=m,
            client_output=OUTPUT/'dense/performance-client',receipt_root=Path(m['model_receipt_root']))
        need(actual==host['summary']['streaming_validation'] and
             actual['schema']=='bole.short-state-single-arm-consumption/v1' and
             actual['arm_state_receipts_verified']is True and 32<=actual['rank_frames']<=56 and
             actual['formal_performance']is False and actual['ON_OFF_state_equality']is False,
             'reexecuted original actual HTTP/token/state/lifecycle stagejoin equals retained host stage')
        for ref in actual['readset']:rs.include(ref,4*2**20)
        return actual
    finally:
        for obj in reversed(loaded):
            need(sys.modules.get(obj.__name__)is obj,'only unload own exact imported consumer')
            sys.modules.pop(obj.__name__)


def repeatability(B,rs,records):
    data={};runtime={}
    need(set(records)=={(g,r)for g in(1,2)for r in range(4)},'all eight actual projection receipts')
    for key,(_,obj) in records.items():
        rec=obj['record'];execution=rec['runtime_execution']
        environment=execution['environment']
        need(type(environment)is dict and set(environment)=={'HCCL_DETERMINISTIC','HCCL_ALGO','ASCEND_LAUNCH_BLOCKING'}
             and environment['HCCL_DETERMINISTIC']=='true',
             'actual production worker HCCL_DETERMINISTIC=true, never inferred from requested env')
        need(type(execution['torch_deterministic_enabled'])is bool and
             type(execution['torch_deterministic_warn_only'])is bool,'actual observed Torch policy booleans')
        runtime['G%d-R%d'%key]=execution
        for stage in B.STAGES:
            meta=rec['stages'][stage]
            need(meta['raw']['sha256']==meta['sha256'] and meta['full_actual_tensor']is True and
                 meta['finite']is True,'original graph stage/raw identity and finite witness')
            data[key[0],key[1],stage]=rs.include(meta['raw'],B.NBYTES,True)
    for rank in range(4):
        need(data[1,rank,'pre_reduce']==data[2,rank,'pre_reduce'],
             'per-rank pre_reduce complete bytes identical across G1/G2')
        need(data[1,rank,'post_reduce']==data[2,rank,'post_reduce'],
             'per-rank post_reduce complete bytes identical across G1/G2')
    for generation in(1,2):
        for rank in range(4):
            need(data[generation,rank,'post_reduce']==data[generation,0,'post_reduce'],
                 'post_reduce all four ranks bitwise identical in each generation')
    return dict(runtime_execution=runtime,complete_pre_cross_generation_equal=True,
        complete_post_cross_generation_equal=True,complete_post_cross_rank_equal=True)


def link_projection_stage(B,rs,source_ref,m,records,stage):
    http=rs.obj(stage['http'],128*1024);root=Path(m['model_receipt_root'])
    for (generation,rank),(_,obj) in records.items():
        rec=obj['record'];row=http['rows'][generation-1]
        begin_ref=next(r for r in stage['readset'] if r['path']==str(root/('STATE-BEGIN-G%d-O-1-R%d.json'%(generation,rank))))
        begin=rs.obj(begin_ref,256*1024)['record']
        need(rec['request']==row['id']+'-0' and begin['request']==rec['request'] and
             begin['calibration']['pid']==obj['pid'],'projection request/PID joins real HTTP and state lifecycle')
        name='G%d-RAW-layer0_out_projection.json'%generation
        need(rec['outer_records']['projection']==name,'actual outer projection graph link')
        ref,raw=rs.actual(root/('BOUNDARY-R%d'%rank)/name,128*1024,True)
        outer_obj=B.parse(raw)
        outer=B.envelope(outer_obj,source_ref,rank,generation,'RAW-layer0_out_projection')
        need(outer_obj['pid']==obj['pid'],'outer projection and full internal raw use same real worker')
        post=rec['stages']['post_reduce']
        returned=rec['stages']['projection_return']
        need(returned.get('observed')is True and returned.get('full_actual_tensor')is True and
             returned.get('finite')is True and returned.get('dtype')=='torch.bfloat16' and
             returned.get('shape')==B.SHAPE and returned.get('bytes')==B.NBYTES,
             'complete observed finite BF16 projection-return stage schema')
        need(outer['name']=='layer0_out_projection' and outer['logical_shape']==B.SHAPE and
             outer['logical_bytes']==B.NBYTES and outer['logical_finite']is True and
             outer['logical_sha256']==post['sha256']==returned['sha256'],
             'actual post-reduce/outer native return complete tensor graph identity')
        need(outer['actual_token_slice']==[123,131] and outer['raw_slice_is_full_tensor']is False,
             'original bounded tail slice is not mislabeled complete tensor')
        tail=rs.include(outer['raw'],128*1024,True)
        complete=rs.include(post['raw'],B.NBYTES,True)
        need(len(tail)==8*5120*2 and tail==complete[-len(tail):],
             'outer original saved slice equals complete observed post-reduce raw suffix')
    return True


def consume(source_ref,host_result_ref):
    B=builder();rs=B.Readset();rs.include(BUILDER_REF,128*1024)
    selfref=B.reference(__file__,128*1024);rs.include(selfref,128*1024)
    m,records,completes,raws,bykey=B.capture(source_ref,rs)
    # Flag/repeat checks occur before any original stage execution: historical
    # V5 evidence cannot accidentally be promoted to a production-common pass.
    equality=repeatability(B,rs,bykey)
    stage=stage_join(B,rs,source_ref,m,host_result_ref)
    graph_join=link_projection_stage(B,rs,source_ref,m,bykey,stage)
    consumer_ref=B.reference(B.CONSUMER,128*1024);math_ref=B.reference(B.MATH,128*1024)
    analysis=B.build('analysis',source_ref,rs,consumer_ref=consumer_ref,math_ref=math_ref,tree_cap=0)
    rs.recheck()
    return dict(schema='bole.V6-production-boundary-repeatability/v1',
        source=source_ref,actual_host_result=host_result_ref,consumer=selfref,
        original_handoff_builder=BUILDER_REF,original_stagejoin=stage,
        projection_records=records,completion_records=completes,raw_refs=raws,
        analysis_input=analysis,repeatability=equality,actual_inputs=list(rs.refs.values()),
        projection_HTTP_lifecycle_outer_graph_join=graph_join,
        production_boundary_repeatability=True,diagnostic_only=True,
        numerical_qualified=False,whole_model_pass=False,candidate_qualification=False,
        formal_performance=False,task_accuracy=False,NPU_executed_by_consumer=False,
        limits=['Only first native prefill projection boundary under common deterministic HCCL.',
                'G1 warmup/G2 measured requests do not establish warmed repeated decode.',
                'Does not prove BOLE tree/state mathematics, full-model equivalence, performance, or task accuracy.'])


def main():
    p=argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--source-ref',type=lambda raw:builder().parse(raw))
    p.add_argument('--host-result-ref',type=lambda raw:builder().parse(raw))
    p.add_argument('--output-dir',type=Path)
    a=p.parse_args()
    if not a.execute:
        print(json.dumps(dict(enabled=False,NPU=False,result_written=False)));return 0
    need(a.source_ref and a.host_result_ref and a.output_dir,'actual complete source/host Refs and new output directory')
    B=builder();out=B.ordinary(a.output_dir)
    need(out.parent.is_dir() and not out.exists(),'fresh independent output directory; never override')
    result=consume(a.source_ref,a.host_result_ref)
    # Reopen every original input immediately before exclusive persistence.
    for ref in result['actual_inputs']:B.checked(ref,max(ref['bytes'],128*1024))
    out.mkdir(mode=0o700)
    ref=B.exclusive_json(out/'REPEATABILITY.json',result)
    print(json.dumps(dict(result=ref,production_boundary_repeatability=True,
        numerical_qualified=False,whole_model_pass=False,formal_performance=False),sort_keys=True))
    return 0


if __name__=='__main__':raise SystemExit(main())
