"""Exact existing source/DSO/raw evidence; no numerical admission."""
import hashlib,importlib.util,json,time
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):n+=len(b);h.update(b)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
 p=Path(r['path']);need(set(r)=={'path','bytes','sha256'}and p.is_absolute()and not p.is_symlink()and ref(p)==r,'exact Ref3');return p
def obj(r):return json.loads(checked(r).read_bytes())
def write(p,v):
 with Path(p).open('x',encoding='utf8')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
def load(r,name):
 s=importlib.util.spec_from_file_location(name,checked(r));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def source(sr):
 m=obj(sr);need(m['schema']=='deltalog.lifecycle-kernel-source/v007'and m['root']==str(Path(__file__).resolve().parent)and m['default_enabled']is False and m['diagnostic040']is True,'actual040 defaultOFF source')
 for r in [*m['files'].values(),*m['dependencies']]:checked(r)
 need(m['saved_raw_ref']['bytes']==151267875 and m['saved_raw_ref']['sha256']=='6057c3726a57f778116e8dd1ff7eef6e2aed9c7d4c4213f286c21d18be58171b','only actual R4 whole B16step80 frame')
 fixture=obj(m['actual035_source_ref'])['files']['qwen36_deltalog_fresh/native_fixture.py'];need(fixture==m['fixture_source_ref'],'actual035 fixture conv provenance');text=checked(fixture).read_text();need('state["conv"]=conv'in text and 'before={k:v.cpu() for k,v in state.items()}'in text,'actual fixture captures all seven state fields');
 old=obj(m['actual016_source_ref']);need(all(old[k]==m[k]for k in('debug_build_ref','debug_kernel_source_ref','debug_library'))and old['libraries']['key_projection']==m['production_ref'],'actual016 bound library chain')
 build=obj(m['debug_build_ref']);need(build['schema']=='deltalog-readout-sidecar-actual-build/v015'and build['primary']is None and build['source_manifest']==m['debug_kernel_source_ref']and len(build['artifacts'])==1 and build['artifacts'][0]['library']==m['debug_library'],'real unchanged015 build/source/DSO')
 need(m['production_ref']['bytes']==2332672 and m['production_ref']['sha256']=='298749129c8586ecea56cb6076c435631b6fbef4b4e7757636ff87a4ec09abf7'and m['debug_library']['sha256']=='0d3400929262a16f6485cebc3fcf7e683fbff335af193df4754875091b915e2c','frozen actual peers')
 need(ref(Path(m['root'])/'proof015/kernel/SOURCE_MANIFEST.json')['sha256']==m['debug_kernel_source_ref']['sha256'],'copied015 exact actual build source')
 inverse=load(m['files']['proof015/verify_inverse.py'],'_040_original015_inverse');rows=inverse.verify(Path(m['root'])/'proof015')
 original=obj(m['files']['proof015/B010_ORIGINAL_SOURCE.json']);kernel=obj(m['original_kernel_source_ref']);need(original['files']==kernel['files']and len(rows)==8,'all eight actualB010 source files recovered, not a different operator')
 failed=obj(m['failed160_owner_ref']);need(failed['primary']is not None and failed['target_source']==m['actual035_source_ref'],'retained actual failed160, not success admission')
 return m
def admissions(m,ar,meta,numeric):
 a=obj(ar);need(ar==m['authority_ref']and a['cutoff_epoch']==1792135097 and 1791962297<=time.time()<1792135097-3060,'original fixed authority/budget, not extended')
 return dict(authority=ar,scope='single saved-frame diagnostic ONLY',old160_failed=m['failed160_owner_ref'],qualification=False)
