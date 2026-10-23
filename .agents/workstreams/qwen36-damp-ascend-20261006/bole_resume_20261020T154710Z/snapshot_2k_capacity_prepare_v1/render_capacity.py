"""Exact two-file native-publication/private-scratch capacity repair. Source only."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole'
PARENT_IDENTITIES={"g2_contract.py":{"bytes":1746,"sha256":"f9e545876a0e922f22408d88c997195abd3ffb4f023b9b2954e168988f47de0a"},"service_runner.py":{"bytes":51175,"sha256":"730ff8d03824d5da0cbe960eb1f2e47dddabae22b282b610e2deee6fb8119d6a"}}
GEOMETRY=dict(path=str(HERE.parent/'fa_2k_geometry_prepare_v1/fa_native_geometry.py'),
    bytes=13677,sha256='405a1f46c7e2245fe0299581991e1f1d8d1234e94413ba4627f6e666787d24f3')

def need(v,s):
    if not v:raise ValueError(s)

CAPACITY="""

def capacity(length, allocated_kernel_pages, *, budget=MAX_OUTPUT, geometry=None):
    # Preserve the original131 function, domain and checks byte-for-byte.
    if type(length)is not int or length<2048:
        return _capacity_131(length,allocated_kernel_pages,budget=budget)
    import fa_native_geometry as NG
    live=NG.require(geometry)
    actual=live.check(length) # strong real C1 request/table/storage, never a JSON plan
    if type(budget)is not int or budget!=live.facts['output_tokens']:
        raise ValueError('same actual native2k output budget as bound prefill geometry')
    if type(allocated_kernel_pages)is not int or allocated_kernel_pages<=0 or allocated_kernel_pages!=actual['initial_kernel_pages']:
        raise ValueError('exact actual native2k allocated kernel count, not scratch count')
    native_pages=(length+2+127)//128
    scratch_pages=(length+3+127)//128
    if native_pages!=actual['publication_kernel_pages']or length+2>128*allocated_kernel_pages:
        raise ValueError('actual native root/accepted-child publication capacity insufficient')
    if scratch_pages!=actual['scratch_kernel_pages']or actual['KV_shape']!=(scratch_pages,1,128,256)or length+3>128*scratch_pages:
        raise ValueError('independent PRIVATE three-node scratch requirement')
    return dict(committed_length=length,native_publication_end_exclusive=length+2,
        private_end_exclusive=length+3,initial_kernel_capacity=128*allocated_kernel_pages,
        active_kernel_pages=native_pages,private_scratch_required_pages=scratch_pages,
        private_scratch_allocation_proven=False,physical_allocation_growth_proven=False)
"""

def adapt(original):
    out=dict(original)
    for n in('g2_contract.py','service_runner.py'):need(n in out,'actual snapshot/capacity source '+n)
    old='def capacity(length, allocated_kernel_pages, *, budget=MAX_OUTPUT):'
    text=out['g2_contract.py'].decode()
    scope_old='prefix=131, request_count=1, max_steps_per_request=output-1,'
    need(text.count(scope_old)==1,'exact source-only native2k stream prefix declaration')
    text=text.replace(scope_old,'prefix=2048, request_count=1, max_steps_per_request=output-1,',1)
    need(text.count(old)==1,'exact original G2.capacity function signature')
    text=text.replace(old,'def _capacity_131(length, allocated_kernel_pages, *, budget=MAX_OUTPUT):',1)
    out['g2_contract.py']=(text+CAPACITY).encode()
    text=out['service_runner.py'].decode()
    old='            G2.capacity(owner.length,len(pages))'
    need(text.count(old)==1,'exact real _snap capacity call')
    text=text.replace(old,"            G2.capacity(owner.length,len(pages),geometry=b.get('native_geometry'))",1)
    out['service_runner.py']=text.encode()
    for n,b in out.items():
        if n.endswith('.py'):compile(b,n,'exec')
    delta={n:dict(before=original[n],after=b)for n,b in out.items()if original.get(n)!=b}
    return dict(files=out,inverse_delta=delta,prepared_only=True,whole_source_ready=False,NPU=False)

def inverse(bundle):
    out=dict(bundle['files'])
    for n,d in bundle['inverse_delta'].items():
        need(out[n]==d['after'],'exact snapshot/capacity after bytes')
        out[n]=d['before']
    return out

def checked(path,identity):
    p=Path(path);need(p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary actual immutable source')
    raw=p.read_bytes()
    need(len(raw)==identity['bytes']and hashlib.sha256(raw).hexdigest()==identity['sha256'],'complete snapshot/capacity source identity')
    return raw

def parent():
    return {n:checked(PARENT/n,r)for n,r in PARENT_IDENTITIES.items()}

if __name__=='__main__':
    if not sys.argv[1:]:print(json.dumps(dict(enabled=False,whole_source_ready=False,NPU=False)))
    else:
        need(sys.argv[1:]==['--check'],'explicit source-only --check')
        p=parent();b=adapt(p);need(inverse(b)==p,'whole snapshot/capacity inverse')
        print(json.dumps(dict(changed=sorted(b['inverse_delta']),whole_source_ready=False,NPU=False)))
