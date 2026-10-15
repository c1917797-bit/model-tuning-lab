"""DL snapshots, not MXR labels. All health checks outside measured duration."""
SOFTWARE_CASES=21
def need(v,m):
 if not v:raise ValueError(m)
def startup_gate(rows,sr,qr):
 need(len(rows)==4 and len({x['pid']for x in rows})==4,'four actual DL workers')
 for row in rows:
  need(row['schema']=='deltalog.production-screen-worker/v033'and row['source_ref']==sr and row['qualification_ref']==qr,'same source/qualification')
  need(row['mode']=='performance-screen'and row['graph']is False and row['async_scheduling']is False and row['PDC']is False and row['tensor_capture']is False and row['native_peer']is False,'source-bound production screen scope')
  need(len(row['prefixes'])==48 and row['health']['all_finite']is True and row['health']['outside_timing']is True,'actual48 and whole-arm finite health')
  need(row['synchronization']is True and row['synchronization_outside_timing']is True and row['health']['synchronization_performed']is True,'actual NPU health synchronization truthfully recorded outside timing')
  need(bool(row['mapped_rows'])and row['library']['sha256']=='298749129c8586ecea56cb6076c435631b6fbef4b4e7757636ff87a4ec09abf7','actual B010 library')
  need(all(v['core_id']==row['actual_core_id']and v['self_id']>0 for v in row['prefixes'].values()),'actual instance/core binding')
 return True
