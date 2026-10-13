"""Real cold source audit; synthetic policy tests are not hardware ABI."""
import argparse,ast,json,os,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bridge as C
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-sha');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False)));return
 start=time.monotonic();C.need(a.source_sha and a.output and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='','explicit actual Devices[] source-only audit')
 C.boot(a.source_sha);v,t=C.views();rows=[]
 def passed(name,ok):C.need(ok,name);rows.append(dict(name=name,passed=True))
 passed('shared_policy_and_runner_warmup1',C.COMMON.COMPILATION['cudagraph_num_of_warmups']==1)
 passed('unchanged_FULL_all16_native10_aux2',C.COMMON.COMPILATION['cudagraph_mode']=='FULL_DECODE_ONLY'and C.COMMON.BATCHES==tuple(range(1,17))and C.COMMON.COMMON['kv_cache_memory_bytes']==10*2**30 and C.COMMON.AUX_CEILING==2*2**30)
 passed('false_effective_leaves_preserved',C.COMMON.EFFECTIVE_ADDITIONAL['ascend_compilation_config']['enable_static_kernel']is False and C.COMMON.EFFECTIVE_ADDITIONAL['ascend_compilation_config']['fuse_allreduce_rms']is False)
 v['formal_guest'].S.source(C.B.ENGINE['sha256'])
 passed('actual_source_retains_spawn_root',sys.path[0]==str(C.ROOT))
 passed('spawn_root_and_single_resolver',v['formal_guest'].HERE==C.ROOT and v['formal_guest'].load_common()is C.COMMON and v['formal_runtime'].load_common()is C.COMMON)
 old=dict(C.COMMON.COMMON);old['compilation_config']=dict(old['compilation_config'],cudagraph_num_of_warmups=2)
 try:C.COMMON.validate(old,'candidate')
 except ValueError:passed('old_warmup2_policy_rejected',True)
 else:raise ValueError('old warmup accepted')
 for role in ('host','guest','independent','whole'):
  cp=subprocess.run([sys.executable,'-I','-B',str(C.ROOT/(role+'.py'))],capture_output=True,text=True,timeout=5)
  passed('fresh_defaultOFF_'+role,cp.returncode==0 and json.loads(cp.stdout)==dict(enabled=False,NPU=False))
 env=dict(os.environ);env.pop(C.ENV,None)
 cp=subprocess.run([sys.executable,'-I','-B','-c',"import sys;sys.path.insert(0,"+repr(str(C.ROOT))+");import skvq_normalized_worker"],env=env,capture_output=True,text=True,timeout=5)
 passed('fresh_worker_defaultOFF_before_backend',cp.returncode!=0 and 'normalized worker default OFF'in cp.stderr)
 env[C.ENV]=C.OWN['sha256'];env.pop('MAIN_SKVQ_FORMAL_PROVIDER_ENABLE',None)
 code="import sys,importlib,json;sys.path.insert(0,"+repr(str(C.ROOT))+")\ntry:importlib.import_module('skvq_normalized_worker')\nexcept ValueError as e:\n import bridge as B\n assert str(e)=='formal provider worker is default OFF'\n tb=e.__traceback__\n frames=[]\n while tb is not None:frames.append(tb.tb_frame);tb=tb.tb_next\n r=B.B.role('formal_worker.py');f=[x for x in frames if x.f_code.co_filename==r['path']][-1]\n assert f.f_globals['__name__']=='formal_worker'and f.f_globals['__file__']==r['path']\n assert f.f_code.co_filename==r['path']and 'formal_worker'not in sys.modules\n assert not any(n in sys.modules for n in ('torch','torch_npu','triton','vllm'))\n print(json.dumps(dict(actual_registered_original_module_before_defaultOFF=True)))\nelse:raise AssertionError('original defaultOFF absent')"
 cp=subprocess.run([sys.executable,'-I','-B','-c',code],env=env,capture_output=True,text=True,timeout=10)
 passed('actual_importlib_original_module_origin_then_defaultOFF',cp.returncode==0 and json.loads(cp.stdout)['actual_registered_original_module_before_defaultOFF']is True)
 code="import sys,types;sys.path.insert(0,"+repr(str(C.ROOT))+");import bridge as B;B.boot("+repr(C.OWN['sha256'])+");r=B.B.role('formal_worker.py');m=types.ModuleType('formal_worker');m.__file__=str(B.ROOT/'skvq_normalized_worker.py');sys.modules['formal_worker']=m\ntry:B.B.engine.module('formal_worker',r)\nexcept ValueError as e:assert str(e)=='no foreign named source module: formal_worker'\nelse:raise AssertionError('foreign original name accepted')\nassert sys.modules['formal_worker']is m"
 cp=subprocess.run([sys.executable,'-I','-B','-c',code],env=env,capture_output=True,text=True,timeout=10)
 passed('foreign_loaded_original_name_rejected_without_hiding',cp.returncode==0)
 code="import sys,types,importlib;sys.path.insert(0,"+repr(str(C.ROOT))+");import bridge as B;B.boot("+repr(C.OWN['sha256'])+");r=B.B.role('formal_worker.py');m=types.ModuleType('formal_worker');m.__file__=r['path'];sys.modules['formal_worker']=m\ntry:importlib.import_module('skvq_normalized_worker')\nexcept ValueError as e:assert str(e)=='unique bootstrap rejects any preexisting original worker module'\nelse:raise AssertionError('same-file partial worker accepted')\nassert sys.modules['formal_worker']is m and not hasattr(m,'ADAPTER')"
 cp=subprocess.run([sys.executable,'-I','-B','-c',code],env=env,capture_output=True,text=True,timeout=10)
 passed('same_file_partial_module_rejected_without_relabel_or_hiding',cp.returncode==0)
 passed('unique_worker_actual_argv',v['formal_guest'].server_argv(8243,C.COMMON)[v['formal_guest'].server_argv(8243,C.COMMON).index('--worker-cls')+1]=='skvq_normalized_worker.FormalWorker')
 try:C.read(dict(C.CONFIG,sha256='0'*64))
 except ValueError:passed('wrong_actual_config_source_rejected',True)
 else:raise ValueError('wrong config pin accepted')
 import formal_runtime as R,provider as P,formal_contract as FC
 worker_ref=C.B.role('formal_worker.py');tree=ast.parse(C.read(worker_ref),worker_ref['path'])
 node=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='SourceAdapter')
 ns={'__name__':'_source_only_actual_SourceAdapter','create_integration':R.create_integration,'SOURCE':C.B.ENGINE,'MANIFEST':C.B.engine_manifest,'IDENTITY':None,'S':C.B.engine}
 exec(compile(ast.Module(body=[node],type_ignores=[]),worker_ref['path'],'exec',dont_inherit=True),ns)
 P.integration_source(ns['SourceAdapter'](),worker_ref)
 passed('six_original_method_codepins_and_shared_real_resolver',R.load_common()is FC.load_common()is C.COMMON and C.B.engine_manifest['integration_source_ref']==worker_ref)
 receiver=C.read(C.B.role('formal_attention.py')).decode()
 passed('immutable_receiver_original_module_class_guards',all(x in receiver for x in ("sys.modules['formal_worker']","worker.__class__.__module__=='formal_worker'")))
 passed('complete_new_sources_compile',all(compile(C.read(r),r['path'],'exec',dont_inherit=True)for r in C.B.manifest['files']))
 from cpu_safe import device_fds
 passed('actual_no_device_FDs_or_backend',not device_fds()and not any(n in sys.modules for n in ('torch','torch_npu','triton','vllm')))
 passed('warmup_compute_inverse_ast_and_no_math_change',C.B.warmup_install['math_changed']is False and C.B.warmup_install['FULL_bind_changed']is False)
 base=dict(phase='capture',capturing=False,mode='NONE',batch=2,
  descriptor={'num_tokens':dict(value=2,type='int')},
  dummy=dict(uniform_decode=True,force_attention=True,skip_eplb=True,is_profile=False,is_graph_capturing=False,create_mixed_batch=False,profile_cpp=False,with_prefill=False,num_tokens=2,num_tokens_unpadded=2,num_tokens_padded=2,num_reqs=2,num_reqs_padded=2,max_query_len=1,max_query_len_type='int',frame_qualified=True),
  target=dict(num_tokens=2,num_reqs=2,uniform=True,has_lora=False,num_active_loras=0,mode='FULL',frame_qualified=True),
  scheduled=[1,1],query_starts=[0,1,2],scheduled_dtype='int32',scheduled_shape=[2],uniform_decode_query_len=1,context_descriptor_is_native=True,context_mode_is_native=True)
 passed('synthetic_warmup_metadata_only_acceptance',C.B.warmup.validate(base)==2)
 import copy
 variants=[('padded_tokens','dummy','num_tokens_padded',3),('padded_requests','dummy','num_reqs_padded',3),('not_uniform','dummy','uniform_decode',False),('profile','dummy','is_profile',True),('actual_capture','dummy','is_graph_capturing',True),('foreign_frame','dummy','frame_qualified',False),('target_not_full','target','mode','NONE'),('LoRA','target','has_lora',True)]
 for label,group,key,value in variants:
  bad=copy.deepcopy(base);bad[group][key]=value
  try:C.B.warmup.validate(bad)
  except ValueError:passed('synthetic_reject_'+label,True)
  else:raise ValueError('bad warmup accepted '+label)
 for label,key,value in [('mixed_schedule','scheduled',[2,0]),('bad_query_starts','query_starts',[0,2,2]),('wrong_cpu_dtype','scheduled_dtype','int64'),('foreign_context','context_descriptor_is_native',False),('not_capture_phase','phase','real-request-inputs')]:
  bad=copy.deepcopy(base);bad[key]=value
  try:C.B.warmup.validate(bad)
  except ValueError:passed('synthetic_reject_'+label,True)
  else:raise ValueError('bad warmup accepted '+label)
 try:C.B.warmup.native_frame(object(),'__str__',C.B.warmup.RUNNER)
 except ValueError:passed('actual_callable_provenance_reject_before_frame',True)
 else:raise ValueError('foreign native frame accepted')
 value=dict(schema='skvq.normalized-common-source-audit/v1',adapter_source_ref=C.OWN,donor_ref=C.DONOR,configuration_origin_ref=C.CONFIG,tests=rows,trace=t,common=C.COMMON.COMMON,effective_additional_config=C.COMMON.EFFECTIVE_ADDITIONAL,scope='Devices-empty-real-source-graph-and-synthetic-policy-only',native_hal_checked=False,model_loaded=False,full47_ready=False,performance_ready=False,task_ready=False,elapsed_seconds=time.monotonic()-start)
 print('MAIN_SKVQ_NORMALIZED_SOURCE_AUDIT '+json.dumps(C.B.engine.publish(a.output,value)),flush=True)
if __name__=='__main__':main()
