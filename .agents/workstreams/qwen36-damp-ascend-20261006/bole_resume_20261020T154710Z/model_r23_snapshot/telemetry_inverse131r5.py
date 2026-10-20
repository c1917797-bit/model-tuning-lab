"""Test-only strict whole-byte inverse of reviewed R5 host telemetry to R4."""
import hashlib,json
BEFORE=(9878,'29da9e5bce1861261065676b1342ce1cfd2b8374177de0923884b7ad4a422b67')
AFTER=(11070,'c993b1f07d68770ea3de472ce788d5c987e4479275cd4c17889b322913b7ea46')

def identity(data):return len(data),hashlib.sha256(data).hexdigest()

def restore(body,plan_bytes,plan_ref):
    if identity(plan_bytes)!=(plan_ref['bytes'],plan_ref['sha256']):raise ValueError('exact source-owned telemetry inverse plan')
    plan=json.loads(plan_bytes)
    if plan['schema']!='bole.reviewed-host-telemetry-inverse/v131r5' or identity(body)!=AFTER:raise ValueError('exact complete R5 host before inverse')
    if (plan['before_host_ref']['bytes'],plan['before_host_ref']['sha256'])!=BEFORE or (plan['after_host_ref']['bytes'],plan['after_host_ref']['sha256'])!=AFTER:raise ValueError('exact reviewed R4/R5 host identities')
    text=body.decode('utf8')
    for old,new in reversed(plan['edits']):
        if text.count(new)!=1:raise ValueError('one exact telemetry edit inverse')
        text=text.replace(new,old)
    data=text.encode('utf8')
    if identity(data)!=BEFORE:raise ValueError('whole inverse must equal actual R4 host bytes')
    return data
