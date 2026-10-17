"""Existing118 ARM guest calls this bounded internal runner, never a launcher."""
import gc,io,json,os,time
from pathlib import Path
import factor as F,decision_gate as G
CAP=256*2**20
def save(t,C,p,v,root):
 C.need(not p.exists(),'exclusive evidence file')
 buffer=io.BytesIO();t.save(v,buffer);data=buffer.getvalue();C.need(len(data)<=4*2**20,'pre-write bounded one-call evidence4MiB')
 used=sum(q.stat().st_size for q in root.iterdir()if q.is_file())
 C.need(used+len(data)<=CAP-32*2**20,'all raw/BEFORE evidence plus reserved32MiB metadata within256MiB')
 with p.open('xb')as out:
  out.write(data);out.flush();os.fsync(out.fileno())
 return C.ref(p)
def json_write(C,p,v,root):
 data=(json.dumps(v,sort_keys=True,allow_nan=False)+'\n').encode()
 C.need(sum(q.stat().st_size for q in root.iterdir()if q.is_file())+len(data)<=CAP,'pre-write total256MiB includes every scalar receipt')
 with p.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 return C.ref(p)
def run(t,torch_npu,C,m,out,deadline):
 C.need(out.is_dir()and not any(out.iterdir()),'fresh owned output')
 proof=G.consume(C,m['actual_diagnostic_source'],m['actual_diagnostic_owner'])
 abi=C.obj(m['actual_abi_ref']);family=F.validate_abi(t,torch_npu,C,abi);rows=[]
 for pair in proof['ranks']:
  maps=Path('/proc/self/maps').read_text();C.need(len(maps.encode())<=2**20,'bounded original process maps1MiB')
  json_write(C,out/('MAPS-BEFORE-RANK-%d.json'%pair['rank']),dict(source=m['_actual_source'],pid=os.getpid(),maps=maps,NPU=True,
     note='loaded mappings only, not a proof of exact resolved FIA C symbol DSO'),out)
  rank=pair['rank'];blob=t.load(C.checked(pair['raw']),map_location='cpu',weights_only=False)
  C.need(blob['schema']=='bole.model-diagnostic-primitives/v1'and blob['logical_tensor_bytes']<=2**30,'original complete bounded raw export')
  raw=blob['payload'];C.need(raw['source']==G.ORIGINAL_SOURCE and raw['rank']==rank,'exact original R17 rank/source')
  for layer in range(3,64,4):
   saved=raw['tree_context']['captures'][layer]['trial']['native_before']
   for arm in F.ARMS:
    C.need(time.time()<deadline,'original guest/whole/fixed authority deadline')
    stem='%d-%d-%s'%(rank,layer,arm[0]);before=out/('BEFORE-'+stem+'.pt');result=out/('RAW-'+stem+'.pt')
    meta=dict(schema='bole.saved-FA-single-factor-raw/v1',source=m['_actual_source'],rank=rank,layer=layer,
       original_raw=pair['raw'],original_producer=pair['producer'],cpu_diagnostic=pair['diagnostic'],actual_abi_ref=m['actual_abi_ref'])
    def capture(value):save(t,C,before,dict(meta,call=value),out)
    value=F.call(t,torch_npu,saved,arm,before_callback=capture)
    rr=save(t,C,result,dict(meta,call=value),out)
    row=dict(rank=rank,layer=layer,arm=arm[0],before=C.ref(before),raw=rr,primary=value['primary'])
    rows.append(row);json_write(C,out/('ROW-'+stem+'.json'),row,out)
  del blob,raw;gc.collect()
  maps=Path('/proc/self/maps').read_text();C.need(len(maps.encode())<=2**20,'bounded final process maps1MiB')
  json_write(C,out/('MAPS-AFTER-RANK-%d.json'%pair['rank']),dict(source=m['_actual_source'],pid=os.getpid(),maps=maps,NPU=True),out)
 value=dict(schema='bole.saved-FA-single-factor-stage/v1',source=m['_actual_source'],rows=rows,
    actual_abi_ref=m['actual_abi_ref'],actual_dispatch_family=family,actual_diagnostic_owner=m['actual_diagnostic_owner'],
    NPU=True,operator_calls_attempted=256,qualified=False,model_ready=False,original_failures_unchanged=True)
 C.need(len(rows)==256,'complete four-rank sixteen-layer four-arm matrix')
 json_write(C,out/'STAGE_RESULT.json',value,out);return value
