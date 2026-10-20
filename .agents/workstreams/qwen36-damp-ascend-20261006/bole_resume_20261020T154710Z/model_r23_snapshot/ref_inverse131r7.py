"""Test-only strict mechanical inverse; never loaded by production owner."""
import hashlib,json
def restore(body,plan_bytes,ref):
 def need(ok):
  if not ok:raise ValueError('exact complete R7 Ref boundary inverse')
 def identity(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 need(identity(plan_bytes)=={k:ref[k]for k in('bytes','sha256')})
 plan=json.loads(plan_bytes);need(identity(body)==plan['after']);text=body.decode('utf8')
 for e in reversed(plan['edits']):
  need(text.count(e['after'])==e['count']);text=text.replace(e['after'],e['before'])
 result=text.encode();need(identity(result)==plan['before']);return result
