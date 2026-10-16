"""Exact003/013 ready evidence, no invented algorithm qualification."""
import importlib.util,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def obj(r):need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'exact Ref3');return json.loads(Path(r['path']).read_bytes())
def admission(m,nr,cr):
 ps=m['plugin_source'];pm=obj(ps);r=pm['files']['qwen36_deltalog_service/admission.py'];need(ref(r['path'])==r,'exact003 validator')
 s=importlib.util.spec_from_file_location('_dl004_003_admission',r['path']);A=importlib.util.module_from_spec(s);s.loader.exec_module(A);a,plugin=A.consume(ps,nr,cr)
 values=[ps,*pm['files'].values(),nr,cr,*plugin['_component_readset']]
 seen={}
 for r in values:need(ref(r['path'])==r,'complete ready readset');seen[r['path']]=r
 return dict(admission=a,readset=list(seen.values()),performance_ready=False)
def gate(nr):
 m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes());need(m['numeric_owner_ref']==nr and m['default_enabled']is False,'exact bound real013 numericRef')
 return admission(m,nr,m['CPU_owner_ref'])
