"""Real -I entry.environment -> current-interpreter metadata discovery.

Only test-path metadata is mirrored to a fresh temporary source root. Every
044/source module retains its exact original bytes. No register, torch, vLLM,
HAL, controller or numerical qualification is executed or manufactured.
"""
import argparse,ast,hashlib,importlib,importlib.metadata,importlib.util,json,os,sys,tempfile
from pathlib import Path
COMPONENT=(9183,'f87ee946b055d511280eced9882fd8dd9127bf8f683b7b2993b5c51331a3dd0f')
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 b=Path(p).read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def data(v):return(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def run(entry_source,component_root,donor_root):
 entry_source=Path(entry_source);component_root=Path(component_root);donor_root=Path(donor_root)
 original=(component_root/'SOURCE_MANIFEST.json').read_bytes();need((len(original),hashlib.sha256(original).hexdigest())==COMPONENT,'exact reviewed original044 component manifest')
 original_m=json.loads(original);entry_bytes=entry_source.read_bytes();support=Path(__file__).resolve().parent;helper=(support/'plugin_discovery.py').read_bytes()
 need(not any(n in('torch','vllm')or n.startswith(('torch.','torch_npu','vllm.'))for n in sys.modules),'cold interpreter before real entry')
 with tempfile.TemporaryDirectory(prefix='mxr-real-I-entry-')as td:
  work=Path(td);ep=work/'entry';cp=work/'component';ep.mkdir();cp.mkdir()
  # Mechanical path-only mirror: preserve all actual candidate/source bytes.
  mirrored=dict(original_m);files={}
  for name,r in original_m['files'].items():
   b=(component_root/name).read_bytes();need((len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'actual044 leaf bytes '+name)
   target=cp/name;save(target,b);files[name]=ref(target)
  mirrored.update(root=str(cp),files=files);save(cp/'SOURCE_MANIFEST.json',data(mirrored));cr=ref(cp/'SOURCE_MANIFEST.json')
  save(ep/'entry.py',entry_bytes);save(ep/'plugin_discovery.py',helper);save(ep/'QUALIFICATION_CORRECTNESS.json',(support/'QUALIFICATION_CORRECTNESS.json').read_bytes())
  assignment=next(n for n in ast.parse(entry_bytes).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Tuple)and [x.id for x in t.elts]==['START','CUT']for t in n.targets))
  start,cut=ast.literal_eval(assignment.value)
  # Baseline048 must retain its own historical metadata window so that its
  # expected failure isolates sys.path, not an unrelated new-authority mismatch.
  source=dict(schema='mxr.diag16.full-gdn-frame-bridge-source/v1',root=str(ep),default_enabled=False,window=dict(start=start,cutoff=cut),files={name:ref(ep/name)for name in('entry.py','plugin_discovery.py','QUALIFICATION_CORRECTNESS.json')},plugin_source=cr,raw_storage=dict(root=str(work/'raw')))
  save(ep/'SOURCE_MANIFEST.json',data(source));sr=ref(ep/'SOURCE_MANIFEST.json')
  s=importlib.util.spec_from_file_location('_actual_frozen_entry_under_I',ep/'entry.py');E=importlib.util.module_from_spec(s);s.loader.exec_module(E)
  E.OLD=donor_root # Exact raw() PINS still verify all reused003 source bytes.
  o=E.overlay();o.environment_original=o.environment
  need(str(cp)not in sys.path,'test did not add component to current interpreter')
  env=E.environment(o,sr,{},dict(ASCEND_RT_VISIBLE_DEVICES='0,1,2,3',TORCH_DEVICE_BACKEND_AUTOLOAD='0',VLLM_PLUGINS='ascend'),'/source',str(work/'capture'),'software_source_only')
  os.environ.update(env) # Same original003 sequence; no exec/new interpreter.
  expected={'mxr_common_precision044':'mxr_common_precision044:register','mxr_block_refinement044':'mxr_block_refinement044:register'}
  # Critical check BEFORE helper static_discovery is allowed to touch sys.path.
  actual={x.name:x.value for d in importlib.metadata.distributions()for x in d.entry_points if x.group=='vllm.general_plugins'and x.name in expected}
  need(actual==expected and str(cp)in sys.path,'same-interpreter plugin discovery absent after real entry.environment')
  need('mxr_common_precision044'in env['VLLM_PLUGINS'].split(',')and'mxr_block_refinement044'not in env['VLLM_PLUGINS'].split(','),'same one-installer diagnostic filter')
  D=importlib.import_module('plugin_discovery');value=D.static_discovery(cp)
  need(value['static_import']is True and value['register_called']is False,'actual package static imports only')
  return dict(schema='mxr.actual-I-real-entry-source-discovery/v050',entry_source=ref(entry_source),component_original_manifest_sha256=COMPONENT[1],original003_environment_source=E.PINS['capture_overlay.py'][1],metadata_path_only_mirror=True,no_fixture_path_insertion=True,real_entry_environment=True,current_interpreter_discovery=True,static_import=True,register_called=False,NPU=False,model=False,resource_admitted=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--entry-source',type=Path,required=True);p.add_argument('--component-root',type=Path,required=True);p.add_argument('--donor-root',type=Path,required=True);a=p.parse_args();print(json.dumps(run(a.entry_source,a.component_root,a.donor_root),sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
