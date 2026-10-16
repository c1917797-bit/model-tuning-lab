"""Shared host+worker shim for a NEW101 source, never edit original101R5."""
import importlib.util,sys
MODE='actual052-split-scale-diagnostic-only'
def api(C,m):
 sr=m.get('recovery_receiver_source_ref');C.need(type(sr)is dict,'reviewed recovery reader source missing')
 s=C.obj(sr);C.need(s['schema']=='deltalog.recovered-model-receiver-source/v128','exact recovered receiver schema')
 for r in s['files'].values():C.obj_file(r)
 r=s['files']['receiver128.py'];p=C.obj_file(r);old=list(sys.path)
 try:
  sys.path.insert(0,str(p.parent));spec=importlib.util.spec_from_file_location('_101_recovery128_shared',p);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 finally:sys.path[:]=old
 return v,sr
def admit(C,m):
 v,sr=api(C,m);return v.admit(C,m,m.get('recovery_model_plan_ref'),sr)
def closure(C,m):
 v,sr=api(C,m);return v.readset(C,m,m.get('recovery_model_plan_ref'),sr)
