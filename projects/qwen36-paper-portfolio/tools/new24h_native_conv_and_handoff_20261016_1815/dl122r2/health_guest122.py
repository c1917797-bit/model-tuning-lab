"""Untimed NPU actual051 replay plus production health/flush equivalence.

No changed recurrence or independent-oracle shortcut: every replay is bitwise
joined to the already independently accepted088 sidecar/source/DSO. All320
mixed calls and actual native-prefill flush inputs are covered. No new tensors
are retained; only bounded JSON metrics, the original raw remains read-only.
"""
import argparse,importlib,json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import api122 as A
FIELDS=('base','k_log','u_log','lambda_log','decay','length')
def same(t,a,b):return a.dtype==b.dtype and a.shape==b.shape and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8))
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m,q=A.qualify(sr,pair=False);A.need(m['stage']=='validation','only actual validation source')
 pm,model,owner,producer,bridge=A.component_inputs(m);A.bootstrap_cann(m)
 sys.path[:0]=[pm['root'],str(Path(model['plugin_source']['path']).parent),bridge['root']]
 import torch,torch_npu,raw_codec
 raw_codec.install(torch);torch.set_num_threads(1);torch.npu.set_device(0)
 A.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0,1,2,3'and torch.npu.device_count()==4,'existing025 exclusive TP4 namespace; this bounded validation uses logical0 only')
 from qwen36_deltalog_production106 import primitives as L,health
 from qwen36_deltalog_service import primitives as D
 A.need(A.ref(L.__file__)==pm['files']['qwen36_deltalog_production106/primitives.py']and A.ref(D.__file__)==A.obj(model['plugin_source'])['files']['qwen36_deltalog_service/primitives.py'],'exact actual production/diagnostic arithmetic')
 torch.ops.load_library(pm['library_ref']['path']);op=torch.ops.qwen36_deltalog_split_scale_v051.decode
 A.need(str(op.default._schema)==pm['operator_schema'],'exact051 schema')
 mapped=[s for s in Path('/proc/self/maps').read_text().splitlines()if pm['library_ref']['path']in s];A.need(mapped,'actual mapped051')
 start=time.monotonic();rows=[];model_rows=[];first=None
 def up(x):return {n:x[n].npu().clone()for n in FIELDS}
 def apply(fn,x,ids):
  layer=SimpleNamespace(kv_cache=[None,x['base']]);fn(torch,layer,x,ids,'untimed-production-health');torch.npu.synchronize();return {n:v.cpu()for n,v in x.items()}
 for row in A.model_inputs(m):
  A.need(time.monotonic()-start<560,'original560s numeric cap');side=row['independent']['actual_sidecar_ref'];A.checked(side);raw=torch.load(side['path'],map_location='cpu',weights_only=False)
  A.need(raw['production_library']==pm['library_ref']and raw['model_identity']=={k:row['identity'][k]for k in('source','prefix','layer_idx','pid','rank','epoch','engine_request_id')},'actual same model source/request/epoch/prefix/DSO')
  before=raw['before'];args=[v.npu().clone()for v in before];actual=op(*args);health.observe(torch,actual);torch.npu.synchronize()
  A.need(same(torch,actual.cpu(),raw['production_output'])and all(same(torch,args[i].cpu(),raw['after'][i])for i in range(13)),'unwrapped actual051+productionhealth output/six state/input equals independently accepted model sidecar')
  model_rows.append(dict(identity=row['identity'],raw=side,decode_bitwise=True))
 records=[r for r in producer['records']if r['kind']=='mixed'];A.need(len(records)==320,'all actual component320 inputs')
 for record in records:
  A.need(time.monotonic()-start<560,'original560s numeric cap')
  A.checked(record['raw']);mixed=torch.load(record['raw']['path'],map_location='cpu',weights_only=False);flush=mixed['captures']['prefill_flush088'];A.need(len(flush)==1,'actual component captured native-prefill flush')
  f=flush[0];A.need(f['actual_ids'].flatten().tolist()==[mixed['prefill_slot']],'actual selected prefill slot before compact0 replay');state={n:f['before'][n]for n in FIELDS};ids=torch.tensor([0],device='npu:0',dtype=torch.int32)
  first=first or state;x=apply(D._flush_slots,up(state),ids);y=apply(L._flush_slots,up(state),ids)
  A.need(all(same(torch,x[n],y[n])and same(torch,y[n],f['after'][n])for n in FIELDS),'actual diagnostic/production flush and retained native input bits')
  rows.append(dict(batch=record['batch'],step=record['step'],raw=record['raw'],flush_bitwise=True))
 dead={n:v.clone()for n,v in first.items()};dead['length'].zero_();dead['decay'].zero_()
 for n in('k_log','u_log','lambda_log'):dead[n].fill_(float('nan'))
 ids=torch.tensor([0],device='npu:0',dtype=torch.int32);x=apply(D._flush_slots,up(dead),ids);y=apply(L._flush_slots,up(dead),ids);A.need(all(same(torch,x[n],y[n])for n in FIELDS),'dead NaN remains logically ignored')
 valid=health.snapshot(torch,outside_timing=True);A.need(valid['all_finite'],'all positive production health')
 bad={n:v.clone()for n,v in dead.items()};bad['length'][:,:,0]=1;bad['lambda_log'][:,:,0]=0;bad['k_log'][:,:,0]=.01;bad['u_log'][:,:,0]=float('nan');rejected=False
 try:apply(D._flush_slots,up(bad),ids)
 except RuntimeError as e:A.need('non-finite'in str(e),'only diagnostic nonfinite exception');rejected=True
 apply(L._flush_slots,up(bad),ids);health.observe(torch,torch.ones((1,12,128),device='npu:0'));invalid=health.snapshot(torch,outside_timing=True);A.need(rejected and not invalid['all_finite'],'invalid live flag cannot recover')
 r=pm['files']['qwen36_deltalog_production106/health.py'];negative={}
 for kind,value in(('NaN',float('nan')),('Inf',float('inf'))):
  spec=importlib.util.spec_from_file_location('_122_actual_output_negative_'+kind,A.checked(r));nh=importlib.util.module_from_spec(spec);spec.loader.exec_module(nh)
  nh.observe(torch,torch.ones(1,device='npu:0'));A.need(nh.snapshot(torch,outside_timing=True)['all_finite'],'fresh source-isolated output negative')
  nh.observe(torch,torch.full((1,),value,device='npu:0'));nh.observe(torch,torch.ones(1,device='npu:0'));negative[kind]=nh.snapshot(torch,outside_timing=True);A.need(not negative[kind]['all_finite'],'output invalid sticky after finite')
 A.write(a.output,dict(schema='deltalog.production-health-equivalence/v122',source=sr,production_source=m['production_source_ref'],production_qualification=m['production_qualification_ref'],actual_component_source=pm['component_source_ref'],actual_component_owner=pm['component_owner_ref'],library=pm['library_ref'],mapped=mapped,NPU=True,rows=rows,model_rows=model_rows,all_model216_decode_bitwise=True,all320_flush_bitwise=True,dead_nan_pass=True,valid_health=valid,invalid_health=invalid,output_negative_health=negative,invalid_live_sticky=True,invalid_output_sticky=True,health_scope='observed decode outputs and materialized logical states; not all cache/aux cells',qualified=False,performance=False,elapsed=time.monotonic()-start));return 0
if __name__=='__main__':raise SystemExit(main())
