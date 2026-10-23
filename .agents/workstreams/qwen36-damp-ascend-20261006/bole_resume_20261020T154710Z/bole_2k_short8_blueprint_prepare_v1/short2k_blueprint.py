"""Whole BOLE2k short8 SOURCE blueprint: memory only, no approval/bind/device."""
import ast,copy,hashlib,json,sys,types
from pathlib import Path
from contextlib import contextmanager

WORK=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
PREP=WORK/'bole_2k_short8_blueprint_prepare_v1'
PINNED=json.loads("{\"fastpath_numeric_bridge_prepare_v1/qualification_short_prepare.py\":{\"path\":\"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_short_prepare.py\",\"bytes\":16410,\"sha256\":\"940f26bd449f6b0577b0d590303bb68aa0f99f73f8051cc165ba4e09a955db0b\"},\"fastpath_numeric_bridge_prepare_v1/qualification_parent_renderer.py\":{\"path\":\"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_parent_renderer.py\",\"bytes\":2751,\"sha256\":\"1db3e787bd7b9a3f3b6b532fb59e9410902c70c2f1f31d5216e4e9d965bdadae\"},\"fastpath_numeric_bridge_prepare_v1/qualification_tap_delta.py\":{\"path\":\"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_numeric_bridge_prepare_v1/qualification_tap_delta.py\",\"bytes\":2577,\"sha256\":\"349bd1da965eca33df950f6817d88d9e9a3759771ce589f9b901c62302fe27da\"},\"fastpath_clock_seam_prepare_v1/qualification_clock_delta.py\":{\"path\":\"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/fastpath_clock_seam_prepare_v1/qualification_clock_delta.py\",\"bytes\":3092,\"sha256\":\"d9393f9d446b86537aa43c2bf40023b5bdf347c3c99cfce56010a1563433212a\"},\"representative_2k_prepare_v1/render_input_stage.py\":{\"path\":\"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/representative_2k_prepare_v1/render_input_stage.py\",\"bytes\":9983,\"sha256\":\"6cef5e1cc27254add7877d2a97c49e77ea03b966fd6197686cac89dc62ebcabd\"},\"bole_2k_composition_prepare_v1/compose_components.py\":{\"path\":\"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_2k_composition_prepare_v1/compose_components.py\",\"bytes\":10060,\"sha256\":\"4d379674e08a85a91799b95eedc01cfa3942e4e605c5e793fdf6c85590ea9c07\"},\"state_capture_codec_prepare_v1/render_state_codec.py\":{\"path\":\"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/state_capture_codec_prepare_v1/render_state_codec.py\",\"bytes\":5745,\"sha256\":\"bc1fa64b1c792496a140f8a2e3ac9f139784cc288b87200db6f2881aeb20c7fa\"},\"state_capture_codec_prepare_v1/state_capture_codec.py\":{\"path\":\"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/state_capture_codec_prepare_v1/state_capture_codec.py\",\"bytes\":15394,\"sha256\":\"b7bc24128b2ba3561a03a7f5cf5694258ab77c6d4d09b02f9b07eabd9a349e86\"}}")
INPUTS={
 'service_client.py':(4,3080,'8ac77e09701558ec77928a2c42bdace68bbe8881fb6b4a271409d7b9e4e0481f'),
 'input_identity.py':(6,3407,'c966413cb66589aa9b8f17a3a35c35657d6fee7a3ddabae2e755430f2ddfa8ea'),
 'bole_performance_profile.py':(3,4979,'f1ffb4485d8963c06eab882f6c2d8b5700de74025b9663cc705e5df5c88c67f8'),
 'performance_service_client.py':(3,7568,'f7222e39db9691c4d578cdd186393e34ed551a49a10da78e2b498b028a51c5cc'),
 'performance_host.py':(1,6748,'e84f28128852599005fb192eaf3409e7e8d51796c3e1759f31f3ea3f4909ea98'),
 'short_state_digest.py':(3,11410,'21d95e3cec1b90260229a4fa156981e48bbdaa9a7d466a230c63fbf4d9099ec8'),
 'compare_state_digest.py':(3,8418,'a7bdff799d6bc214b69e2da69d3bb8d78ee19dd73c30ef48a22317b27064c826'),
 'validated_performance_policy.py':(2,3644,'c68aa6d14ae8dee329b88ed37f0e57025789ae1cbc9eea2d73e0afb86cdd5112')}

def need(v,s):
 if not v:raise ValueError(s)
def ref(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 p=Path(r['path']);need(p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary exact blueprint source')
 b=p.read_bytes();need(ref(p,b)==r,'independent whole preparation pin '+str(p));return b
def once(t,a,b):
 need(t.count(a)==1,'one whole2k source seam '+a[:100]);return t.replace(a,b,1)
def namespace(path,raw,name):
 ns=dict(__file__=str(path),__name__=name);exec(compile(raw,str(path),'exec'),ns);return ns
@contextmanager
def isolated():
 saved=dict(sys.modules);path=list(sys.path)
 try:yield
 finally:sys.modules.clear();sys.modules.update(saved);sys.path[:]=path

def setup():
 # Complete independent pins BEFORE first renderer byte, never current arbitrary files.
 texts={n:checked(r)for n,r in PINNED.items()}
 core=namespace(PINNED['bole_2k_composition_prepare_v1/compose_components.py']['path'],
  texts['bole_2k_composition_prepare_v1/compose_components.py'],'_whole2k_utils')
 dep=dict(PINNED)
 for row in core['RENDERERS'][1:-1]:
  _,relative,size,digest=row;p=WORK/relative;dep[relative]=dict(path=str(p),bytes=size,sha256=digest)
 for relative,size,digest in core['HELPERS']:
  p=WORK/relative;dep[relative]=dict(path=str(p),bytes=size,sha256=digest)
 allraw={n:checked(r)for n,r in dep.items()}
 for name in('qualification_parent_renderer','qualification_tap_delta','qualification_short_prepare'):
  relative='fastpath_numeric_bridge_prepare_v1/'+name+'.py';p=WORK/relative
  module=types.ModuleType(name);module.__file__=str(p);sys.modules[name]=module
  exec(compile(allraw[relative],str(p),'exec'),module.__dict__)
 inp=namespace(WORK/'representative_2k_prepare_v1/render_input_stage.py',texts['representative_2k_prepare_v1/render_input_stage.py'],'_whole2k_input')
 clock=namespace(WORK/'fastpath_clock_seam_prepare_v1/qualification_clock_delta.py',texts['fastpath_clock_seam_prepare_v1/qualification_clock_delta.py'],'_whole2k_clock')
 return sys.modules['qualification_short_prepare'],core,inp,clock,dep,allraw

def rebase(m,files):
 old={r['path']:(n,r)for n,r in m['files'].items()}
 new={n:ref(Path(m['root'])/n,b)for n,b in files.items()}
 def walk(x):
  if type(x)is dict:
   if set(x)=={'path','bytes','sha256'}and x['path']in old:
    name,r=old[x['path']];need(x==r,'exact complete old source Ref');return dict(new[name])
   return {k:walk(v)for k,v in x.items()}
  if type(x)is list:return [walk(v)for v in x]
  return x
 m=walk(m);m['files']=new;return m

def render(*,base_root=None,permit_materialized=True,parent_pair_preparation_root=None,
 historical_short_source_ref=None,authority_ref=None,parent_preparation_readset=None):
 with isolated():
  Q,core,I,CLOCK,dep,raws=setup()
  base=PREP if base_root is None else Path(base_root)
  parent=Q.render(base_root=base,permit_materialized=permit_materialized,
   parent_pair_preparation_root=parent_pair_preparation_root,
   historical_short_source_ref=historical_short_source_ref,authority_ref=authority_ref,
   parent_preparation_readset=parent_preparation_readset)
  files=dict(parent['files']);stages=[]
  def save(name,before,after,mode='whole_exact_delta',ns=None,bundle=None):
   stages.append(dict(name=name,before=before,after=after,mode=mode,ns=ns,bundle=bundle))
  before=files;files=dict(files)
  for name,(count,size,digest)in INPUTS.items():
   need(len(files[name])==size and hashlib.sha256(files[name]).hexdigest()==digest,'exact original Q.short8 input source '+name)
   files[name]=I['literal_delta'](files[name],{131:2048},expected_count=count)[0]
  files['service_client.py']=once(files['service_client.py'].decode(),"'Explain how trees grow. '*256","'Explain how trees grow. '*1024").encode()
  files['input_identity.py']=once(files['input_identity.py'].decode(),'exact actual131-token prompt, not string length','exact actual2048-token prompt, not string length').encode()
  files['short_state_digest.py']=once(files['short_state_digest.py'].decode(),'actual 131 prefill token IDs','actual 2048 prefill token IDs').encode()
  files['bole_performance_profile.py']=once(files['bole_performance_profile.py'].decode(),'only reviewed C1/131/1024, two-generation scope','only declared C1/2048/8 numerical collection, two-generation scope').encode()
  save('actual-short8-input-identity-profile-client-state',before,files)
  before=files;files=CLOCK['apply'](files);save('original-public-clock-seam',before,files)
  for name,relative,_,_ in core['RENDERERS'][1:-1]:
   ns=namespace(WORK/relative,raws[relative],'_whole2k_'+name);before=files
   bundle=ns['adapt'](files);files=bundle['files'];save(name,before,files,'actual_inverse',ns,bundle)
  relative='state_capture_codec_prepare_v1/render_state_codec.py'
  ns=namespace(WORK/relative,raws[relative],'_whole2k_b53_codec');before=files
  out,ledger=ns['adapt']({n:b.decode()for n,b in files.items()if n.endswith('.py')})
  files={n:b for n,b in files.items()if not n.endswith('.py')};files.update({n:s.encode()for n,s in out.items()})
  save('b53-statecodec',before,files,'actual_codec_undo',ns,ledger)
  before=files;files=dict(files)
  files['qualification_clock_delta.py']=raws['fastpath_clock_seam_prepare_v1/qualification_clock_delta.py']
  selfraw=Path(PREP/'short2k_blueprint.py').read_bytes()
  files['short2k_blueprint.py']=selfraw
  contract=files['contract090.py']
  need(contract.count(b'm[\'profile\']==dict(input_tokens=131,tree_nodes=3,')==1,'exact original whole preregistered diagnostic profile input')
  files['contract090.py']=contract.replace(b'm[\'profile\']==dict(input_tokens=131,tree_nodes=3,',b'm[\'profile\']==dict(input_tokens=2048,tree_nodes=3,',1)
  # Qualifier-only collection scope, never a formal performance or numerical PASS.
  val=files['qualification_source_validate.py'].decode()
  count=sum(isinstance(n,ast.Constant)and type(n.value)is int and n.value==131 for n in ast.walk(ast.parse(val)))
  need(count==3,'reviewed three short8 validator input-domain literals')
  val=I['literal_delta'](val.encode(),{131:2048},expected_count=3)[0].decode()
  val=once(val,"review.get('historical_short_source')==m['qualification_historical_short_source'],",
   "review.get('historical_short_source')==m['qualification_historical_short_source']and\n         review.get('short2k_helper_refs')==m['short2k_helper_refs'],")
  val=once(val,'    import qualification_short_prepare as Q',
   "    for helper_ref in m['short2k_helper_refs'].values():read_ref(helper_ref)\n    read_ref(m['files']['short2k_blueprint.py'])\n    import short2k_blueprint as BP\n    need(C.ref(BP.__file__)==m['files']['short2k_blueprint.py'],'actual source-owned whole2k reconstruction helper')\n    import qualification_short_prepare as Q")
  val=once(val,'    expected=Q.render(','    expected=BP.render(')
  val=once(val,'    Q.inverse(expected)','    BP.inverse(expected)')
  files['qualification_source_validate.py']=val.encode()
  text=files['host_service.py'].decode()
  text=once(text,"'BOLE_OBSERVATION_ONLY_OFF=1']",
   "'BOLE_OBSERVATION_ONLY_OFF=1','--env','BOLE_NATIVE_2K_GEOMETRY_ENABLE=1','--env','BOLE_STATE_CAPTURE_CODEC_ENABLE=1']")
  files['host_service.py']=text.encode()
  save('whole2k-source-review-reconstruction-gate',before,files)
  m=rebase(copy.deepcopy(parent['manifest']),files)
  for name in('performance_profile',):m[name]['scope']['input_tokens']=2048
  for name in('fastpath_numeric_qualification','short_state_digest_profile','profile','performance_client_contract'):m[name]['input_tokens']=2048
  m['service_experiment']['prefix']=2048
  codec=namespace(WORK/'state_capture_codec_prepare_v1/state_capture_codec.py',
    raws['state_capture_codec_prepare_v1/state_capture_codec.py'],'_whole2k_codec_contract')
  m['state_capture_codec']=copy.deepcopy(codec['CONTRACT'])
  m['short2k_helper_refs']=copy.deepcopy(dep)
  m['short2k_helper_refs']['short2k_blueprint.py']=ref(PREP/'short2k_blueprint.py',selfraw)
  m['short2k_blueprint']=dict(schema='bole.whole2k-short8-blueprint/v1',input_tokens=2048,output_tokens=8,
   synthetic_screening_only=True,no_general_gain_claim=True,actual_NPU_qualified=False,
   runtime_joint_fit=False,actual_prefill_geometry=False,sameimage_current_cases_executed=False)
  # Explicit dependency closure (not recipe-PASS) is covered by the MAIN review above.
  paths={r['path']:r for r in m['dependencies']}
  for r in m['short2k_helper_refs'].values():
   need(r['path']not in paths or paths[r['path']]==r,'unambiguous independent helper dependency')
   paths[r['path']]=r
  m['dependencies']=list(paths.values())
  for n,b in files.items():
   if n.endswith('.py'):compile(b,n,'exec')
  return dict(manifest=m,files=files,parent=parent,stages=stages,source_bound=False,whole2k_ready=False,
   numerical_qualified=False,actual_bound_validated=False,NPU=False)

def inverse(bundle):
 with isolated():
  Q,core,*_=setup()
  current=bundle['files']
  for stage in reversed(bundle['stages']):current=core['undo_stage'](stage,current)
  need(current==bundle['parent']['files'],'complete Q.short8 bytes restored')
  Q.inverse(bundle['parent'])
  return current

if __name__=='__main__':
 if not sys.argv[1:]:print('{"enabled":false,"whole2k_ready":false,"NPU":false}')
 else:
  need(sys.argv[1:]==['--check'],'pure memory --check only')
  b=render();inverse(b)
  print(json.dumps(dict(files=len(b['files']),py=sum(n.endswith('.py')for n in b['files']),
   stages=[s['name']for s in b['stages']],whole_inverse=True,source_bound=False,
   whole2k_ready=False,numerical_qualified=False,NPU=False)))
