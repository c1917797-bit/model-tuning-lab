"""Cold aggregate software/CLI gate for the bounded continuous service packet."""
import argparse,json,os,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))

def main():
 parser=argparse.ArgumentParser(allow_abbrev=False)
 parser.add_argument('--source-audit',action='store_true');parser.add_argument('--software',action='store_true')
 a=parser.parse_args()
 if not(a.source_audit or a.software):print('{"enabled":false,"NPU":false}');return 0
 import sourceio as C,root_repeat_witness as RW
 m=C.obj(C.ref(P/'SOURCE.json'))
 C.need(m['default_enabled']is False and m['service_experiment']==dict(schema='bole.c1-service-prefix-experiment/v1',prefix=131,max_steps=3,max_output_tokens=4),'explicit bounded defaultOFF service source')
 for r in m['files'].values():C.checked(r)
 RW.cpu_preflight(C,m,P)
 if a.source_audit:print(json.dumps(dict(source_audited=True,NPU=False,actual_scheduler_executed=False)));return 0
 import unittest
 suite=unittest.defaultTestLoader.discover(str(P),pattern='test*.py',top_level_dir=str(P))
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 C.need(result.wasSuccessful()and result.testsRun==m['service_required_sameimage_software_cases'],'all original and new same-image software controls passed')
 env={k:v for k,v in os.environ.items()if not k.startswith('BOLE_')}
 cli=[]
 for name in('service_entry.py','host_service.py','service_client.py','consume_service.py','server090.py'):
  for mode in((),('--help',)):
   value=subprocess.run([sys.executable,'-I','-B',str(P/name),*mode],env=env,capture_output=True,text=True,timeout=25)
   C.need(value.returncode==0,'actual cold CLI '+name+repr(mode)+' '+value.stderr[-4000:])
   if not mode:C.need(json.loads(value.stdout)['enabled']is False,'actual defaultOFF CLI '+name)
   cli.append(dict(file=name,mode=list(mode),exit_code=value.returncode))
 sr=C.ref(P/'SOURCE_BOUND.json')
 from service_metadata import run as installed_metadata
 metadata=installed_metadata(sr)
 value=subprocess.run([sys.executable,'-I','-B',str(P/'consume_service.py'),
  '--validate-source','--source-ref',json.dumps(sr)],env=env,capture_output=True,text=True,timeout=40)
 C.need(value.returncode==0 and json.loads(value.stdout)['source_validated']is True,
        'actual independent reader complete source closure '+value.stderr[-4000:])
 for mode in('model','CPU'):
  output=m['output_root']+('-CPU'if mode=='CPU'else'')
  value=subprocess.run([sys.executable,'-I','-B',str(P/'host_service.py'),
   '--output-contract-only','--output',output],env=env,capture_output=True,text=True,timeout=25)
  C.need(value.returncode==0 and json.loads(value.stdout)==dict(output=output,NPU=False,contract_only=True),'actual complete owned output CLI')
 value=subprocess.run([sys.executable,'-I','-B',str(P/'host_service.py'),
  '--source-audit','--source-ref',json.dumps(sr)],env=env,capture_output=True,text=True,timeout=40)
 C.need(value.returncode==0 and json.loads(value.stdout)['NPU']is False,'actual complete source/readset CLI '+value.stderr[-4000:])
 print(json.dumps(dict(schema='bole.service-cold-aggregate-software/v1',source=sr,
  tests=result.testsRun,all_tests_passed=True,actual_cold_cli=cli,complete_readset_audited=True,
  actual_installed_metadata=metadata,
  NPU=False,actual_scheduler_executed=False,model_ready=False)))
 return 0

if __name__=='__main__':raise SystemExit(main())
