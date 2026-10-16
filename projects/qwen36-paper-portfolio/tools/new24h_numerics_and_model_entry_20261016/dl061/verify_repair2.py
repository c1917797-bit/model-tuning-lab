"""Exact single numerical predicate delta; no candidate algorithm mutation."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;OLD=P.parent/'deltalog-mixed-precast-new48h-20261015-043-repair1'
def h(b):return hashlib.sha256(b).hexdigest()
def main():
 a=" passed=(not pred['finite']and not pred['passed'])if overflow else(pred['passed']and all(math.isfinite(e)and e<=R.STATE_LIMIT for e in states))"
 b=" state_pass=all(math.isfinite(e)and e<=R.STATE_LIMIT for e in states)\n passed=state_pass and ((not pred['finite']and not pred['passed'])if overflow else pred['passed'])"
 old=(OLD/'sidecar_audit.py').read_text(encoding='utf8');new=(P/'sidecar_audit.py').read_text(encoding='utf8');assert old.count(a)==1 and old.replace(a,b)==new
 files=('producer.py','oracle.py','consume.py','consume_increment.py','flush_increment.py','precast.py','direct_round.py','npu_controls.py','sidecar_capture.py','per_request_increment.py','qwen36_deltalog_fresh/provider.py','qwen36_deltalog_fresh/primitives.py','qwen36_deltalog_fresh/native_fixture.py')
 unchanged={}
 for n in files:
  x=(P/n).read_bytes();assert x==(OLD/n).read_bytes(),n;unchanged[n]=h(x)
 result=dict(numerical_delta='expected output overflow still requires original finite state error<=7.92e-7',old_audit_sha256=h(old.encode()),new_audit_sha256=h(new.encode()),unchanged_source_SHA256=unchanged,NPU=False)
 with (P/'REPAIR2_DELTA.json').open('x',encoding='utf8',newline='\n')as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
 print(json.dumps(result))
if __name__=='__main__':main()
