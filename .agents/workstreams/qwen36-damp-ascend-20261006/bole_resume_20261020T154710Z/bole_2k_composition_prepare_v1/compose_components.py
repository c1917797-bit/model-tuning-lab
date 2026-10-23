"""Actual six-component BOLE2k in-memory composition; never a source producer."""
from pathlib import Path
from contextlib import contextmanager
import hashlib,json,subprocess,sys

HERE=Path(__file__).resolve().parent
WS=HERE.parent
ROOT=WS.parents[3]
BASE=WS/'formal_pair_ready_prepare_v1/strict-source-proposal-v3/PREPARED_PAIR.json'
BASE_PIN=(3012587,'9ea9814123901c0ecda21c52ab5e6b7e1cbd4e373fb3373ccbeec8cdaedb7f37')
COMMIT='6f8461ee834089fd57f945097eae22d58ae2b646'
RENDERERS=(
 ('qualification_tap','fastpath_numeric_bridge_prepare_v1/qualification_tap_delta.py',2577,'349bd1da965eca33df950f6817d88d9e9a3759771ce589f9b901c62302fe27da'),
 ('geometry','fa_2k_geometry_prepare_v1/render_geometry.py',10907,'3c7b6059320206757be8fbadcba70f701781579e84e975aa460bf1ffab6e7382'),
 ('snapshot','snapshot_2k_capacity_prepare_v1/render_capacity.py',4765,'1f4e0462a4e1b0fe6af9397e800e750738d88397cda7f02e74846a424be1e3eb'),
 ('native_input','native_2k_service_input_prepare_v1/render_native_input.py',7388,'54395af088510407c8194f612df44e191d30a17c0d81e64592f5e802a8cca3a4'),
 ('numeric2k','numerical_2k_prefix_prepare_v1/render_numeric_2k.py',8010,'573c864501c0fe8dc1bd6213cf37608be68fafcff3d1381a758dd0279d6853cd'),
 ('statecodec','state_capture_codec_prepare_v1/render_state_codec.py',5444,'1b0b923bf117dde24ad62910718a02836ff74fa3c83c16fe4c39a31072a90641'))
HELPERS=(
 ('fastpath_numeric_bridge_prepare_v1/fastpath_numeric_observer.py',8846,'c5943291ed026402f67bbc0f6c515ba506439943c2baf55b9f12153836f6c6b2'),
 ('fastpath_numeric_bridge_prepare_v1/fastpath_numeric_sink.py',5497,'adfd91fd06ca949bdb32dc9617bb60ffc794fd06a7aa50298d02cac1cbd1b62a'),
 ('fastpath_numeric_bridge_prepare_v1/fastpath_numeric_consumer.py',11339,'ed4499e8b64035d4a4280b895d559087c98548b853d4a28eb08be858ef6f2945'),
 ('fastpath_numeric_bridge_prepare_v1/qualification_state_probe.py',4413,'d08ee36da48a4ee91ee3aa3f42fbdf16b3060ac3a0d9dfdfa7c5834316f6250e'),
 ('fa_2k_geometry_prepare_v1/fa_native_geometry.py',13677,'405a1f46c7e2245fe0299581991e1f1d8d1234e94413ba4627f6e666787d24f3'),
 ('numerical_2k_prefix_prepare_v1/numeric_prefix_2k.py',11069,'12933f6510e8a8dc8120f8adea2e8e806ab7e8e7c8a1a9d2fa56f30a7b9c3463'),
 ('state_capture_codec_prepare_v1/state_capture_codec.py',15394,'b7bc24128b2ba3561a03a7f5cf5694258ab77c6d4d09b02f9b07eabd9a349e86'))
PENDING=[
 'whole2k Q.short8 and render160 producer/manifest/command integration',
 'whole2k source-validator and current finite clock/authority plus independent MAIN source review',
 'actual native2k prefill-first geometry/ID evidence and same-image/ABI controls',
 'runtime_joint raw/disk/host/NPU reservation admission before actual allocation',
 'raw_reservation is defined but not connected to real sink',
 'post-6f8461ee CPU raw-release fix is NOT covered by this pinned old-codec composition',
 '2048 input identity/profile/client needs whole-source integration, not this six-component stage',
 'actual2k independent numerical/state NPU gates; nativeAR pairing; diverse accepted workload',
 'formal performance and GSM8K/HumanEval/MMLU smoke/full task accuracy'
]

def need(v,s):
 if not v:raise ValueError(s)

def identity(raw):
 return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def checked(path,pin,*,commit=None):
 path=Path(path)
 need(path.is_file()and not any(p.is_symlink()for p in(path,*path.parents)),'ordinary actual dependency')
 if commit:
  need(commit==COMMIT,'only fixed audited codec commit')
  raw=subprocess.run(['git','show',commit+':'+str(path.relative_to(ROOT))],
      cwd=ROOT,capture_output=True,check=True,timeout=10).stdout
 else:raw=path.read_bytes()
 need((len(raw),hashlib.sha256(raw).hexdigest())==tuple(pin),'complete dependency pin '+str(path))
 return raw

@contextmanager
def private_renderers():
 # No sys.path insertion; dictionary execution has a unique name, no importable alias.
 saved=dict(sys.modules);path=list(sys.path)
 try:yield
 finally:
  sys.modules.clear();sys.modules.update(saved);sys.path[:]=path

def load_renderer(row):
 label,relative,size,digest=row;p=WS/relative
 raw=checked(p,(size,digest),commit=COMMIT if label=='statecodec'else None)
 ns={'__file__':str(p),'__name__':'_bole2k_composition_'+label}
 exec(compile(raw,str(p),'exec'),ns)
 return ns

def compile_all(files):
 count=0
 for n,raw in files.items():
  if n.endswith('.py'):compile(raw,n,'exec');count+=1
 return count

def read_parent():
 m=json.loads(checked(BASE,BASE_PIN));need(m['source_bound']is False and m['authority_ref']is None,
  'actual unbound preparation, not current authority')
 arm=m['arms']['bole']['manifest'];out={}
 for name,r in arm['files'].items():
  need(set(r)=={'path','bytes','sha256'} and type(name)is str,'complete actual file Ref')
  out[name]=checked(r['path'],(r['bytes'],r['sha256']))
 need(len(out)==402 and arm['performance_arm']=='bole','exact complete BOLE prepared parent')
 return out

def undo_stage(stage,current):
 need(current==stage['after'],'whole after-map exact before inverse '+stage['name'])
 mode=stage['mode'];ns=stage.get('ns');bundle=stage.get('bundle')
 if mode=='actual_inverse':back=ns['inverse'](dict(bundle,files=current))
 elif mode=='actual_codec_undo':
  py={n:b.decode()for n,b in current.items()if n.endswith('.py')}
  restored=ns['undo'](py,bundle)
  back={n:b for n,b in current.items()if not n.endswith('.py')}
  back.update({n:s.encode()for n,s in restored.items()})
 else:
  back=dict(current)
  for n in set(current)|set(stage['before']):
   if current.get(n)!=stage['before'].get(n):
    if n in stage['before']:back[n]=stage['before'][n]
    else:back.pop(n)
 need(back==stage['before'],'complete exact inverse '+stage['name'])
 return back

def compose():
 with private_renderers():
  parent=read_parent();files=dict(parent);stages=[]
  compile_all(parent)
  # Validate every helper BEFORE any renderer executes; additions have an explicit inverse.
  helpers={Path(r).name:checked(WS/r,(size,digest))for r,size,digest in HELPERS}
  before=files;files=dict(files)
  for r,_,_ in HELPERS[:4]:
   n=Path(r).name;need(n not in files,'no helper overwrite');files[n]=helpers[n]
  stages.append(dict(name='qualification_dependencies',before=before,after=files,mode='whole_exact_delta'))
  events=[]
  for row in RENDERERS:
   name=row[0];ns=load_renderer(row);before=files
   if name in('qualification_tap','statecodec'):
    py={n:b.decode()for n,b in files.items()if n.endswith('.py')}
    if name=='qualification_tap':
     output=ns['render'](py);inverse=None;mode='whole_exact_delta'
    else:output,inverse=ns['adapt'](py);mode='actual_codec_undo'
    files={n:b for n,b in files.items()if not n.endswith('.py')}
    files.update({n:s.encode()for n,s in output.items()})
    bundle=inverse
   else:
    bundle=ns['adapt'](files);files=bundle['files'];mode='actual_inverse'
   compiled=compile_all(files)
   changed=sorted(n for n in files if files[n]!=before.get(n))
   stages.append(dict(name=name,before=before,after=files,mode=mode,ns=ns,bundle=bundle))
   events.append(dict(stage=name,changed=changed,files=len(files),compiled_py=compiled))
  for r,_,_ in HELPERS:
   n=Path(r).name
   if n not in('fastpath_numeric_observer.py','fastpath_numeric_sink.py','fastpath_numeric_consumer.py'):
    need(files[n]==helpers[n],'added helper exact fixed bytes '+n)
  back=files
  for stage in reversed(stages):back=undo_stage(stage,back)
  need(back==parent,'ALL parent bytes and keys restored')
  return dict(parent=parent,files=files,stages=stages,events=events)

def controls():
 before=dict(sys.modules);before_path=list(sys.path)
 aliases=['render_geometry','render_capacity','render_native_input','render_numeric_2k','render_state_codec','qualification_tap_delta']
 missing=object();saved={n:sys.modules.get(n,missing)for n in aliases}
 try:
  for i,n in enumerate(aliases):sys.modules[n]=None if i%2 else object()
  poisoned={n:sys.modules[n]for n in aliases}
  b=compose()
  need(all(sys.modules[n]is value for n,value in poisoned.items()),'poison and None aliases restored')
  need(sys.path==before_path,'no import path drift')
  # Actual native-input public renderer rejects missing geometry/snapshot; not a fake marker.
  ns=load_renderer(RENDERERS[3])
  try:ns['adapt'](b['parent'])
  except ValueError as e:need('fixed composition'in str(e),'actual order rejection')
  else:raise ValueError('missing predecessor accepted')
  last=b['stages'][-1];tampered=dict(b['files'])
  tampered['service_runner.py']+=b'\n# unexpected source drift\n'
  try:undo_stage(last,tampered)
  except ValueError:pass
  else:raise ValueError('changed after bytes accepted')
  p=WS/RENDERERS[0][1]
  try:checked(p,(RENDERERS[0][2],'0'*64))
  except ValueError:pass
  else:raise ValueError('wrong real renderer pin accepted')
  # Codec must not silently apply twice to the actual fully composed observer.
  codec=load_renderer(RENDERERS[-1])
  try:codec['adapt']({n:v.decode()for n,v in b['files'].items()if n.endswith('.py')})
  except ValueError as e:need('twice'in str(e),'actual double codec rejection')
  else:raise ValueError('double codec accepted')
 finally:
  for n,v in saved.items():
   if v is missing:sys.modules.pop(n,None)
   else:sys.modules[n]=v
 need(set(sys.modules)==set(before)and all(sys.modules[k]is v for k,v in before.items()),'complete module state restored')
 return dict(schema='bole.actual-six-component-composition/v1',events=b['events'],
  parent_files=len(b['parent']),final_files=len(b['files']),parent_py=compile_all(b['parent']),
  final_py=compile_all(b['files']),whole_inverse=True,poison_and_None_restored=True,
  actual_wrong_order_rejected=True,after_drift_rejected=True,wrong_pin_rejected=True,
  double_codec_rejected=True,pinned_codec_commit=COMMIT,source_bound=False,
  whole2k_ready=False,numerical_qualified=False,NPU=False,HTTP=False,pending=PENDING)

if __name__=='__main__':
 if not sys.argv[1:]:print(json.dumps(dict(enabled=False,whole2k_ready=False,NPU=False)))
 else:
  need(sys.argv[1:]==['--check'],'only explicit pure-host --check')
  print(json.dumps(controls(),sort_keys=True))
