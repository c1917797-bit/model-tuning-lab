"""Persistent device-only validity flags; read only outside measured interval.

Invalid live arithmetic rejects the ENTIRE arm. This does not preserve the
diagnostic before-mutation exception policy on invalid inputs. Finite valid
inputs use exactly the same state arithmetic. Flags cannot be cleared/reused.
"""
_FLAGS={}
_OBSERVATIONS={}

def observe(torch,tensor):
 device=str(tensor.device)
 if device not in _FLAGS:
  _FLAGS[device]=torch.ones((),dtype=torch.bool,device=tensor.device)
  _OBSERVATIONS[device]=0
 valid=torch.isfinite(tensor).all()
 _FLAGS[device].logical_and_(valid)
 _OBSERVATIONS[device]+=1

def snapshot(torch,*,outside_timing=False):
 if outside_timing is not True:raise RuntimeError('health read prohibited inside timed core')
 if not _FLAGS:raise RuntimeError('no actual materialization/decode health observations')
 synchronized=any(flag.device.type=='npu' for flag in _FLAGS.values())
 if synchronized:torch.npu.synchronize()
 rows={device:dict(observations=_OBSERVATIONS[device],finite=bool(flag.item())) for device,flag in _FLAGS.items()}
 return dict(schema='deltalog.production-device-health/v033',rows=rows,all_finite=all(x['finite'] for x in rows.values()),outside_timing=True,synchronization_performed=synchronized)
