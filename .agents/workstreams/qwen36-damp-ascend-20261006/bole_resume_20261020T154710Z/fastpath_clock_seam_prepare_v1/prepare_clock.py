"""Independent source-only successor of short8. Never materializes/binds/approves."""
import copy
import hashlib
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import qualification_clock_delta as CLOCK


def once(text,a,b):
    if text.count(a)!=1:raise ValueError('exact clock preparation operand '+a[:80])
    return text.replace(a,b,1)


def render(*,authority_ref=None):
    stable=HERE.parent/'fastpath_numeric_bridge_prepare_v1'
    sys.path.insert(0,str(stable))
    import qualification_short_prepare as Q
    parent=Q.render(base_root=HERE,authority_ref=authority_ref)
    files=CLOCK.apply(parent['files'])
    text=files['qualification_short_prepare.py'].decode()
    text=once(text,'import qualification_tap_delta as TAP','import qualification_tap_delta as TAP\nimport qualification_clock_delta as CLOCK')
    text=once(text,"         'qualification_parent_renderer.py',","         'qualification_parent_renderer.py','qualification_clock_delta.py',")
    text=once(text,'    for n in HELPERS:files[n]=(HERE/n).read_bytes()',
              '    files=CLOCK.apply(files)\n    for n in HELPERS:files[n]=(HERE/n).read_bytes()')
    files['qualification_short_prepare.py']=text.encode()
    files['qualification_clock_delta.py']=(HERE/'qualification_clock_delta.py').read_bytes()
    v=files['qualification_source_validate.py'].decode()
    v=once(v,"    read_ref(m['files']['qualification_tap_delta.py'])",
           "    read_ref(m['files']['qualification_tap_delta.py'])\n    read_ref(m['files']['qualification_clock_delta.py'])")
    files['qualification_source_validate.py']=v.encode()
    m=copy.deepcopy(parent['manifest']);root=Path(m['root'])
    old={r['path']:(n,r)for n,r in m['files'].items()}
    m['files']={n:dict(path=str(root/n),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())for n,b in files.items()}
    def rebase(x):
        if type(x)is dict:
            if set(x)=={'path','bytes','sha256'}and x['path']in old:
                n,previous=old[x['path']]
                if x!=previous:raise ValueError('exact pre-clock Ref')
                return dict(m['files'][n])
            return {k:rebase(v)for k,v in x.items()}
        if type(x)is list:return [rebase(v)for v in x]
        return x
    for key in('dependencies','service_runtime_source_snapshots','performance_timing_donor','performance_streaming_client'):
        m[key]=rebase(m[key])
    changed={n:dict(before=parent['files'].get(n),after=b)for n,b in files.items()
             if n not in parent['files']or parent['files'][n]!=b}
    for n,b in files.items():
        if n.endswith('.py'):compile(b,n,'exec')
    return dict(manifest=m,files=files,parent=parent,delta=changed,prepared_only=True,
        execution_ready=False,actual_bound_validated=False,NPU=False)


def inverse(bundle):
    actual=dict(bundle['files']);parent=bundle['parent']['files']
    changed={n for n,b in actual.items()if n not in parent or b!=parent[n]}
    if changed!=set(bundle['delta']):raise ValueError('all clock successor deltas present')
    for n in changed:
        d=bundle['delta'][n]
        if actual[n]!=d['after']:raise ValueError('actual clock delta successor')
        if d['before']is None:actual.pop(n)
        else:actual[n]=d['before']
    if actual!=parent:raise ValueError('full source clock inverse')
    return actual


if __name__=='__main__':
    import json
    if sys.argv[1:]!=['--check']:raise SystemExit('default OFF: source-only --check')
    b=render();inverse(b)
    print(json.dumps(dict(files=len(b['files']),changed=sorted(b['delta']),prepared_only=True,
        execution_ready=False,actual_bound_validated=False,NPU=False),sort_keys=True))
