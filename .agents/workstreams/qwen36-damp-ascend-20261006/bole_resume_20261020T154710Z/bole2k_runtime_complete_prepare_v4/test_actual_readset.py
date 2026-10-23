"""Real current source read/mount integration controls; no container or NPU."""
import ast,hashlib,importlib,json,runpy,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'bole2k_runtime_complete_prepare_v3/prepared-source-short8-qualifier'

def main():
 B=runpy.run_path(str(HERE/'complete_runtime_blueprint.py'),run_name='_v4_check')
 bundle=B['render']();B['inverse'](bundle)
 raw=(OLD/'SOURCE_BOUND.json').read_bytes()
 sr=dict(path=str(OLD/'SOURCE_BOUND.json'),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 m=json.loads(raw)
 saved=dict(sys.modules);paths=list(sys.path)
 try:
  sys.path.insert(0,str(OLD))
  C=importlib.import_module('contract090')
  V=importlib.import_module('followup_source_validate')
  proof=V.validate(sr)
  bind=importlib.import_module('bind_model')
  command=importlib.import_module('command_contract')
  original=bind.readset(sr)+m['dependencies']+command.validate(C,sr,m)
  gc=types.ModuleType('guest_readset_coverage')
  gc.__file__=str(HERE/'prospective-guest-readset-coverage.py')
  exec(compile(bundle['files']['guest_readset_coverage.py'],gc.__file__,'exec'),gc.__dict__)
  sys.modules['guest_readset_coverage']=gc
  host=bundle['files']['host_service.py'].decode()
  node=next(n for n in ast.parse(host).body if isinstance(n,ast.FunctionDef)and n.name=='complete_readset')
  ns={};exec(compile(ast.get_source_segment(host,node),'<actual-v4-complete-readset>','exec'),ns)
  # This is the real V3 parser, hash gate, parent proof and original readset.
  # Only the new source-owned helper itself is compiled prospectively.
  calls={};checked=C.checked
  def counted(r):
   calls[r['path']]=calls.get(r['path'],0)+1
   return checked(r)
  C.checked=counted
  try:rows=ns['complete_readset'](C,original,proof,sr)
  finally:C.checked=checked
  idx={r['path']:r for r in rows}
  assert all(idx.get(r['path'])==r for r in gc.AUDIT17)
  missing_before=[r['path']for r in gc.AUDIT17 if r not in original and r not in proof['readset']]
  assert len(missing_before)==17
  # No guessed workspace mount. The actual source root alone and exact extra
  # RO files are the same mapping form used by the existing producer.
  mounts=[dict(Source=str(OLD),Destination=str(OLD),RW=False)]
  mounts.extend(dict(Source=r['path'],Destination=r['path'],RW=False)
   for r in rows if Path(r['path'])!=OLD and OLD not in Path(r['path']).parents)
  coverage=gc.mount_coverage(C,gc.required(C,sr,original),mounts,OLD)
  controls={}
  def rejects(label,fn):
   try:fn()
   except (ValueError,AssertionError):controls[label]=True
   else:raise AssertionError('missing rejection '+label)
  bad=dict(gc.AUDIT17[0],sha256='0'*64)
  rejects('conflicting_ref',lambda:ns['complete_readset'](C,[*original,bad],proof,sr))
  rejects('missing_proof_source',lambda:ns['complete_readset'](C,original,dict(proof,source={}),sr))
  dropped=[x for x in mounts if x['Destination']!=gc.AUDIT17[0]['path']]
  rejects('missing_exact_mount',lambda:gc.mount_coverage(C,[gc.AUDIT17[0]],dropped,OLD))
  rw=[dict(x,RW=True)if x['Destination']==gc.AUDIT17[0]['path']else x for x in mounts]
  rejects('writable_dependency',lambda:gc.mount_coverage(C,[gc.AUDIT17[0]],rw,OLD))
  print(json.dumps(dict(schema='bole.v4.actual-readset-integration-controls/v1',
   original=len(original),proof=len(proof['readset']),complete=len(rows),
   actual17_added=True,required_unique_checks=len(calls),maximum_checks_per_path=max(calls.values()),
   mount_coverage=coverage,negative_controls=controls,
   complete_source_compiled=len(bundle['files']),whole_inverse=True,
   source_bound=False,container_started=False,NPU=False,numerical_qualification=False)))
 finally:
  sys.modules.clear();sys.modules.update(saved);sys.path[:]=paths

if __name__=='__main__':main()
