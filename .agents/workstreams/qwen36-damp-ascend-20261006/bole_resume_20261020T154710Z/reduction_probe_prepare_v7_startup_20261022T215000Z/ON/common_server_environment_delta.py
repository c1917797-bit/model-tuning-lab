"""Pure server-entry common HCCL opt-in renderer; no live source or env change."""
import argparse
import ast
import hashlib
import json

ORIGINAL_BYTES=4168
ORIGINAL_SHA256='e69c2e7634598153183d3456c42d97dc7b526db37f960bbc1e4ca8a6b59873e1'
BEFORE=b" arm=m.get('performance_arm')\n if m.get('observation_only_profile') is not None:"
AFTER=b""" arm=m.get('performance_arm')
 common=m.get('common_collective_configuration')
 if common is not None:
  C.need(performance is not None and arm in ('native_ar','bole') and common==dict(
   schema='bole.common-collective-configuration/v1',hccl_deterministic='true',
   applies_to=['native_ar','bole']),'explicit matched common HCCL source contract')
  C.need(e.get('HCCL_DETERMINISTIC') in (None,'true'),'conflicting incoming HCCL mode')
  e['HCCL_DETERMINISTIC']='true'
 if m.get('observation_only_profile') is not None:"""

def need(value,why):
    if not value:
        raise ValueError(why)

def render(body,enable=False):
    need(type(body) is bytes and (len(body),hashlib.sha256(body).hexdigest())==
         (ORIGINAL_BYTES,ORIGINAL_SHA256),'exact whole actual V5 server entry')
    need(type(enable) is bool,'explicit boolean source-variant selection')
    if not enable:
        return body
    need(body.count(BEFORE)==1 and AFTER not in body,'one source-owned prebranch seam')
    changed=body.replace(BEFORE,AFTER)
    need(changed.count(AFTER)==1 and changed.replace(AFTER,BEFORE)==body,
         'exact whole inverse source bytes')
    def functions(raw):
        return {n.name:ast.dump(n,include_attributes=False)for n in ast.parse(raw).body
                if isinstance(n,ast.FunctionDef)}
    a,b=functions(body),functions(changed)
    need(set(a)==set(b) and {k for k in a if a[k]!=b[k]}=={'environment'},
         'only API environment resolver changes; original main/order unchanged')
    return changed

def inverse(changed):
    need(type(changed) is bytes and changed.count(AFTER)==1,'one enabled source delta')
    original=changed.replace(AFTER,BEFORE)
    need(render(original,True)==changed,'exact reviewed inverse')
    return original

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.parse_args()
    print(json.dumps(dict(enabled=False,source_rendered=False,NPU=False,
                          live_environment_modified=False,numerical_qualified=False)))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
