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
 for k in('bridge-source-ref','bridge-owner-ref','component-cpu-owner-ref'):p.add_argument('--'+k)
 p.add_argument('--closed-evidence-ref',required='--execute'in sys.argv)
 a=p.parse_args()
 if not a.execute:print('disabled');return 0
 tr=ref(P/'SOURCE_TEMPLATE.json');O.need(tr['sha256']==a.template_sha256,'MAIN reviewed053 template')
 m=O.obj(tr);O.need(m['root']==str(P)and m['prepared_only']is True,'actual immutable053 deployment')
 # Derived ticket cannot be inside the template that contains its own hash.
 # Bind its exact Ref only after the source-owned spec/template whole join,
 # before reading any original component or closed historical data.
 pstatic=O.obj_file(m['files']['prebind_static.py'])
 import importlib.util
 ss=importlib.util.spec_from_file_location('_r21_bound_command_source',pstatic);STATIC=importlib.util.module_from_spec(ss);ss.loader.exec_module(STATIC)
 STATIC.bind(O,m,tr,P)
 O.need(type(m['firstdecode_contract'].get('prior_r23_terminal_evidence_ref'))is dict,'actual terminal R23 created-candidate/released-empty evidence pending; do not bind before original RESULT')
 # Actual complete same-image suite must precede any old closedraw rebind.
 import early_software_gate22 as EARLY
 m['early_software_admission']=EARLY.require(O,m,tr)
 m['dependencies'].extend(m['early_software_admission']['readset'])
 O.need(type(m.get('reviewed_domain_template_ref'))is dict and type(m.get('reviewed_domain_files'))is dict and m['reviewed_domain_files'],'final reviewed052 pins pending')
 sr=json.loads(a.bridge_source_ref);bm=O.obj(sr);reviewed=O.obj(m['reviewed_domain_template_ref'])
 bind_actual_bridge(m,sr,bm)
 owner=json.loads(a.bridge_owner_ref);cpu=json.loads(a.component_cpu_owner_ref)
 import firstdecode_refs as F
 m['firstdecode_contract']['closed_evidence_ref']=json.loads(a.closed_evidence_ref)
 O.obj_file(m['files']['readonly_binder_guard.py'])
 import readonly_binder_guard as RG
 readonly=RG.Guard(O,m,tr)
 m['firstdecode_contract']['closed_readset']=F.bind_closed(O,m['firstdecode_contract'],readonly)
 m['readonly_binder_observation']=dict(program_ref=readonly.program,template_ref=tr,verified_processes=readonly.verified,FD_and_maps_not_exempt=True,execution_or_consumer_exception=False)
 m.update(admission_mode='actual052-split-scale-diagnostic-only',prepared_only=False,prepared_template=tr,bridge024_source_ref=sr,bridge024_owner_ref=owner,component_cpu_owner_ref=cpu,production_build_ref=bm['split_build_ref'],debug_build_ref=bm['debug_build_ref'],split_kernel_source_ref=bm['split_kernel_source_ref'],debug_kernel_source_ref=bm['debug_kernel_source_ref'],library_ref=bm['library_ref'],debug_library=bm['debug_library'],composite_source_ref=bm['composite_source_ref'],composite_cpu_owner_ref=bm['composite_cpu_owner_ref'])
 pt=P/'plugin/SOURCE_TEMPLATE.json';pm=O.obj(m['plugin_template_ref']);O.need(ref(pt)==m['plugin_template_ref'],'exact new053 plugin template')
 operator='qwen36_deltalog_split_scale_v051::decode(Tensor query, Tensor key, Tensor value, Tensor g, Tensor beta, Tensor(a!) base_state, Tensor(b!) k_log, Tensor(c!) u_log, Tensor(d!) lambda_log, Tensor(e!) cumulative_decay, Tensor(f!) log_length, Tensor actual_seq_lengths, Tensor state_indices) -> Tensor'
 for k in('short_model_diagnostic_scope','admission_mode','reviewed_domain_template_ref','reviewed_domain_files','bridge024_source_ref','bridge024_owner_ref','component_cpu_owner_ref','production_build_ref','debug_build_ref','split_kernel_source_ref','debug_kernel_source_ref','library_ref','debug_library','composite_source_ref','composite_cpu_owner_ref'):
  pm[k]=m[k]
 pm.update(prepared_only=False,prepared_template=m['plugin_template_ref'],operator_schema=operator)
 rp=O.obj_file(pm['files']['qwen36_deltalog_service/split_qualification.py'])
 import importlib.util
 sp=importlib.util.spec_from_file_location('_053_shared052_actual',rp);Q=importlib.util.module_from_spec(sp);sp.loader.exec_module(Q)
 # Complete all original numerical gates before publishing either source.
 Q.admit(O,pm)
 m['split_qualification_api_ref']=pm['files']['qwen36_deltalog_service/split_qualification.py']
 plugin_path=P/'plugin/SOURCE_MANIFEST.json';write(plugin_path,pm);m['plugin_source']=ref(plugin_path)
 O.model_gate(m)
 for r in[*m['files'].values(),*m['dependencies'],*O.transitive_refs(m),*F.refs(O,m)]:O.obj_file(r)
 O.need('torch'not in sys.modules and'torch_npu'not in sys.modules,'host lightweight receipt only')
 write(P/'SOURCE_MANIFEST.json',m);print(json.dumps(dict(source=ref(P/'SOURCE_MANIFEST.json'),model_ready=False,NPU=False)));return 0
if __name__=='__main__':raise SystemExit(main())
