"""Bind real inputs only; no future numeric/model/performance PASS invented."""
import argparse,importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from qwen36_deltalog_screen import admission as A
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--configuration-ref',required=True);a=p.parse_args();cr=json.loads(a.configuration_ref);cfg=A.obj(cr)
 A.need(cfg['schema']=='deltalog.production-screen-binding-inputs/v037','actual input binding, not a qualifier')
 m=dict(cfg,configuration_ref=cr,schema='deltalog.production-screen-source/v037',root=str(P),window=dict(start=1791962297,cutoff=1792135097),default_enabled=False,mode='performance-screen-only',prepared_only=False,READY=False,performance_qualified=False)
 m['files']={f.relative_to(P).as_posix():A.ref(f)for f in P.rglob('*')if f.is_file()and (f.suffix in('.py','.txt')or f.name in('METADATA','DOMAIN_PINS.json'))and '__pycache__'not in f.parts}
 for key in('library_ref','composite_api_ref','composite_source_ref','composite_certificate_ref','composite_cpu_owner_ref','production_build_ref','diagnostic_predecessor_ref','model_smoke_api_ref','model_smoke_pins_ref','validation_inputs_ref'):
  A.need(A.ref(m[key]['path'])==m[key],'actual closed binding input '+key)
 for r in m['dependencies']:A.need(A.ref(r['path'])==r,'all actual external dependencies')
 A.need(m['model_smoke_api_ref']==A.ref(P/'receivers/model_smoke_receipt.py')and m['model_smoke_pins_ref']==A.ref(P/'receivers/DOMAIN_PINS.json'),'only new source-ownedMODEL036 receiver and final035 pins')
 spec=importlib.util.spec_from_file_location('_pf037_source_bind_model_receipt',m['model_smoke_api_ref']['path']);api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
 from types import SimpleNamespace
 def checked(r):A.need(A.ref(r['path'])==r,'actual source-bound model dependency');return Path(r['path'])
 C=SimpleNamespace(obj=A.obj,checked=checked,need=A.need)
 receipt=api.consume(C,m['model_smoke_plan']);A.need(receipt['schema']=='deltalog.actualMODEL036R5-model-diagnostic-smoke/v037-repair5'and receipt['selected_numeric_pass']is True,'actual035160 plus realMODEL036 smoke required before binding PF037R5')
 A.need(m['diagnostic_predecessor_ref']==m['model_smoke_plan']['production_source_ref'],'same original023R1 finite-domain predecessor')
 owner=A.obj(m['model_smoke_plan']['qualification_ref']);inputs=A.obj(m['validation_inputs_ref'])
 A.need(inputs['producer_ref']==owner['result']and inputs['source031_ref']==m['model_smoke_plan']['bridge_source_ref'],'same actual035 full160 source/raw for separate production finite NPU comparison')
 m['model_smoke_receipt']=receipt
 # The actual023 mathematical/CPU-metadata predecessor is part of the source
 # closure, not an optional broad mount guessed after reserving hardware.
 previous=A.obj(m['diagnostic_predecessor_ref']);dependencies={r['path']:r for r in m['dependencies']}
 for r in [m['diagnostic_predecessor_ref'],*previous['files'].values()]:
  A.need(A.ref(r['path'])==r,'actual023 predecessor closure');dependencies[r['path']]=r
 for r in api.closure(C,m['model_smoke_plan']):checked(r);dependencies[r['path']]=r
 m['dependencies']=list(dependencies.values())
 out=P/'SOURCE_MANIFEST.json';A.need(not out.exists(),'new one-shot immutable source')
 with out.open('x',encoding='utf8')as f:json.dump(m,f,sort_keys=True,allow_nan=False);f.write('\n')
 print(json.dumps(dict(source=A.ref(out),qualification=False,NPU=False)))
if __name__=='__main__':main()
