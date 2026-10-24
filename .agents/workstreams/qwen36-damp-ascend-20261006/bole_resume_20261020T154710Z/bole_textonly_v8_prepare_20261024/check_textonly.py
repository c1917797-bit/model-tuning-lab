"""Narrow common-argv and parsed-contract controls, no image execution."""
import ast,hashlib,json,os,resource,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
 if sys.argv[1:]!=['--check']:raise ValueError('default OFF; explicit --check only')
 assert 144 in os.sched_getaffinity(0);os.sched_setaffinity(0,{144});resource.setrlimit(resource.RLIMIT_AS,(512<<20,512<<20))
 sys.path.insert(0,str(HERE));import adapt_textonly as A;import text_only_profile as T
 root=HERE.parent/'bole_guard_observation_prepare_v7_20261024/prepared-source-short8-v7'
 m=json.loads((root/'SOURCE_BOUND.json').read_bytes());files={}
 for n in('bole_performance_profile.py','preflight114.py'):
  raw=(root/n).read_bytes();r=m['files'][n]
  assert len(raw)==r['bytes']and hashlib.sha256(raw).hexdigest()==r['sha256'];files[n]=raw
 out,d=A.adapt(files);assert A.inverse(out,d)==files
 P=types.ModuleType('_actual_text_only_profile');exec(compile(out['bole_performance_profile.py'],str(root/'bole_performance_profile.py'),'exec'),P.__dict__)
 specs=[v for v in vars(P).values()if type(v)is dict and v.get('method')=='mtp']
 assert len(specs)==1,'one actual inherited speculative configuration'
 profile_ast=ast.parse(out['bole_performance_profile.py'])
 paired_fn=next(n for n in profile_ast.body if isinstance(n,ast.FunctionDef)and n.name=='paired_argv')
 required_flags=sorted({n.left.value for n in ast.walk(paired_fn)if isinstance(n,ast.Compare)and len(n.ops)==1 and isinstance(n.ops[0],ast.In)and isinstance(n.left,ast.Constant)and type(n.left.value)is str and n.left.value.startswith('--')and isinstance(n.comparators[0],ast.Name)and n.comparators[0].id=='candidate_argv'})
 pairs=P.paired_argv(['python','-m','vllm.entrypoints.openai.api_server',*required_flags,'--speculative-config',json.dumps(specs[0])])
 for arm,args in pairs.items():
  assert args.count(T.FLAG)==1 and json.loads(args[args.index(T.FLAG)+1])==T.LIMITS
  print('actual_paired_argv',arm,T.LIMITS)
 for bad in([T.FLAG,'{}'],[T.FLAG+'={}']):
  try:T.argv(bad)
  except ValueError:pass
  else:raise AssertionError('duplicate quota accepted')
 for bad in({}, {'image':0,'video':1},{'image':False,'video':0}):
  try:T.require_parsed(types.SimpleNamespace(limit_mm_per_prompt=bad),types.SimpleNamespace(limit_mm_per_prompt=bad))
  except ValueError:pass
  else:raise AssertionError('incorrect parsed quota accepted')
 a=ast.parse(out['preflight114.py']);calls=[n for n in ast.walk(a)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='require_parsed']
 assert len(calls)==1 and [ast.unparse(n)for n in calls[0].args]==['args','engine']
 raw=HERE/'image_multimodal_registry.py';a=ast.parse(raw.read_bytes())
 f=next(n for n in ast.walk(a)if isinstance(n,ast.FunctionDef)and n.name=='supports_multimodal_inputs')
 assert any(isinstance(n,ast.If)and 'get_limit_per_prompt'in ast.unparse(n.test)and any(isinstance(x,ast.Return)and isinstance(x.value,ast.Constant)and x.value.value is False for x in ast.walk(n))for n in ast.walk(f))
 print('inverse/common_argv/duplicates/strict_parsed_negative/actual_preflight_seam/actual_registry_zero_branch PASS')
 print('actual_image_parser_pending=true,NPU=false')
if __name__=='__main__':main()
