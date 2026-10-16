"""Join actual both-arm common policy receipts to existing025 worker proof."""
from pathlib import Path
import api122 as A
def snapshot(c,ctl,root):
 sr=ctl.expected['source'];m=A.source(sr,pair=True);health=A.obj(A.obj(m['health_owner_ref'])['numeric']);from precision122 import validate_pair
 rows=c.obj(ctl.observe('common-policy-before'))['actual_compute'];result=[]
 for card in(4,5,6,7):
  matches=[r for r in rows if r['physical']==card];A.need(len(matches)==1,'one actual owned worker percard');r=matches[0];p=Path('/proc')/str(r['pid']);text=(p/'stat').read_text()
  A.need(int(text[text.rfind(')')+2:].split()[19])==r['start_ticks']and ctl.cid in(p/'cgroup').read_text(),'fresh owned worker policy identity')
  ns=[int(x)for l in(p/'status').read_text().splitlines()if l.startswith('NSpid:')for x in l.split()[1:]];A.need(ns,'namespace PID');file=root/('common-policy-%d.json'%ns[-1]);v=c.obj(c.ref(file))
  A.need(v['schema']=='deltalog.common-precision-worker/v122'and v['source']==sr and v['arm']==ctl.expected['arm']and v['pid']==ns[-1]and v['logical']==card-4 and v['policy']==dict(matmul_allow_hf32=False,conv_allow_hf32=False),'actual identical common HF32OFF botharms')
  validate_pair(v['actual_precision'],v['actual_precision_after'],health['actual_precision']['common_source'])
  A.need(v['actual_precision_after']['deterministic']==health['actual_precision_after']['deterministic'],'health and both model arms same actual deterministic flags')
  result.append(dict(host=r,guest=v,raw=c.ref(file)))
 return result
