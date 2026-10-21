"""Default-OFF exact actual metadata assembly for the finite CPU diagnostic."""
import argparse,ast,hashlib,json,os,resource,subprocess,sys,time
from pathlib import Path
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
PACKET=Path(__file__).resolve().parent
def ref(p):
 p=Path(p);s=p.stat();h=hashlib.sha256();n=0
 with p.open('rb')as f:
  z=os.fstat(f.fileno());assert(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)
  for b in iter(lambda:f.read(2**20),b''):h.update(b);n+=len(b)
  q=os.fstat(f.fileno())
 a=p.stat();assert(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(q.st_dev,q.st_ino,q.st_size,q.st_mtime_ns)==(a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def obj(r):
 assert ref(r['path'])==r;return json.loads(Path(r['path']).read_bytes())
def write(p,v):
 with Path(p).open('x')as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
 return ref(p)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true');a=p.parse_args()
 if not a.prepare:print('{"enabled":false,"resources_admitted":false}');return 0
 os.sched_setaffinity(0,{166});_,hard=resource.getrlimit(resource.RLIMIT_AS);assert hard==resource.RLIM_INFINITY;resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
 ir=dict(path='/opt/host/vnf/austinov/bole-native-ar-fia-control-v2/INPUTS.json',bytes=15602,sha256='767c1e9209805f1f9eed6a6861482254ae884656e7747674a69dfa82eda1bb92')
 y=obj(ir);m=obj(y['AR_source']);old=obj(y['original_fsum_inputs']);num=obj(old['original_NUMdiag_inputs']);original=obj(num['original_numeric_inputs'])
 original_root=Path('/opt/host/vnf/austinov/run-bole-native-ar-fia-v2')
 mapping_ref=ref(original_root/'SOURCE-MAPPING.json');mapping=obj(mapping_ref)
 copy_ref=ref(T/'native_ar_map_diagnostic_v1/TORCH_IMPORT_SOURCE_COPY.json');copy=obj(copy_ref)
 assert copy['schema']=='bole.stopped-owned-image-exact-import-source-copy/v1'and copy['read_only_copy']is True and copy['resources_started']is False and copy['NPU']is False
 assert copy['before']['exit_code']==copy['copy']['exit_code']==copy['after']['exit_code']==0
 assert ref(copy['host_ref']['path'])==copy['host_ref']
 projections={}
 def pair(a,b):
  assert(a['bytes'],a['sha256'])==(b['bytes'],b['sha256'])and ref(b['path'])==b
  key=(a['path'],a['bytes'],a['sha256']);row=dict(installed_ref=a,host_ref=b)
  assert key not in projections or projections[key]==row;projections[key]=row
 for path,row in mapping['installed_copies'].items():
  assert row['installed']['path']==path;pair(row['installed'],row['host'])
 pair(copy['installed_ref'],copy['host_ref'])
 assert len(mapping['installed_copies'])==25 and len(mapping['wheel_libraries'])==9 and len(projections)==26
 projection_ref=write(PACKET/'INSTALLED_HOST_PROJECTION.json',list(projections.values()))
 npuref=dict(path='/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/__init__.py',bytes=2435,sha256='a21f553fb9ac12f087cfdf0fb61a583be3c864d3785cff9920ec862f565d6072')
 imports=[dict(kind='module',name='torch',ref=copy['installed_ref']),dict(kind='module',name='torch_npu',ref=npuref),
  dict(kind='file',name='pair_contract',ref=m['files']['pair_contract.py']),
  dict(kind='file',name='_fia_metadata_frozen_math',ref=original['files']['derived_math_consumer.py']),
  dict(kind='file',name='_fia_metadata_frozen_diagnostic',ref=num['files']['numeric_diagnostic.py']),
  dict(kind='file',name='_fia_metadata_arena',ref=y['files']['arena_layout.py']),
  dict(kind='file',name='_fia_metadata_maps',ref=y['files']['library_maps.py'])]
 new_root=Path('/opt/host/vnf/austinov/bole-native-ar-map-control-v1');new_out=Path('/opt/host/vnf/austinov/run-bole-native-ar-map-v1')
 assert not new_root.exists()and not new_out.exists()
 diagnostic=dict(schema='bole.native-ar-map-identity-diagnostic-inputs/v1',default_enabled=False,diagnostic_seconds=600,
  files=dict(diagnostic=ref(PACKET/'map_identity_diagnostic.py'),library_maps=y['files']['library_maps.py'],metadata_cpu=y['files']['metadata_cpu.py']),
  imports=imports,library_name='_fia_metadata_maps',sys_path=[m['root']],
  source_refs=[ir,y['files']['replay_cpu_owner.py'],y['files']['replay_common.py'],copy_ref,copy['host_ref']],
  known_files=[dict(alias_ref=item['ref'],canonical_ref=None,ELF=None)for item in imports],
  output_dir=str(new_out/'cpu-preflight/map-identity'))
 diagnostic_ref=write(PACKET/'DIAGNOSTIC_TEMPLATE.json',diagnostic)
 unit='bole-native-ar-fia-20261020t154710z-v2.service'
 r=subprocess.run(['/usr/bin/systemctl','show',unit,'--property=Id,ActiveState,SubState,Result,ExecMainStatus,MainPID,ControlPID,Type,Restart'],capture_output=True,text=True,timeout=15)
 assert r.returncode==0;properties=dict(line.split('=',1)for line in r.stdout.splitlines());assert properties['MainPID']==properties['ControlPID']=='0'and properties['ExecMainStatus']=='3'and properties['Result']=='exit-code'
 unit_ref=write(PACKET/'ORIGINAL_V2_UNIT_TERMINAL.json',dict(schema='bole.actual-finite-unit-terminal/v1',observed_epoch=time.time(),properties=properties))
 old_result_ref=ref(original_root/'RESULT.json');v=obj(old_result_ref);assert v['primary']is not None and v['secondary']==[]
 predecessors=[ref(__file__),unit_ref,old_result_ref,mapping_ref,copy_ref,copy['cleanup_ref'],copy['owned_ref'],ref(T/'NATIVE_AR_FIA_V2_FAILURE_AUDIT.json')]
 for n in ['FIRST-FAULT.json']:
  f=original_root/n
  if f.is_file():predecessors.append(ref(f))
 for r in v['summary'].values():
  if isinstance(r,dict)and set(r)=={'path','bytes','sha256'}:predecessors.append(r)
 predecessors_ref=write(PACKET/'PREDECESSORS.json',predecessors)
 argv=[sys.executable,'-I','-B',str(PACKET/'prepare_map_owner.py'),'--prepare','--source-root',str(new_root),'--output-root',str(new_out),
  '--original-inputs-ref',json.dumps(ir),'--diagnostic-template-ref',json.dumps(diagnostic_ref),'--projection-ref',json.dumps(projection_ref),
  '--torch-host-copy-ref',json.dumps(copy['host_ref']),'--torch-copy-receipt-ref',json.dumps(copy_ref),'--v2-result-ref',json.dumps(old_result_ref),
  '--predecessors-ref',json.dumps(predecessors_ref)]
 start=time.monotonic();r=subprocess.run(argv,capture_output=True,text=True,timeout=600)
 er=write(PACKET/'ACTUAL_PREPARER_EXECUTION.json',dict(schema='bole.actual-native-ar-map-source-preparer-execution/v1',argv=argv,elapsed=time.monotonic()-start,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,NPU=False,resources_admitted=False,projection_count=26,unprojected_wheel_entries_not_silently_skipped=9))
 print(json.dumps(dict(execution_ref=er,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr)),flush=True);return r.returncode
if __name__=='__main__':raise SystemExit(main())
