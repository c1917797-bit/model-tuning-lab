"""Thin explicit022 component API boundary; NEVER claims model admission."""
import hashlib,importlib.util,json,time
from pathlib import Path
from . import contract as C
ROOT=Path(__file__).resolve().parent.parent
def need(v,m):
 if not v:raise RuntimeError(m)
def ref(p):
 p=Path(p);need(p.is_absolute()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary immutable Ref path');b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'exact Ref3');return json.loads(Path(r['path']).read_bytes())
def source(sr):
 m=obj(sr);need(m['schema']=='deltalog.real-qwen-service-bridge-source/v023'and m['root']==str(ROOT)and m['default_enabled']is False and m['mode']=='diagnostic-bridge-only'and m['prepared_only']is False,'new independently frozen runtime source')
 need(m['window']==dict(start=1792134133,cutoff=1792220533)and 1792134133<=time.time()<1792220533,'unchanged fixed clock')
 for r in m['files'].values():need(ref(r['path'])==r,'whole actual023 closure')
 return m
def certificate(c,cr,library,schema):
 need(c['schema']=='deltalog.composite-component-qualification/v022'and c['source']==cr,'real022 typed component scope')
 for key in('strict324','original_numeric325','strict325_composed','old002_failure_unchanged'):
  need(c[key]is True,'complete strict composite component '+key)
 need(type(c['strict137_join'])is dict and c['strict137_join']['actual_tensor_join']is True,'actual guarded/raw bytejoin, not a fabricated Boolean')
 need(c['original019_strict_pass']is False,'old019 failure remains unchanged')
 for key in('model_ready','performance_ready','task_ready','graph','PDC'):need(c[key]is False,'component cannot authorize '+key)
 need(c['library']==library and c['operator_schema']==schema,'same actual production library/schema')
 return c
def consume(sr,composite_source_ref):
 m=source(sr)
 need(composite_source_ref==m['composite_source_ref'],'old state-ABI provenance source remains explicit')
 from . import split_qualification as Q
 class Reader:
  need=staticmethod(need)
  obj=staticmethod(obj)
  @staticmethod
  def obj_file(r):
   need(ref(r['path'])==r,'source/readset actual Ref3');return Path(r['path'])
 qualification=Q.admit(Reader,m)
 need(qualification['diagnostic_smoke_admitted']is True and qualification['model_ready']is False,'actual052160 permits diagnostic model load only')
 need(ref(m['library_ref']['path'])==m['library_ref'],'actual051 production library bytes')
 expected='qwen36_deltalog_split_scale_v051::decode(Tensor query, Tensor key, Tensor value, Tensor g, Tensor beta, Tensor(a!) base_state, Tensor(b!) k_log, Tensor(c!) u_log, Tensor(d!) lambda_log, Tensor(e!) cumulative_decay, Tensor(f!) log_length, Tensor actual_seq_lengths, Tensor state_indices) -> Tensor'
 need(m['operator_schema']==expected and C.NAMESPACE=='qwen36_deltalog_split_scale_v051','actual051 registered production schema, no debug model compute')
 return dict(schema='deltalog.actual-component-to-model-bridge/v053',runtime_source=sr,component_source=m['bridge024_source_ref'],actual052_qualification=qualification,component_only=True,model_ready=False,performance_ready=False,task_ready=False,graph=False,PDC=False),m
