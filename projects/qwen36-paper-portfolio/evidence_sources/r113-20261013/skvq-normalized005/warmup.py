"""Only native FULL-target dummy warmup may use original eager writer."""
import ast,copy,inspect,types
from pathlib import Path
RUNNER='94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968'
GPU='6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666'
ACTIVE=None
def need(v,m):
 if not v:raise ValueError(m)
def validate(v):
 need(v['phase']=='capture' and v['capturing']is False and v['mode']=='NONE','only noncapturing native capture warmup')
 for key in ('uniform_decode','force_attention','skip_eplb'):
  need(v['dummy'][key]is True,'true native dummy '+key)
 for key in ('is_profile','is_graph_capturing','create_mixed_batch','profile_cpp','with_prefill'):
  need(v['dummy'][key]is False,'false native dummy '+key)
 b=v['batch'];need(type(b)is int and 1<=b<=16,'native unpadded batch1..16')
 need(all(type(v['dummy'][k])is int and v['dummy'][k]==b for k in ('num_tokens','num_tokens_unpadded','num_tokens_padded','num_reqs','num_reqs_padded')),'native actual token/request extents equal actual QKV, no padding')
 need(v['dummy']['max_query_len']==1 and v['dummy']['max_query_len_type']=='int','native one-token query')
 need(v['scheduled_dtype']=='int32' and v['scheduled_shape']==[b] and v['uniform_decode_query_len']==1,'actual CPU int32 scheduled and native uniform query length1')
 need(v['context_descriptor_is_native']is True and v['context_mode_is_native']is True,'same actual native context descriptor/mode objects')
 need(v['scheduled']==[1]*b and v['query_starts']==list(range(b+1)),'actual CPU scheduled/query starts uniform1 no pad')
 need(v['target']['num_tokens']==v['target']['num_reqs']==b and v['target']['uniform']is True and v['target']['mode']=='FULL','original source-bound FULL target descriptor')
 need(v['target']['num_active_loras']==0 and v['target']['has_lora']is False,'original nonLoRA target')
 need(v['dummy']['frame_qualified']is True and v['target']['frame_qualified']is True,'actual original code frames qualified')
 need(v['descriptor']['num_tokens']['value']==b and v['descriptor']['num_tokens']['type']=='int','actual context token descriptor; never changed')
 return b
def fields(d):
 return {k:dict(type=type(getattr(d,k)).__name__,value=getattr(d,k))for k in ('num_tokens','num_reqs','uniform','has_lora','num_active_loras')}
def native_frame(runner,name,sha):
 from formal_contract import pin_function
 fn=inspect.unwrap(getattr(getattr(runner,name),'__func__',getattr(runner,name)));r=pin_function(fn,sha)
 frame=inspect.currentframe().f_back
 while frame is not None:
  if frame.f_code is fn.__code__:
   need(frame.f_locals.get('self')is runner,'actual original runner receiver');return frame,r
  frame=frame.f_back
 raise ValueError('no actual original native '+name+' frame')
def binding(adapter,worker,state,layer,q,k,v,view,context):
 need(ACTIVE is not None,'warmup adapter default OFF')
 resources=state['writers'][layer]
 if context.capturing is True:
  return resources.bind(k,v,view['controls'],view['row_epochs'],view['slot_epochs'],view['error'],context=context)
 # Record genuine native metadata BEFORE any acceptance assertion.
 dummy,dr=native_frame(worker.model_runner,'_dummy_run',RUNNER)
 warm,wr=native_frame(worker.model_runner,'_warmup_and_capture',GPU)
 d=dummy.f_locals;w=warm.f_locals;target=w['desc'];b=q.shape[0]
 scalars=('uniform_decode','force_attention','skip_eplb','is_profile','is_graph_capturing','create_mixed_batch','profile_cpp','with_prefill','num_tokens','num_tokens_unpadded','num_tokens_padded','num_reqs','num_reqs_padded','max_query_len')
 snapshot=dict(phase=state['boundary'].phase,capturing=context.capturing,mode=context.cudagraph_runtime_mode.name,
  batch=b,descriptor=fields(context.batch_descriptor),
  dummy={key:d[key]for key in scalars},
  target=dict(num_tokens=target.num_tokens,num_reqs=target.num_reqs,uniform=target.uniform,has_lora=target.has_lora,num_active_loras=target.num_active_loras,mode=w['cudagraph_runtime_mode'].name,frame_qualified=True),
  context_descriptor_is_native=context.batch_descriptor is d['batch_desc'],context_mode_is_native=context.cudagraph_runtime_mode is d['cudagraph_runtime_mode'],
  uniform_decode_query_len=worker.model_runner.uniform_decode_query_len,
  scheduled_dtype=str(d['num_scheduled_tokens'].dtype),scheduled_shape=list(d['num_scheduled_tokens'].shape),scheduled=d['num_scheduled_tokens'].tolist(),
  query_starts=worker.model_runner.query_start_loc.np[:b+1].tolist())
 snapshot['dummy'].update(frame_qualified=True,max_query_len_type=type(d['max_query_len']).__name__)
 from formal_attention import storage_row
 snapshot.update(schema='skvq.actual-native-FULL-target-warmup/v1',rank=adapter.rank,layer=layer,source_ref=adapter.source,
  adapter_source_ref=ACTIVE['own'],warmup_source_ref=ACTIVE['leaf'],native_dummy_ref=dr,native_warmup_ref=wr,
  actual_QKV={n:storage_row(x)for n,x in (('q',q),('k',k),('v',v))},
  native_ready=False,math_verified=False,performance_ready=False)
 adapter.publish('WARMUP_BEFORE_BIND',snapshot)
 validate(snapshot)
 need(q.shape[0]==k.shape[0]==v.shape[0]==b,'actual warmup QKV rows')
 return resources.bind_eager(k,v,view['controls'],view['row_epochs'],view['slot_epochs'],view['error'],
  context=context,actual_rows=list(range(b)),native_query_tokens=b)
def install(B,own,leaf):
 global ACTIVE
 need(ACTIVE is None,'one cold warmup adapter')
 import formal_attention as A
 from formal_contract import pin_function
 row=B.role('formal_attention.py');pin_function(A.Integration.compute,row['sha256'])
 original=ast.parse(B.checked(row),row['path'])
 cls=next(n for n in original.body if isinstance(n,ast.ClassDef)and n.name=='Integration')
 old=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='compute');fn=copy.deepcopy(old)
 capture=next(n for n in fn.body if isinstance(n,ast.If)and ast.unparse(n.test)=="boundary.phase == 'capture'")
 assignment=next(n for n in capture.body if isinstance(n,ast.Assign)and ast.unparse(n.targets[0])=='writer')
 expected="state['writers'][layer].bind(k, v, view['controls'], view['row_epochs'], view['slot_epochs'], view['error'], context=ctx)"
 need(ast.unparse(assignment.value)==expected,'only exact original capture bind site')
 assignment.value=ast.parse('_skvq_warm_binding(self,worker,state,layer,q,k,v,view,ctx)',mode='eval').body
 inverse=copy.deepcopy(fn)
 invcap=next(n for n in inverse.body if isinstance(n,ast.If)and ast.unparse(n.test)=="boundary.phase == 'capture'")
 invassign=next(n for n in invcap.body if isinstance(n,ast.Assign)and ast.unparse(n.targets[0])=='writer')
 invassign.value=ast.parse(expected,mode='eval').body
 need(ast.dump(inverse,include_attributes=False)==ast.dump(old,include_attributes=False),'complete compute inverse AST; original math/guards/reader/FULL untouched')
 ns=dict(A.__dict__,_skvq_warm_binding=binding)
 exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),leaf['path'],'exec',dont_inherit=True),ns)
 A.Integration.compute=ns['compute'];ACTIVE=dict(own=own,leaf=leaf)
 return dict(original_compute_ref=row,warmup_source_ref=leaf,math_changed=False,FULL_bind_changed=False)
