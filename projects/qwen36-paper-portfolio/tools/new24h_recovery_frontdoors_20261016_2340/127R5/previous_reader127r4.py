"""Exact actual failed reader provenance, never a successful owner alias."""
ROOT='/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/run-anchor-recovery127repair3-MAIN-20261016-NEW24H-001'
def r(path,n,h):return dict(path=path,bytes=n,sha256=h)
REFS={
 'owner':r(ROOT+'/RESULT.json',1381,'e837b54fd0c9b5fe89d3c6afa16425e1e4b969d0a6b6bd794fc490a20a3bf700'),
 'child':r(ROOT+'/native/result/CHILD127.json',3028,'537b1cfdc8e1d4419aae61455bb3eafeaad9a4f854355a3810b6cc0621f3c61c'),
 'logs':r(ROOT+'/native/actual-container-logs.json',3956,'db80f532e397b2ab36f32c3d3807c58c7df8334f7e2bf54f5ae83cf4e207fbc2'),
 'cleanup':r(ROOT+'/native/cleanup-verdict.json',356,'c253037a3574065ac8221ed6386f227a6fa75862ed57d10ae219b0e73a91b2df'),
 'source':r('/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-anchor-consumer-recovery-new24h-v1-127-repair3/SOURCE_MANIFEST.json',38304,'3875d7db6b641b8d934454a827a775c5e34d6eaf4185eba8485c31742a884e88')}
def validate(obj,producer_source):
 owner,child,logs,cleanup,source=[obj(REFS[k])for k in('owner','child','logs','cleanup','source')]
 if owner['schema']!='deltalog.fresh-bridge-owned-host/v5'or owner['source']!=REFS['source']or owner['target_source']!=REFS['source']or owner['stage']!='cpu'or owner['NPU']is not False or owner['result']is not None or owner['stopped_retained']is not True:raise ValueError('preserved exact failed R3 CPU reader')
 if owner['primary']!="ValueError('new48h authority cutoff/cleanup reserve exhausted')"or source['producer_source']!=producer_source:raise ValueError('failed reader source/clock category unchanged')
 text=__import__('json').dumps(child,sort_keys=True)
 if 'TimeoutExpired'not in text or '585.6111058300012'not in text:raise ValueError('actual earlier reader585.611 timeout')
 # Deliberately do NOT relabel old cleanup false, secondary or parent success.
 return dict(owner=REFS['owner'],source=REFS['source'],child=REFS['child'],logs=REFS['logs'],cleanup=REFS['cleanup'],old_failure_unchanged=True)
