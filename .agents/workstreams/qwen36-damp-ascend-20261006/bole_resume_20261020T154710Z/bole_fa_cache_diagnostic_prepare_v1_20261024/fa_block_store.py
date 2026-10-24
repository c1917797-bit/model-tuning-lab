"""Immutable content blocks and bounded delta manifests; no tensor math/admission."""
import fa_cache_advisory as CACHE
import hashlib
import json
import os
from pathlib import Path

BLOCK=64*1024
import disk_ledger as D
RAW_CAP=D.template_disk_cap()
META_CAP=64*2**20
CHECKPOINT=128*2**20
MAX_TENSOR=40*2**20
MAX_BLOCKS=MAX_TENSOR//BLOCK
MAX_CHAIN=640
DTYPES={'bfloat16':2,'float16':2,'float32':4,'float64':8,'bool':1,'int32':4,'int64':8,'uint8':1}


def need(v,s):
 if not v:raise ValueError(s)


def digest(raw):return hashlib.sha256(raw).hexdigest()


def canonical(v):return (json.dumps(v,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n').encode()


def sha(v):
 return type(v)is str and len(v)==64 and all(c in'0123456789abcdef'for c in v)


def shape_nbytes(shape,dtype):
 need(type(shape)is list and all(type(n)is int and n>=0 for n in shape)and
      type(dtype)is str and dtype in DTYPES,'strict actual raw dtype/shape')
 count=1
 for n in shape:
  count*=n;need(count*DTYPES[dtype]<=MAX_TENSOR,'one bounded layer operand before allocation')
 return count*DTYPES[dtype]


def exact_ref(path,raw):return dict(path=str(path),bytes=len(raw),sha256=digest(raw))


def ordinary(path):
 p=Path(path)
 need(p.is_absolute()and not any(q.is_symlink()for q in(p,*p.parents)),'ordinary absolute owned file')
 return p


def read_ref(r,root,cap):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and
      0<=r['bytes']<=cap and sha(r['sha256']),'strict bounded immutable Ref3')
 p=ordinary(r['path']);need(p.parent==root and p.is_file(),'only exact owned archive leaf')
 before=p.stat();need(before.st_size==r['bytes'],'actual file size bounded before read')
 raw=CACHE.verified_read(p,r,root,cap,digest) if CACHE.selected(root,p) else p.read_bytes();after=p.stat()
 need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
      (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)and
      exact_ref(p,raw)==r,'stable complete immutable archive identity')
 return raw


class CaptureFailure(ValueError):
 pass


class Store:
 def __init__(self,c):
  # c is the original source-owned sink context, not a caller PASS or new owner.
  self.c=c;self.root=ordinary(Path(c['root'])/'FA-BLOCKS')
  need(not self.root.exists(),'exclusive new FA evidence leaf')
  self.root.mkdir(mode=0o700);CACHE.configure(c,self.root);self.index={};self.last={};self.failed=False
  self.references={};self.frame_refs={};self.meta_index={};self.failure=None
 def _write(self,name,raw,*,metadata):
  p=None;charged=False
  try:
   need(not self.failed and type(raw)is bytes,'sticky archive failure')
   c=self.c
   need(type(c['used'])is int and type(c['metadata_bytes'])is int and
        c['used']>=0 and c['metadata_bytes']>=0,'real original evidence counters')
   D.archive_before(c,len(raw),metadata=metadata)
   if metadata:need(c['metadata_bytes']+len(raw)<=META_CAP,'all FA manifests inside original64MiB JSON cap')
   p=self.root/name
   fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
   with os.fdopen(fd,'wb')as f:
    n=f.write(raw);need(n==len(raw),'complete immutable block write');f.flush();os.fsync(f.fileno())
   fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
   try:os.fsync(fd)
   finally:os.close(fd)
   r=exact_ref(p,raw)
   need(read_ref(r,self.root,len(raw))==raw,'actual independent reopen before block reuse')
   # Blob bytes and JSON bytes have separate original counters. JSON reserve is
   # never free; original sink metadata checks and final all-leaf audit include it.
   if metadata:c['metadata_bytes']+=len(raw)
   else:c['used']+=len(raw)
   charged=True
   self.references[r['path']]=r
   return r
  except Exception as error:
   self.failed=True
   if p is not None and p.is_file():
    # Preserve exact partial bytes even on fsync/short-write failure. Never
    # replace a bad block, emit ACK, or retry this Store after first refusal.
    observed=p.read_bytes();self.failure=exact_ref(p,observed)
    if not charged:
     if metadata:self.c['metadata_bytes']+=len(observed)
     else:self.c['used']+=len(observed)
    raise CaptureFailure('first failed immutable write retained: '+json.dumps(self.failure,sort_keys=True))from error
   raise
 def put(self,raw):
  try:return self._put(raw)
  except Exception:self.failed=True;raise
 def _put(self,raw):
  need(not self.failed and type(raw)is bytes and 0<len(raw)<=BLOCK,'one bounded actual block')
  key=(digest(raw),len(raw))
  if key in self.index:
   r=self.index[key]
   try:need(read_ref(r,self.root,BLOCK)==raw,'SHA collision/full existing block drift')
   except Exception:self.failed=True;raise
   return r
  r=self._write('B-'+key[0]+'.bin',raw,metadata=False);self.index[key]=r;return r
 def tensor(self,blocks,*,shape,dtype,family,witness):
  """blocks yields actual complete CPU byte chunks, not a serialized tensor."""
  try:
   nbytes=shape_nbytes(shape,dtype)
   need(type(family)is str and 0<len(family)<160 and type(witness)is dict,'typed layer/family/witness')
   items=[];h=hashlib.sha256();count=0
   for raw in blocks:
    need(type(raw)is bytes and 0<len(raw)<=BLOCK and count+len(raw)<=nbytes,'bounded gapless actual tensor blocks')
    if count+len(raw)<nbytes:need(len(raw)==BLOCK,'only final block may be short')
    h.update(raw);count+=len(raw);items.append(self.put(raw))
   need(count==nbytes and len(items)==(nbytes+BLOCK-1)//BLOCK,'complete exact tensor extent')
   value=dict(schema='bole.immutable-fa-tensor/v1',shape=shape,dtype=dtype,nbytes=nbytes,
    sha256=h.hexdigest(),blocks=items)
   key=(family,tuple(shape),dtype)
   previous=self.last.get(key)
   if previous is not None and previous[1]['sha256']==value['sha256']:
    need(previous[1]['blocks']==items,'same full digest must have exact complete block identities')
    r=previous[0]
   else:
    base=None;changes=[[i,r]for i,r in enumerate(items)]
    if previous is not None:
     base=previous[0];old=previous[1]['blocks']
     changes=[[i,r]for i,r in enumerate(items)if i>=len(old)or old[i]!=r]
    manifest={k:v for k,v in value.items()if k!='blocks'}
    manifest.update(base=base,block_count=len(items),changes=changes)
    raw=canonical(manifest);need(len(raw)<=256*1024,'original individual metadata bound')
    code=digest(raw)
    if code in self.meta_index:
     r=self.meta_index[code];need(read_ref(r,self.root,256*1024)==raw,'existing immutable manifest bytes')
    else:
     r=self._write('T-'+code+'.json',raw,metadata=True);self.meta_index[code]=r
    self.last[key]=(r,value)
   # Witness is current source/rank/owner/layer/phase. Cross-generation storage
   # reuse is byte compression ONLY; it never proves state continuity.
   return dict(schema='bole.actual-fa-tensor-block-ref/v1',tensor=r,
    shape=list(shape),dtype=dtype,nbytes=nbytes,sha256=value['sha256'],witness=witness)
  except Exception:self.failed=True;raise


class Reader:
 def __init__(self,root):
  self.root=ordinary(root);need(self.root.is_dir(),'actual archive root');self.cache={}
 def manifest(self,r,*,seen=None):
  if r['path']in self.cache:
   old,ref=self.cache[r['path']];need(ref==r,'one exact cached immutable manifest identity')
   read_ref(r,self.root,256*1024)
   return old
  seen=set()if seen is None else seen
  need(r['path']not in seen and len(seen)<MAX_CHAIN,'no cyclic or unbounded manifest predecessor')
  seen.add(r['path']);v=json.loads(read_ref(r,self.root,256*1024))
  need(type(v)is dict and set(v)=={'schema','shape','dtype','nbytes','sha256','base','block_count','changes'}and
       v['schema']=='bole.immutable-fa-tensor/v1'and type(v['nbytes'])is int and
       v['nbytes']==shape_nbytes(v['shape'],v['dtype'])and sha(v['sha256'])and
       type(v['block_count'])is int and v['block_count']==(v['nbytes']+BLOCK-1)//BLOCK<=MAX_BLOCKS,
       'strict complete bounded tensor manifest')
  if v['base']is None:items=[None]*v['block_count']
  else:
   old=self.manifest(v['base'],seen=seen)
   need(old['shape']==v['shape']and old['dtype']==v['dtype'],'same byte-layout compression base')
   items=list(old['blocks'])
  need(type(v['changes'])is list,'ordered exact block deltas')
  last=-1
  for pair in v['changes']:
   need(type(pair)is list and len(pair)==2 and type(pair[0])is int and
        last<pair[0]<len(items),'unique sorted in-range changed block')
   last=pair[0];item=pair[1]
   need(type(item)is dict and set(item)=={'path','bytes','sha256'}and
        type(item['bytes'])is int and item['bytes']==min(BLOCK,v['nbytes']-pair[0]*BLOCK),
        'strict exact block extent, no bool/extra data')
   need(ordinary(item['path']).parent==self.root,'owned immutable blocks only')
   items[pair[0]]=item
  need(all(x is not None for x in items),'full base-free manifest covers all bytes')
  result=dict(v,blocks=items);self.cache[r['path']]=(result,dict(r));return result
 def raw(self,ref,*,expected_witness):
  need(type(ref)is dict and set(ref)=={'schema','tensor','shape','dtype','nbytes','sha256','witness'}and
       ref['schema']=='bole.actual-fa-tensor-block-ref/v1'and ref['witness']==expected_witness,
       'exact current source/rank/owner/layer/phase witness, never metadata PASS')
  v=self.manifest(ref['tensor'])
  need(all(v[k]==ref[k]for k in('shape','dtype','nbytes','sha256')),'actual witness and complete manifest join')
  pieces=[read_ref(r,self.root,BLOCK)for r in v['blocks']]
  raw=b''.join(pieces)
  need(len(raw)==v['nbytes']and digest(raw)==v['sha256'],'independent complete tensor byte reconstruction')
  return raw
 def tensor(self,t,ref,*,expected_witness):
  raw=self.raw(ref,expected_witness=expected_witness)
  dtype=getattr(t,ref['dtype'])
  value=t.frombuffer(bytearray(raw),dtype=dtype).reshape(ref['shape']).clone()if raw else t.empty(ref['shape'],dtype=dtype)
  need(value.device.type=='cpu'and value.numel()*value.element_size()==ref['nbytes'],'exact CPU dtype/shape without cast')
  return value


def geometry_bound(native_pages=264,scratch_pages=257):
 need(type(native_pages)is int and native_pages>=256 and type(scratch_pages)is int and scratch_pages>=257,
      'actual32k publication/private page domains, not invented allocation')
 native=16*2*native_pages*128*256*2
 # One decoded FA before+after K/V plus actual private scratch K/V; all16 are
 # validated serially. This is a payload bound, NOT a full Torch RAM peak.
 decoded=(4*native_pages+2*scratch_pages)*128*256*2
 return dict(full_native_FA_bytes=native,whole_native_exceeds448MiB=native>448*2**20,
  per_layer_decoded_payload_bytes=decoded,logical_cap=448*2**20,raw_cap=RAW_CAP,
  first_two_uncompressed_baselines_exceed_raw=(2*native+CHECKPOINT+META_CAP>RAW_CAP),
  requires_actual_unique_blocks=True,fit_proven=False,runtime_admitted=False)
