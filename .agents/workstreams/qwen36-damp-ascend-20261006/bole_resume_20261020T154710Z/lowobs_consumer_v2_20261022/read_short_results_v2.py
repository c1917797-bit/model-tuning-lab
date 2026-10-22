"""Consume only retained real low-observation short results; no owners/devices."""
import argparse,hashlib,importlib.util,json,os,sys
from pathlib import Path
ON={"bytes":1680250,"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_performance_profile_prepare_20261021/successor_layer/formal_pair_prepare_v1/revision3/bound-lowobs-short-ON-v1/SOURCE_BOUND.json","sha256":"649df148853c3e37159bf9eaab58ed19e31398379087ea9143d6ca0eea747899"}
OFF={"bytes":1681352,"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_performance_profile_prepare_20261021/successor_layer/formal_pair_prepare_v1/revision3/bound-lowobs-short-OFF-v1/SOURCE_BOUND.json","sha256":"bfb320f57dfb24747ed4ec579c2288b0d291256c938b029a2149d15563199683"}
ROOT=Path(__file__).resolve().parent
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);need(p.is_file()and not any(x.is_symlink()for x in (p,*p.parents)),'ordinary evidence')
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and 0<r['bytes']<=16*2**20,'bounded exact Ref')
 need(ref(r['path'])==r,'immutable complete evidence');return json.loads(Path(r['path']).read_bytes())
def cleanup_obj(summary,expected_path):
 p=Path(__file__).resolve().parent/'cleanup_summary.py'
 need(p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary pinned cleanup helper')
 with p.open('rb')as f:b=f.read(3958)
 need(len(b)==3957 and hashlib.sha256(b).hexdigest()=='1c2e014303bec214cff2e19d8c428eee1a13d69c3f8b525308b3ae958faf9687','exact copied cleanup summary helper')
 scope={'__name__':'_bole_lowobs_cleanup_summary_v2','__file__':str(p)}
 exec(compile(b,str(p),'exec'),scope)
 return scope['read_cleanup_summary'](summary,expected_path)[1]
def arm(sr,rr):
 m=obj(sr);v=obj(rr);out=Path(m['output_root'])
 need(Path(rr['path'])==out/'RESULT.json'and v['source']==sr and v['schema']=='bole.actual-three-node-model-owned/v131'
  and v['cpu_only']is False and v['primary']is None and v['secondary']==[]and v['source_before']==v['source_after'],'actual complete model source/result')
 s=v['summary']
 for k in ('model_release','CPU_release'):
  r=cleanup_obj(s[k],out/('dense'if k=='model_release'else'cpu-preflight')/'cleanup.json');need(r['stopped']is True and r['retained']is True and r['errors']==[],'actual release')
 c=obj(s['CPU_report']);need(c['source']==sr and c['pass_preflight']is True and c['Devices']==[],'same-image preflight')
 c=obj(s['actual_client_terminal']);need(c['exit_code']==0,'actual complete client')
 need(len(s['worker_snapshots'])==4,'all4 worker snapshots')
 for r in s['worker_snapshots']:need(r['source_ref']==sr and r['native_core']is True and r['native_inverse']is True and r['allow_hf32']is False,'native barrier real restored precision')
 http=s['streaming_validation']['http'];need(http==ref(out/'dense/performance-client/HTTP_RESULT.json'),'original bound short HTTP result')
 need(s['streaming_validation']['source']==sr and s['streaming_validation']['arm_state_receipts_verified']is True,'original single-arm independent state consumer')
 return m,http
def consume(on_result,off_result):
 a,ah=arm(ON,on_result);b,bh=arm(OFF,off_result)
 expected=a['files']['compare_state_digest.py'];need(expected['sha256']==b['files']['compare_state_digest.py']['sha256'],'identical independent reader')
 need(ref(expected['path'])==expected,'source-owned reader')
 sys.path.insert(0,a['root'])
 spec=importlib.util.spec_from_file_location('_actual_lowobs_pair_reader',expected['path']);R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
 need(ref(R.__file__)==expected,'actual reader path')
 result=R.compare(ON,OFF,Path(a['model_receipt_root']),Path(b['model_receipt_root']),ah,bh)
 result.update(actual_model_results=[on_result,off_result],retained_complete_model_results=True,paired_fixed1024_qualified=False,
  scope='observational elision full committed-state equality for131 input, two8-token generations')
 return result
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--on-result-ref',required=True,type=json.loads);p.add_argument('--off-result-ref',required=True,type=json.loads)
 a=p.parse_args();out=ROOT/'LOWOBS_SHORT_NPU_COMPARE_v2.json';need(not out.exists(),'exclusive actual comparison output')
 result=consume(a.on_result_ref,a.off_result_ref)
 with out.open('xb')as f:f.write((json.dumps(result,sort_keys=True)+'\n').encode());f.flush();os.fsync(f.fileno())
 print(json.dumps(dict(result=ref(out),state_digest_equal=result['state_digest_equal'],NPU_executed_here=False,formal_performance=False)))
if __name__=='__main__':main()
