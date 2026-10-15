"""Reuse exact019 owned CPU controller; no resource/cleanup/Lane body changes."""
import ast,hashlib,importlib.util,inspect,json,sys,textwrap
from pathlib import Path
HERE=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def transform_main(original):
 old="om['schema']=='deltalog.raw-bitwise-audit-source/v019'";new="om['schema']=='deltalog.composite-source/v022'"
 source=textwrap.dedent(original);need(source.count(old)==1,'one exact019 schema anchor');changed=source.replace(old,new);need(changed.replace(new,old)==source,'reversible single schema delta');ast.parse(changed);return changed
def main():
 if '--execute'not in sys.argv and '--source-audit-only'not in sys.argv:print('disabled');return 0
 p=HERE/'SOURCE_TEMPLATE.json';t=json.loads(p.read_bytes());r=t['original019_host_ref'];b=Path(r['path']).read_bytes();need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'exact existing019 ownedCPU controller')
 s=importlib.util.spec_from_file_location('_frozen019_ownedCPU',r['path']);H=importlib.util.module_from_spec(s);s.loader.exec_module(H)
 H.HERE=HERE;H.OWNER='deltalog-composite-new48h-MAIN-022';H.__file__=str(Path(__file__).resolve())
 def closure(sr):
  m=H.obj(sr);C=H.load(m['files']['io_contract.py'],'_composite022_contract');need(C.source(sr)==m,'bound exact022 CPU target')
  refs=[sr,*m['files'].values(),*m['diagnostic_input_refs'],r]
  for q in refs:H.checked(q)
  return HERE,m,C,refs,HERE
 H.target_closure=closure
 ns={};exec(compile(transform_main(inspect.getsource(H.main)),str(HERE/'host.py')+':schema-only019-main','exec'),H.__dict__,ns)
 return ns['main']()
if __name__=='__main__':raise SystemExit(main())
