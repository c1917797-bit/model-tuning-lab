"""Actual copied current ABI regression only; no authority/container/NPU."""
import argparse,json,traceback,types
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,s):
 if not v:raise ValueError(s)
def loaded(path,name):
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),vars(m));return m
def check():
 R=P/'prepared-source'
 B=loaded(R/'prepare_successor.py','_actual_r4_builder')
 t=B.reference(R/'SOURCE_TEMPLATE.json');m=B.validate_template(t)
 # Private input fixture solely substitutes reading an intentionally absent
 # manifest. All71 real source bytes, template and readset are then verified
 # by the unchanged actual current() -> source-owned helper path.
 sr=dict(path=str(R/'SOURCE_MANIFEST.json'),bytes=1,sha256='0'*64)
 fixture=dict(m,prepared_only=False,authority_ref=None,prepared_template_ref=t)
 need(not Path(sr['path']).exists(),'no fabricated execution manifest')
 errors={}
 for label,path in [('original_r3',P.parent/'revision3/prepared-source/event_contract.py'),('fixed_r4',R/'event_contract.py')]:
  C=loaded(path,'_actual_'+label)
  oldobj=C.obj
  C.obj=lambda ref:fixture if ref==sr else oldobj(ref)
  need(type(C.checked(m['files']['successor_bindings.py']))is bytes,'actual inherited event reader returns bytes')
  try:C.current(sr,R)
  except BaseException as exc:errors[label]=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
  else:raise ValueError('unbound actual current unexpectedly accepted')
 need(errors['original_r3']['type']=='AttributeError'and 'read_bytes'in errors['original_r3']['message'],'actual original defect reproduced')
 need(errors['fixed_r4']['type']=='ValueError'and 'authority is unbound'in errors['fixed_r4']['message']
  and 'validate_source'in errors['fixed_r4']['traceback']and 'validate_authority'in errors['fixed_r4']['traceback'],'fixed copied public current reaches specific authority guard after reconstruction')
 S=loaded(R/'successor_bindings.py','_actual_path_reader')
 need(isinstance(B.checked(t),Path)and isinstance(S.checked(t),Path),'separate producer and helper Path APIs retained')
 need(not Path(sr['path']).exists(),'source remains unbound')
 return dict(original_error=errors['original_r3'],fixed_error=errors['fixed_r4'],source_bound=False,NPU=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--check',action='store_true');a=p.parse_args()
 print(json.dumps(check()if a.check else dict(enabled=False,NPU=False)))
if __name__=='__main__':main()
