"""Persist each actual independent result before an unchanged aggregate assertion."""
import hashlib,json,os
from pathlib import Path
def one(torch,R,P,raw,source,producer,manifest,output,index,mixed,overflow,controls,checked):
 row=dict(raw=raw,source=source,producer=producer,passed=False,primary=None)
 try:
  import sidecar_audit
  value=torch.load(checked(raw),map_location='cpu',weights_only=False)
  regression=next((c for c in controls if c['raw']==raw and c['case'].startswith('original-B16-')),None)
  if regression is not None:
   import regression052,bridge_io
   regression052.audit(torch,manifest,bridge_io,regression,value)
  row.update(sidecar_audit.audit(torch,R,P,value,overflow=raw['path']in overflow,numeric=raw['path']not in mixed))
 except Exception as e:row['primary']=repr(e)
 p=Path(output).with_name('SIDECAR052-%04d.json'%index)
 with p.open('x',encoding='utf8')as f:json.dump(row,f,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 b=p.read_bytes();row['receipt']=dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 return row
