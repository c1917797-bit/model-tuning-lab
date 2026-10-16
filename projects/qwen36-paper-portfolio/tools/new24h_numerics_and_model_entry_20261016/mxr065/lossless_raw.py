"""Only exact equal boundary tensors share serialized storage; every leaf audited."""
import hashlib,json
ELIGIBLE=('v','g','beta','initial_state','cu_seqlens')
def need(v,s):
 if not v:raise ValueError(s)
def descriptor(torch,t):
 c=t.detach().cpu().contiguous();view=c.view(torch.uint8).numpy()
 return dict(dtype=str(t.dtype),shape=list(t.shape),stride=list(t.stride()),storage_offset=t.storage_offset(),bytes=t.numel()*t.element_size(),sha256=hashlib.sha256(memoryview(view)).hexdigest())
def leaves(torch,obj,path=()):
 if torch.is_tensor(obj):yield path,obj
 elif isinstance(obj,dict):
  for k,v in obj.items():yield from leaves(torch,v,path+(k,))
def prepare(torch,payload):
 table=[dict(path=list(p),**descriptor(torch,t))for p,t in leaves(torch,payload)]
 aliases=[];saved=0
 if 'inputs'in payload and 'normalized_inputs'in payload:
  a,b=payload['inputs'],payload['normalized_inputs']
  for k in ELIGIBLE:
   if k not in a or k not in b or not torch.is_tensor(a[k])or not torch.is_tensor(b[k]):continue
   da,db=descriptor(torch,a[k]),descriptor(torch,b[k])
   if da!=db:continue
   need(torch.equal(a[k].contiguous().view(torch.uint8),b[k].contiguous().view(torch.uint8)),'full byte equality, not approximate')
   b[k]=a[k];aliases.append(dict(path=['normalized_inputs',k],target=['inputs',k],descriptor=da));saved+=da['bytes']
 return dict(schema='mxr.lossless-boundary-sharing/v1',payload=payload,manifest=dict(schema='mxr.lossless-full-tensor-leaves/v1',leaves=table,aliases=aliases,logical_bytes=sum(x['bytes']for x in table),exact_alias_saved_bytes=saved,compression_claim=False))
def restore(torch,bundle,sidecar):
 need(set(bundle)=={'schema','payload','manifest'}and bundle['schema']=='mxr.lossless-boundary-sharing/v1','exact shared raw schema')
 need(bundle['manifest']==sidecar,'independent sidecar matches persisted manifest')
 p=bundle['payload'];actual=[dict(path=list(k),**descriptor(torch,t))for k,t in leaves(torch,p)]
 need(actual==sidecar['leaves'],'all original logical tensor dtype/shape/stride/offset/fullhash restored')
 allowed={('normalized_inputs',k)for k in ELIGIBLE};seen=set()
 for a in sidecar['aliases']:
  path=tuple(a['path']);target=tuple(a['target']);need(path in allowed and target==('inputs',path[1])and path not in seen,'restricted unique direct alias')
  seen.add(path);x=p[path[0]][path[1]];y=p[target[0]][target[1]]
  need(descriptor(torch,x)==descriptor(torch,y)==a['descriptor'],'exact reverse alias hash chain')
  need(x.untyped_storage().data_ptr()==y.untyped_storage().data_ptr(),'persisted storage sharing is real')
 need(sum(a['descriptor']['bytes']for a in sidecar['aliases'])==sidecar['exact_alias_saved_bytes'],'exact savings ledger')
 return p
def write(torch,path,payload):
 path=__import__('pathlib').Path(path);bundle=prepare(torch,payload)
 with path.open('xb')as h:torch.save(bundle,h)
 side=path.with_suffix('.STORAGE.json')
 with side.open('x')as h:json.dump(bundle['manifest'],h,sort_keys=True);h.write('\n')
 return bundle['manifest']
def read(torch,path):
 path=__import__('pathlib').Path(path);side=json.loads(path.with_suffix('.STORAGE.json').read_bytes())
 return restore(torch,torch.load(path,map_location='cpu',weights_only=True),side)
