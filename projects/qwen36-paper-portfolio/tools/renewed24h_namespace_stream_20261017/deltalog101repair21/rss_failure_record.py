"""Observe the unchanged original512MiB rejection; never replace its predicate."""
import resource
def install(Owned,c):
 original=Owned.rss
 def rss(self):
  own=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
  child=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
  try:return original(self)
  except BaseException:
   # Bounded best-effort evidence; any recording error cannot mask the original.
   value=dict(schema='deltalog.actual-host-child-rss-failure/v1',host_peak_rss_kib=own,child_peak_rss_kib=child,aggregate_peak_rss_kib=own+child,original_limit_kib=512*1024,original_gate_unchanged=True,cid=self.cid,stage=str(self.out),qualification=False)
   try:c.write(self.out/'HOST-CHILD-RSS-FAILURE.json',value)
   except BaseException:pass
   raise
 Owned.rss=rss
