"""Default-OFF pure pair-consumer repair. Never admits a model or launches HTTP."""
import ast,copy,hashlib,json
from pathlib import Path
from fractions import Fraction
W=Path(__file__).resolve().parent.parent
READER=W/'fixed1024_sse_timing_client_v1/independent_reader.py'
READER_SHA='9ffba3df8c2417e2249f368ebe7573f093e6a45f62e5bcefc1186259f08f273c'
PROFILE=W/'bole_performance_profile_prepare_20261021/successor_layer/bound-bole-v2-r1/bole_performance_profile.py'
PROFILE_SHA='e046c1c48b02b8c8a701f15dc90c5bf162db652921eeeae1aa2f7558c451fdbd'
def need(v,m):
 if not v:raise ValueError(m)
def functions(path,sha,names,env):
 raw=path.read_bytes();need(hashlib.sha256(raw).hexdigest()==sha,'exact unchanged donor source')
 tree=ast.parse(raw);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names]
 need(len(nodes)==len(names),'exact actual function closure')
 return tree,nodes
def checked_math(pairs,*,obj,source_set_ref=None):
 """obj must be the source-bound whole-Ref reader. Qualification stays external."""
 prepared=copy.deepcopy(pairs);need(type(prepared)is list and len(prepared)==3,'exactly3 complete pairs')
 source_set=None
 if source_set_ref is not None:
  import three_trial_sources as TRIALS
  source_set=TRIALS.validate(source_set_ref)
  common_source_set=TRIALS.refs(source_set)
 pair_refs=None
 for trial_index,pair in enumerate(prepared):
  for mode,arm in [('OFF','native_ar'),('ON','bole')]:
   row=pair[mode];ident=row['identity'];m=obj(ident['source_ref']);server=obj(ident['server_command_ref'])
   need(ident['execution_arm']==m['performance_arm']==arm,'baseline must be true native AR, never observerOFF')
   need(m['common_collective_configuration']==dict(schema='bole.common-collective-configuration/v1',
    hccl_deterministic='true',applies_to=['native_ar','bole']),'same actual source-bound common HCCL')
   need(m['common']==dict(HF32=False,async_scheduling=False,eager=True,mamba_cache_mode='none',prefix_cache=False,profiling=False),'same precision and no profiling')
   need(server['source']==ident['source_ref'] and server['performance_arm']==arm
    and server['native_MTP']is (arm=='bole') and server['num_speculative_tokens']==(8 if arm=='bole'else 0),'real server entry arm and MTP distinction')
   argv=server['argv']
   need(argv.count('--tensor-parallel-size')==1 and argv[argv.index('--tensor-parallel-size')+1]=='4'
    and argv.count('--max-num-seqs')==1 and argv[argv.index('--max-num-seqs')+1]=='1'
    and not any('profiler' in x.lower() for x in argv),'actual TP4/C1 argv with profiling absent')
   need(m['performance_profile']['scope']['output_tokens']==m['performance_client_contract']['output_tokens']==1024
    and m['performance_client_contract']['input_tokens']==131 and m['performance_client_contract']['concurrency']==1,'no short8 promotion')
  a=pair['OFF']['identity'];b=pair['ON']['identity']
  refs=dict(native_ar=a['source_ref'],bole=b['source_ref'])
  if source_set is None:
   need(refs['native_ar']!=refs['bole'] and (pair_refs is None or refs==pair_refs),'distinct immutable arm sources, stable across all3 pairs')
  else:
   need(pair['pair_index']==trial_index and refs==source_set['trials'][trial_index]['arms'],'each actual row exactly joins independently reconstructed own trial source; no foreign/repeated trial')
   refs=common_source_set
  pair_refs=refs
  for key in ('checkpoint_config_ref','checkpoint_index_ref','installed_sources','cache_memory_config'):
   need(obj(a['source_ref'])[key]==obj(b['source_ref'])[key],'same checkpoint/stack/cache '+key)
  env={'require':need,'json':json,'NATIVE_SPEC':dict(method='mtp',num_speculative_tokens=8)}
  _,nodes=functions(PROFILE,PROFILE_SHA,{'paired_argv'},env);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(PROFILE),'exec'),env)
  need(env['paired_argv'](obj(b['server_command_ref'])['argv'])['native_ar']==obj(a['server_command_ref'])['argv'],'same actual argv except exact MTP removal; TP4/checkpoint preserved')
  for ident in(a,b):ident['pair_source_refs']=refs
 env={'need':need,'Fraction':Fraction,'json':json,'MODEL':'qwen36-mxr-eager'}
 tree,nodes=functions(READER,READER_SHA,{'expected_request','_after_full_qualification_math'},env)
 # Match the exact seed=0 body already used by both actual rendered arms.
 expected=next(n for n in nodes if n.name=='expected_request')
 text=ast.get_source_segment(READER.read_text(),expected)
 need(text.count('temperature=0,top_p=1,n=1,stream=True')==1,'one original request body seed seam')
 expected=ast.parse(text.replace('temperature=0,top_p=1,n=1,stream=True','temperature=0,top_p=1,seed=0,n=1,stream=True',1)).body[0]
 nodes=[expected if n.name=='expected_request'else n for n in nodes]
 # Sole existing arithmetic correction: two real arms cannot have one source_ref.
 node=next(n for n in nodes if n.name=='_after_full_qualification_math')
 text=ast.get_source_segment(READER.read_text(),node)
 need(text.count("'source_ref'")==1,'exact donor common-source predicate')
 node=ast.parse(text.replace("'source_ref'","'pair_source_refs'")).body[0]
 nodes=[node if n.name=='_after_full_qualification_math'else n for n in nodes]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(READER),'exec'),env)
 result=env['_after_full_qualification_math'](prepared)
 for out,pair in zip(result['pairs'],prepared):
  out['unit']='nanoseconds; throughput tokens/second'
  out['rates']={mode:dict(output_tokens=1024,throughput_tokens_per_second=1024*10**9/pair[mode]['observation']['T_total_ns'],
    TTFT_ms=pair[mode]['observation']['TTFT_ns']/10**6,
    TPOT_ms=pair[mode]['observation']['TPOT_numerator_ns']/1023/10**6)for mode in('OFF','ON')}
 result.update(source_pair=pair_refs,model_qualification=False,formal_qualification=False,
  raw_SSE_replay_required=True,owner_admission_required=True)
 return result
if __name__=='__main__':print('{"enabled":false,"formal_qualification":false,"HTTP":false,"NPU":false}')
