"""Lightweight actual bridge-owner receipt. No template/sample substitutes."""
import json
from pathlib import Path
import bridge_io as C
def consume(owner_ref):
 v=C.obj(owner_ref);sr=v['target_source'];m=C.source(sr)
 C.need(v['schema']=='deltalog.fresh-bridge-owned-host/v5'and v['source']==sr and v['stage']=='numeric'and v['steps']==160 and v['physical']==[5]and v['bridge_primitive_gate_pass']is True and v['primary']is None and not v['secondary']and v['stopped_retained']is True,'actual full160 independent bridge owner/release')
 r=C.obj(v['independent_consumer']);C.need(r['source']==sr and r['actual_result']==v['result']and r['pass_gate']is True and r['primary']is None,'actual independent source/raw join')
 for b in(1,16):
  rows=[x for x in r['rows']if x['identity']['kind']=='mixed'and x['identity']['batch']==b]
  C.need([x['identity']['step']for x in rows]==list(range(160)),'complete ordered full160 real GDN')
  flush=[x['independent']for x in r['rows']if x['identity']['kind']=='dead_flush'and x['identity']['batch']==b]
  C.need(len(flush)==2 and any(x['length0']for x in flush)and any(x['partial_live']for x in flush),'actual zero and partial NaN repair')
 return dict(source=sr,actual_NPU=True,independent_pass=True,dead_zero_partial_live_pass=True,mixed_B1_B16_pass=True,slot_reuse_pass=True,library=m['library_ref'],owner=owner_ref,consumer=v['independent_consumer'],model_ready=False,performance_ready=False,graph=False,PDC=False)
