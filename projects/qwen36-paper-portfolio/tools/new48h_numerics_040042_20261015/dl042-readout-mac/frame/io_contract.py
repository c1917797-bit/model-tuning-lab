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
 old=obj(m['actual016_source_ref']);need(old['libraries']['key_projection']==m['baseline_ref'],'unchanged actual B010 baseline provenance')
 build=obj(m['new_build_ref']);need(build['schema']=='deltalog-readout-mac-actual-build/v042'and build['source_manifest']==m['new_kernel_source_ref']and build['primary']is None and build['Devices']==[]and build['NPU']is False,'actual042 source-bound twoDSO build')
 need([x['arm']for x in build['artifacts']]==['readout_mac042','readout_mac042_debug']and [x['library']for x in build['artifacts']]==[m['production_ref'],m['debug_library']],'actual new042 libraries, not oldB010 qualification')
 owner=obj(m['build_owner_ref']);need(owner['source']==m['build_owner_source_ref']and owner['primary']is None and owner['secondary']==[]and owner['NPU']is False,'actual new042 CPU build owner')
 cleanup=obj(owner['cleanup']);need(cleanup['stopped']is cleanup['retained']is True and cleanup['errors']==[],'actual build owner cleanup')
 v=load(m['inverse_ref'],'_042_inverse_runtime');need(len(v.verify(Path(m['root']).parent))==16,'one-factor inverse16')
 failed=obj(m['failed160_owner_ref']);need(failed['primary']is not None and failed['target_source']==m['actual035_source_ref'],'retained actual failed160, not success admission')
 return m
def admissions(m,ar,meta,numeric):
 a=obj(ar);need(ar==m['authority_ref']and a['cutoff_epoch']==1792135097 and 1791962297<=time.time()<1792135097-3060,'original fixed authority/budget, not extended')
 return dict(authority=ar,scope='single saved-frame diagnostic ONLY',old160_failed=m['failed160_owner_ref'],qualification=False)
