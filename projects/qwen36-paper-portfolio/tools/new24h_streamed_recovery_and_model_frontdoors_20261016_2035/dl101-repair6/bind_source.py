"""Bind only actual052 full160+CPU and actual051 dual build to existing model owner."""
import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import owner_overlay as O
def ref(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def write(p,v):
 with p.open('x',encoding='utf8')as f:json.dump(v,f,sort_keys=True);f.write('\n')
def bind_actual_bridge(m,sr,bm):
 reviewed=O.obj(m['reviewed_domain_template_ref'])
 O.need(bm['prepared_template']==m['reviewed_domain_template_ref']and bm['files']==m['reviewed_domain_files']==reviewed['files']and bm['root']==reviewed['root']and bm['prepared_only']is False and bm['validation_contract']==reviewed['validation_contract'],'only final052 target source/reference contract')
 O.need(m.get('expected_bound_bridge_ref')is None or m['expected_bound_bridge_ref']==sr,'bound target substitution rejected')
 m['expected_bound_bridge_ref']=sr
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-sha256')
 for k in('bridge-source-ref','bridge-owner-ref','component-cpu-owner-ref','recovery-model-plan-ref','recovery-receiver-source-ref'):p.add_argument('--'+k)
 a=p.parse_args()
 if not a.execute:print('disabled');return 0
 tr=ref(P/'SOURCE_TEMPLATE.json');O.need(tr['sha256']==a.template_sha256,'MAIN reviewed053 template')
 m=O.obj(tr);O.need(m['root']==str(P)and m['prepared_only']is True,'actual immutable053 deployment')
 O.need(type(m.get('reviewed_domain_template_ref'))is dict and type(m.get('reviewed_domain_files'))is dict and m['reviewed_domain_files'],'final reviewed052 pins pending')
 sr=json.loads(a.bridge_source_ref);bm=O.obj(sr);reviewed=O.obj(m['reviewed_domain_template_ref'])
 bind_actual_bridge(m,sr,bm)
 owner=json.loads(a.bridge_owner_ref);cpu=json.loads(a.component_cpu_owner_ref)
 m.update(admission_mode='actual052-split-scale-diagnostic-only',prepared_only=False,prepared_template=tr,bridge024_source_ref=sr,bridge024_owner_ref=owner,component_cpu_owner_ref=cpu,production_build_ref=bm['split_build_ref'],debug_build_ref=bm['debug_build_ref'],split_kernel_source_ref=bm['split_kernel_source_ref'],debug_kernel_source_ref=bm['debug_kernel_source_ref'],library_ref=bm['library_ref'],debug_library=bm['debug_library'],composite_source_ref=bm['composite_source_ref'],composite_cpu_owner_ref=bm['composite_cpu_owner_ref'])
 O.need(a.recovery_model_plan_ref is not None and a.recovery_receiver_source_ref is not None,'actual recovery input/reader source pending')
 m.update(recovery_model_plan_ref=json.loads(a.recovery_model_plan_ref),recovery_receiver_source_ref=json.loads(a.recovery_receiver_source_ref))
 O.need(m['recovery_receiver_source_ref']==m['recovery_receiver_template_ref'],'exact final source-bound128 receiver, no old R2 alias')
 pt=P/'plugin/SOURCE_TEMPLATE.json';pm=O.obj(m['plugin_template_ref']);O.need(ref(pt)==m['plugin_template_ref'],'exact new053 plugin template')
 operator='qwen36_deltalog_split_scale_v051::decode(Tensor query, Tensor key, Tensor value, Tensor g, Tensor beta, Tensor(a!) base_state, Tensor(b!) k_log, Tensor(c!) u_log, Tensor(d!) lambda_log, Tensor(e!) cumulative_decay, Tensor(f!) log_length, Tensor actual_seq_lengths, Tensor state_indices) -> Tensor'
 for k in('recovery_model_plan_ref','recovery_receiver_source_ref','admission_mode','reviewed_domain_template_ref','reviewed_domain_files','bridge024_source_ref','bridge024_owner_ref','component_cpu_owner_ref','production_build_ref','debug_build_ref','split_kernel_source_ref','debug_kernel_source_ref','library_ref','debug_library','composite_source_ref','composite_cpu_owner_ref'):
  pm[k]=m[k]
 pm.update(prepared_only=False,prepared_template=m['plugin_template_ref'],operator_schema=operator)
 rp=O.obj_file(pm['files']['qwen36_deltalog_service/split_qualification.py'])
 import importlib.util
 sp=importlib.util.spec_from_file_location('_053_shared052_actual',rp);Q=importlib.util.module_from_spec(sp);sp.loader.exec_module(Q)
 # Complete all original numerical gates before publishing either source.
 Q.admit(O,pm)
 recovered=Q.closure(O,pm);descriptor=recovered.descriptor
 O.need(type(descriptor)is dict and set(descriptor)=={'schema','index_ref','entries','parents','parent_count'},'authenticated small recovery index descriptor')
 pm['recovery_readset_index']=m['recovery_readset_index']=descriptor
 m['split_qualification_api_ref']=pm['files']['qwen36_deltalog_service/split_qualification.py']
 plugin_path=P/'plugin/SOURCE_MANIFEST.json';write(plugin_path,pm);m['plugin_source']=ref(plugin_path)
 O.model_gate(m)
 from itertools import chain
 for r in chain(m['files'].values(),m['dependencies'],O.transitive_refs(m)):O.obj_file(r)
 O.need('torch'not in sys.modules and'torch_npu'not in sys.modules,'host lightweight receipt only')
 write(P/'SOURCE_MANIFEST.json',m);print(json.dumps(dict(source=ref(P/'SOURCE_MANIFEST.json'),model_ready=False,NPU=False)));return 0
if __name__=='__main__':raise SystemExit(main())
