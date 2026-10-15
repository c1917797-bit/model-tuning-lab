"""Frozen reads/exclusive outputs and prior real paired admission; no Torch."""
import hashlib,importlib.util,json,time
from pathlib import Path
def need(x,m):
 if not x:raise ValueError(m)
def ref(p):
 p=Path(p);h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
 p=Path(r['path']);need(set(r)=={'path','bytes','sha256'}and p.is_absolute()and not p.is_symlink()and ref(p)==r,'exact Ref3');return p
def obj(r):return json.loads(checked(r).read_bytes())
def write(p,v):
 with Path(p).open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False)
def load(r,name):
 s=importlib.util.spec_from_file_location(name,checked(r));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def source(r):
 m=obj(r);need(m['schema']=='deltalog.lifecycle-kernel-source/v007'and m['root']==str(Path(__file__).resolve().parent)and m['default_enabled']is False,'current source/defaultOFF')
 for f in m['files'].values():checked(f)
 checked(m['probe_ref'])
 for r in m['correction_source_refs']:checked(r)
 need(set(m['libraries'])=={'key_projection'},'only opt-in independently named A arm')
 for f in m['libraries'].values():checked(f)
 checked(m['kernel_source_ref']);checked(m['build_owner_result_ref'])
 b=obj(m['build_ref']);need(b['primary']is None and b['source_manifest']==m['kernel_source_ref'] and b['schema']=='deltalog-key-projection-actual-build/v010'and m['libraries']=={x['arm']:x['library']for x in b['artifacts']},'actual006 complete build/library binding')
 d=obj(m['debug_build_ref']);need(d['schema']=='deltalog-readout-sidecar-actual-build/v015'and d['primary']is None and d['source_manifest']==m['debug_kernel_source_ref']and len(d['artifacts'])==1 and d['artifacts'][0]['arm']=='readout_sidecar_v015'and d['artifacts'][0]['library']==m['debug_library'],'actual debug015 build binding');checked(m['debug_library']);need(m['debug_kernel_source_ref']['sha256']==m['expected015_kernel_source']['sha256']and m['debug_kernel_source_ref']['bytes']==m['expected015_kernel_source']['bytes'],'actual exact015 source')
 return m
def admissions(m,authority_ref,meta_ref,numeric_ref):
 need(numeric_ref==m['numeric_ref']and meta_ref==m['meta_ref'],'exact actual0300/02fb predecessors, not borrowed PASS')
 a=obj(authority_ref);need(authority_ref['sha256']=='71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99'and a['cutoff_epoch']==1792135097 and 1791962297<=time.time()<1792135097-3060,'fixed cutoff/remaining budget')
 meta=obj(meta_ref);need(meta['schema']=='deltalog-pair.actual-ABI-preflight/v007'and meta['source']['sha256']=='896e030385ce9ff48ccaf9c194b4401a42a10a3522c6d824227595b65bb93045'and meta['pass_gate']is True and meta['NPU']is False,'actual007 Meta child Ref')
 n=obj(numeric_ref);need(n['schema']=='deltalog-pair.actual-owned-host-stage/v007'and n['pair_gate_pass']is True and n['primary']is None and not n['secondary']and n['stopped_retained']is True,'actual007 qualified numeric/release, not borrowed futurePASS')
 need(n['target_source']==meta['source']and n['authority']==authority_ref and n['physical']==[5],'same source/clock/physical')
 c=obj(n['independent_consumer']);need(c['pass_gate']is True and c['NPU']is False,'independent original pair consumer')
 return dict(authority=authority_ref,meta=meta_ref,numeric=numeric_ref)
