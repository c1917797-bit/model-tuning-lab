"""Thin022 source contract for the unchanged019 CPU controller."""
import hashlib,importlib.util,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
 p=Path(r['path']);need(set(r)=={'path','bytes','sha256'}and p.is_absolute()and not any(x.is_symlink()for x in(p,*p.parents))and ref(p)==r,'exact ordinary Ref3');return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,name):
 s=importlib.util.spec_from_file_location(name,checked(r));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def source(sr):
 m=obj(sr);need(m['schema']=='deltalog.composite-source/v022'and m['root']==str(ROOT)and m['default_enabled']is False and m['prepared_only']is False,'bound022 same root/defaultOFF')
 for r in [*m['files'].values(),*m['diagnostic_input_refs']]:checked(r)
 return m
def admissions(m,authority_ref,meta_ref,numeric_ref):
 need(authority_ref==m['authority_ref']and authority_ref['sha256']=='71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99','exact current authority');a=obj(authority_ref)
 need(a['cutoff_epoch']==1792135097 and 1791962297<=time.time()<1792135097-810,'720s owner+90s cleanup within frozen window')
 # No borrowed old numeric007 PASS: this CPU stage ONLY computes new composite.
 need(meta_ref is None and numeric_ref is None,'no obsolete component gate donors')
 return dict(authority=authority_ref,composite_pending=True,NPU=False)
