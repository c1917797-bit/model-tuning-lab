"""Bounded exclusive actual native identity events, no request mutations."""
import json,os
from pathlib import Path
import sourceio as C


def emitter(source_ref,role):
 m=C.obj(source_ref);root=Path(os.environ['BOLE_MODEL_RAW_ROOT'])
 C.need(str(root)==m['model_receipt_root']and root.is_dir(),'exact owned identity root')
 C.need(role=='frontend'or role in tuple('rank%d'%i for i in range(4)), 'actual journal role')
 count=0;total=0
 def emit(kind,event):
  nonlocal count,total
  count+=1
  value=dict(schema='bole.actual-identity-journal/v1',source=source_ref,role=role,kind=kind,event=event)
  body=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode('utf8');total+=len(body)
  C.need(count<=512 and total<=8*2**20,'bounded512 actual events/8MiB per process')
  path=root/('IDENTITY-%s-%06d.json'%(role,count))
  with path.open('xb')as f:f.write(body);f.flush();os.fsync(f.fileno())
  return C.ref(path)
 return emit


def install_frontend(source_ref):
 import identity_capture
 from vllm.v1.engine.input_processor import InputProcessor
 return identity_capture.install_assignment(InputProcessor,emitter(source_ref,'frontend'))


def install_worker(source_ref,worker,rank):
 import identity_capture
 return identity_capture.install_worker(type(worker.model_runner),rank,emitter(source_ref,'rank%d'%rank))
