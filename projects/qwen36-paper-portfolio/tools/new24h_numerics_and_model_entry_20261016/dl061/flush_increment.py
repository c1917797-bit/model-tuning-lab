"""Default-OFF producer increment for the existing real native bridge005.

No fake native implementation: only the exact source-pinned021 flush function
is installed into the legacy module passed to native_fixture.mixed_case.
"""
import ast,hashlib,pathlib
EXPECTED='1b9a2e53ce137f319ca5939be6e21fa293735edd363cdc37f7b438626e985470'
FIELDS=('base','k_log','u_log','lambda_log','decay','length')
def install(torch,legacy,source,records,*,execute=False,max_records=4):
 if not execute:raise RuntimeError('explicit owned numeric admission required')
 p=pathlib.Path(source['path']);b=p.read_bytes()
 if len(b)!=11828 or hashlib.sha256(b).hexdigest()!=EXPECTED or source['sha256']!=EXPECTED:raise ValueError('actual021 exact source')
 tree=ast.parse(b);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='_flush_slots')
 node=ast.Module(body=[fn],type_ignores=[]);ast.fix_missing_locations(node)
 events=[];ns=dict(Any=object,CAPACITY=7,VALUE_HEADS=12,KEY_HEADS=4,_audit=lambda *a,**kw:events.append((a,kw)))
 exec(compile(node,str(p),'exec'),ns);actual=ns['_flush_slots']
 def flush(T,layer,aux,indices,reason,selection='batch'):
  if indices.device.type!='npu':raise ValueError('real NPU only; CPU fixture is not evidence')
  ids=indices.flatten().long();length=aux['length'].index_select(0,ids)[:,:,0]
  live=T.arange(7,device=indices.device).view(1,1,7)<length.unsqueeze(-1)
  # Poison only logically dead payloads, leaving all live inputs unchanged.
  for name in ('u_log','k_log'):
   x=aux[name].index_select(0,ids);mask=live if name=='u_log'else live[:,::3]
   x.masked_fill_(~mask.unsqueeze(-1),float('nan'));aux[name].index_copy_(0,ids,x)
  capture=flush.captured<max_records
  before={n:(layer.kv_cache[1]if n=='base'else aux[n]).cpu().clone()for n in FIELDS}if capture else None
  actual(T,layer,aux,indices,reason,selection);T.npu.synchronize()
  after={n:(layer.kv_cache[1]if n=='base'else aux[n]).cpu().clone()for n in FIELDS}if capture else None
  if capture:
   flush.captured+=1
   records.append(dict(before=before,after=after,ids=indices.cpu().clone(),reason=reason,selection=selection,source=source,actual_NPU=True))
 flush.captured=0
 legacy._flush_slots=flush
 return dict(source=source,function='_flush_slots',source_function_unmodified=True,events=events)
