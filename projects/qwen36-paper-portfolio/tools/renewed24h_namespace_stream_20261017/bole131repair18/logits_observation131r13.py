"""Strict pre-canonical operand evidence only: no cast, mask, or gate change."""
import inspect,json,os
from pathlib import Path
CAP=4*2**20
def object_sources(C,model):
 def identity(obj):
  typ=type(obj);return dict(module=typ.__module__,qualname=typ.__qualname__)
 def method(obj,name):
  fn=getattr(obj,name);body=getattr(fn,'__func__',fn);path=inspect.getsourcefile(body)
  return dict(module=getattr(body,'__module__',None),qualname=getattr(body,'__qualname__',None),source=C.ref(path)if path else None)
 lp=model.logits_processor;head=model.lm_head;q=head.quant_method
 return dict(logits_processor=identity(lp),logits_forward=method(lp,'forward'),get_logits=method(lp,'_get_logits'),quant_method=identity(q),quant_apply=method(q,'apply'),lm_head=identity(head),weight_dtype=str(head.weight.dtype),weight_shape=list(head.weight.shape),org_vocab_size=getattr(lp,'org_vocab_size',None),vocab_size=getattr(lp,'vocab_size',None))
def snapshot(t,value,*,vocab_size,rank,reduced):
 shape=list(value.shape);ndim=value.ndim
 good_vocab=type(vocab_size)is int and vocab_size>0
 expected_local=(vocab_size+3)//4 if good_vocab else None
 start=rank*shape[-1]if ndim==2 and reduced is True else 0
 valid=max(0,min(shape[-1],vocab_size-start))if ndim==2 and good_vocab else 0
 def region(x):
  return dict(elements=x.numel(),nan=int(t.isnan(x).sum().item()),positive_inf=int(t.isposinf(x).sum().item()),negative_inf=int(t.isneginf(x).sum().item()),finite=int(t.isfinite(x).sum().item()))
 return dict(schema='bole.native-logits-operand/v131r13',shape=shape,stride=list(value.stride()),dtype=str(value.dtype),device=str(value.device),rank=rank,reduced=reduced,vocab_size=vocab_size,expected_uniform_local_min=expected_local,valid_columns=valid,region_interpretation='original canonical uniform-rank-major hypothesis; not proof of live processor layout',subconditions=dict(ndim2=ndim==2,dtypeFP32=value.dtype==t.float32,vocab_positive_int=good_vocab,all_finite=bool(t.isfinite(value).all().item())),whole=region(value),valid=region(value[:,:valid])if ndim==2 else None,padding=region(value[:,valid:])if ndim==2 else None,diagnostic_only=True,qualified=False)
def record(t,C,sr,root,rank,value,*,vocab_size,reduced,ordinal,live_sources=None):
 m=C.obj(sr);root=Path(root)
 C.need(str(root)==m['model_receipt_root']and root.is_dir()and not any(p.is_symlink()for p in(root,*root.parents)),'exact existing sole-owned receipt root')
 C.need(type(rank)is int and rank in range(4)and ordinal==0,'one first canonical operand per actual rank')
 C.need(value.numel()*value.element_size()<=CAP-2**16,'bounded original-dtype operand before D2H')
 info=snapshot(t,value,vocab_size=vocab_size,rank=rank,reduced=reduced)
 info.update(source=sr,canonical_source=m['files']['native_logits.py'],observer_source=m['files']['logits_observation131r13.py'],live_sources=live_sources,caller=[dict(file=x.filename,function=x.function,line=x.lineno)for x in inspect.stack(context=0)[1:8]])
 raw=root/('BOLE-LOGITS-OPERAND-RANK-%d.pt'%rank)
 with raw.open('xb')as f:t.save(dict(logits=value.detach().cpu().clone()),f);f.flush();os.fsync(f.fileno())
 C.need(raw.stat().st_size<=CAP-2**15,'bounded exact original-dtype serialized raw')
 info['raw']=C.ref(raw);path=root/('BOLE-LOGITS-OPERAND-RANK-%d.json'%rank)
 with path.open('x',encoding='utf8',newline='\n')as f:json.dump(info,f,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 C.need(raw.stat().st_size+path.stat().st_size<=CAP,'combined operand evidence cap reserved inside original rank cap')
 if os.name!='nt':
  fd=os.open(str(root),os.O_RDONLY)
  try:os.fsync(fd)
  finally:os.close(fd)
 return C.ref(path)
