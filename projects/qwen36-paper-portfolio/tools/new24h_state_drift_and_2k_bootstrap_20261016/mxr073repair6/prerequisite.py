"""Consume ACTUAL039, never manufacture a legacy solve gate or higher-scope PASS."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
START,CUT=1791916056,1792002456
LOW='/cache/cch/qwen36-paper-preparation-20261007/lowbit'
RUN=LOW+'/run-mxr-y16-single5-owned-main-R156_039_001'
SOURCE={'path':LOW+'/_draft_damp_operator_reuse/R156/mxr-diag16-defect-v1-037/SOURCE_MANIFEST.json','bytes':17260,'sha256':'a5642a92dfe0635b9ff7c84944935ea9cd88264061676b984efce10e37ffdb88'}
OWNER_SOURCE={'path':LOW+'/_draft_damp_operator_reuse/R156/mxr-diag16-numeric-binding-v1-039/SOURCE_MANIFEST.json','bytes':5319,'sha256':'9269c6c4732bf7800f209fd350b50642d232e75fae7b1919284e147f44eac08f'}
HOST={'path':RUN+'/RESULT.json','bytes':294133,'sha256':'5e126fd1412764ac47197cd99144f451417b92e0f6dde940e1f10ecbe623d03b'}
NUMERIC={'path':RUN+'/physical5/numeric/RESULT.json','bytes':242693,'sha256':'8b36505fe8b27a2468e1a98142745a98cbaf1abb2dc4b760274ce739ff9efcf4'}
BUILD={'path':LOW+'/run-mxr-y16-build-owned-main-R156_038_001/cpu/build/BUILD.json','bytes':327253,'sha256':'16a9e165cad0bff4f70817446facae514727e7f54d65509f3fc96e4f3b6b2b7a'}
ORIGINAL={'path':RUN+'/MAIN_ORIGINAL_OPERATION.json','bytes':6878,'sha256':'a654e585202512c1daa0d76e212131ee3715e9c29a34fc5265e14f307c13597f'}
DONOR={'path':LOW+'/_draft_damp_operator_reuse/R118/mxr-y16-serial-single5-numeric-owner-v1-031/host.py','bytes':11330,'sha256':'63687e5c1ba0ed33b3adc14e16cc767817a3384edde392d8c319a60a990858f4'}
CID='bc5f3ed3996490faadc481664b0eab30c4c0feabc3bcb8903c8b46db4194ceb7'
GUEST_BUILD_IDENTITIES={
 'compiler':dict(path='/usr/local/Ascend/cann-9.1.0/tools/bisheng_compiler/bin/bisheng',bytes=145696432,sha256='1cb33347c991d8ec143c0ba080ca126d9cc84167c4edea3e4953ff5865c5f60a'),
 'nm':dict(path='/usr/bin/aarch64-linux-gnu-nm',bytes=40312,sha256='8577d988ea43aaff6bb4255e34d32b60dd4eaadd99ac383418c79d3de12a8c6b')}
def build_guest_identities(b):
 # These are exact resolved executable identities observed by original build.py
 # INSIDE same660 Devices[]; they are not host artifact paths. Bind the two
 # specific registered fields to the pinned original BUILD and complete argv.
 need({k:b[k]for k in GUEST_BUILD_IDENTITIES}==GUEST_BUILD_IDENTITIES,'exact original guest compiler/nm identities')
 expected=['/usr/local/Ascend/ascend-toolkit/latest/bin/bisheng','-fPIC','-shared','-xcce','-DMEMORY_BASE','-O2','-std=c++17','-I/cache/cch/paper-sources/mxr-tri-inverse-20260918/extracted/megagdn-pto-d357fd38608f99ddf9b9fb2d217b2e731ecd3a72/kernels/pto/include','-I/cache/cch/paper-sources/mxr-tri-inverse-20260918/pto-isa-01666f3b386f296c95e6e05825fe63b8e6bb4ef4/include','--npu-arch=dav-2201',SOURCE['path'].rsplit('/',1)[0]+'/tri_inverse_y16.cpp','-o',b['library']['path']]
 need(b['argv']==expected and b['nm_argv']==['/usr/bin/nm','-D','--defined-only',b['library']['path']]and b['source']==SOURCE and b['Devices']==[]and b['NPU']is False,'registered actual compile and symbol-check commands; no path guessing')
 return [dict(location='BUILD.'+k,ref=b[k],view='recorded-same660-no-device-build-guest-binary',actual_original_build_ref=BUILD,host_filesystem_rehash_claimed=False)for k in GUEST_BUILD_IDENTITIES]
def need(v,m):
 if not v:raise ValueError(m)
def checked(r,empty=False):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and(r['bytes']>=0 if empty else r['bytes']>0),'strict actual Ref3')
 p=Path(r['path']);need(p.is_absolute()and p.is_file()and not p.is_symlink(),'ordinary exact original/source');b=p.read_bytes();need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'whole bytes');return b
def obj(r):return json.loads(checked(r))
def ref(p):
 b=Path(p).read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def load(r,name):
 checked(r);s=importlib.util.spec_from_file_location(name,r['path']);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def original_refs(value,location):
 if type(value)is dict:
  if set(value)=={'path','bytes','sha256'}:yield location,value
  else:
   for k,x in value.items():yield from original_refs(x,location+'.'+k)
 elif type(value)is list:
  for i,x in enumerate(value):yield from original_refs(x,location+'['+str(i)+']')
def reference_domains(h,n,b,raw,child,owned,cleanup,actual,inspected):
 guests=build_guest_identities(b);allowed={x['location']:x['ref']for x in guests};host=[];seen=set()
 for label,value in zip(('HOST','NUMERIC','BUILD','ORIGINAL','CHILD','OWNED','CLEANUP','ACTUAL_OWNER','AFTER_INSPECT'),(h,n,b,raw,child,owned,cleanup,actual,inspected)):
  for where,r in original_refs(value,label):
   if where in allowed:
    need(r==allowed[where],'registered guest identity not substituted');seen.add(where)
   else:
    need(type(r['path'])is str and r['path'].startswith(('/cache/','/opt/host/vnf/austinov/model-tuning-lab/')),'unregistered non-host Ref domain '+where);host.append(r)
 need(seen==set(allowed),'both registered guest binary fields present')
 return host,guests
def ownership(h,child,owned,cleanup,actual,inspected):
 need(child['exit_code']==0 and child['child_termination_observed']is True and child['primary_error']is None and child['expected_image_python_argv']==h['expected_child_argv']and child['physical_pid_proofs'],'actual exact owned matrix child')
 need(owned['cid']==CID and owned['source']==OWNER_SOURCE and owned['physical']==5 and actual['physical']==5 and CID in actual['cgroup']and actual['argv']==h['expected_child_argv'],'actual source/CID/PID argv binding')
 need(cleanup['container']==CID and cleanup['stopped']is cleanup['retained']is True and cleanup['deleted']is False and cleanup['errors']==[],'actual own stop-retain, not fresh execution authority')
 need(inspected['exit_code']==0 and inspected['requested_argv']==['/usr/bin/docker','inspect',CID],'exact afterinspect original')
 values=json.loads(inspected['stdout']);need(len(values)==1 and values[0]['Id']==CID and values[0]['State']['Running']is False and values[0]['State']['Pid']==0 and values[0]['State']['OOMKilled']is False and not values[0].get('ExecIDs'),'actual quiescent/noOOM retained container')
def metadata(h,n,b,raw):
 """This pure predicate alone grants NOTHING; consume additionally reads all artifacts."""
 root=raw.get('structuredContent',raw);op=root['operation'];record=op['result']['record']
 need(root['schema']=='agentweb.operation/v1'and root['operationId']=='exec-000000000000001e'and root['terminal']is True and root['phase']==root['status']=='completed'and root['succeeded']is True and op['routeDecision']=='peer_direct'and op['targetPeerId']=='lgw_fba5a82fcb8b4c1eb9c2ae2d1b87d61d'and op['fallbackUsed']is False,'real original terminal/direct route')
 blocks=[x for x in raw.get('content',[])if x.get('type')=='text']
 if blocks:need(len(blocks)==1 and json.loads(blocks[0]['text'])==root,'original text/structured exact semantic agreement')
 need(record['id']==root['operationId']and record['state']=='completed'and type(record['exitCode'])is int and record['exitCode']==0 and record['timedOut']is record['cancelled']is False and record['error']is None and record['stderr']=='','actual success no reconstructed terminal')
 need([record['command'],*record['args']]==h['actual_host_argv']and record['command']=='/usr/bin/python3'and record['args'][:3]==['-I','-B',OWNER_SOURCE['path'].rsplit('/',1)[0]+'/host.py']and record['cwd']=='/opt/host/vnf/austinov/model-tuning-lab','exact current039 original command')
 lines=record['stdout'].splitlines(keepends=True);marker='MAIN_MXR_Y16_SINGLE5_OWNER '
 need(len(lines)==1 and lines[0].startswith(marker)and lines[0].endswith('\n')and json.loads(lines[0][len(marker):])==HOST,'unique registered host marker and Ref')
 need(h['schema']=='mxr.y16.serial-single5-owned-numeric/v1'and h['source']==OWNER_SOURCE and h['target_source']==SOURCE and h['build_ref']==BUILD and h['numeric_ref']==NUMERIC and h['status']=='ACTUAL_CAPTURED4FRAME_GATE'and h['matrix_gate_pass']is True and h['primary']is None and h['secondary']==[]and h['physical']==[5]and(h['phase_seconds'],h['child_seconds'],h['cleanup_seconds'])==(300,120,90)and h['cleanup_spent']<=90 and h['elapsed_seconds']<=300,'actual complete039 scope/termination/budgets')
 need(n['schema']=='mxr.y16.actual-captured-frame-gate/v1'and n['source']==SOURCE and n['build_ref']==BUILD and n['plan_ref']==h['plan_ref']and n['actual_entry_argv']==h['expected_child_argv']and n['matrix_gate_pass']is True and n['primary']is None and n['secondary']==[]and n['original_rank2_failure_bitwise_reproduced']is True,'new actual numeric; original failure preserved')
 need(b['schema']=='mxr.y16.compensated-build/v1'and b['source']==SOURCE and b['status']=='compiled_no_device'and b['error']is None and b['secondary']==[]and b['Devices']==[]and b['NPU']is False and b['header_refs_before']==b['header_refs_after'],'actual037 build/header closure')
 need(h['source_hashes_before']==h['source_hashes_after']and n['source_hashes_before']==n['source_hashes_after'],'actual sourcebeforeafter')
 for value in(h,n):
  for key in('full_gdn_state_qualified','graph_qualified','model_ready','performance_ready','task_ready'):need(value[key]is False,'prior narrow scope must stay false')
 return record
def consume():
 h,n,b,raw=[obj(x)for x in(HOST,NUMERIC,BUILD,ORIGINAL)];metadata(h,n,b,raw)
 m=obj(SOURCE);owner=obj(OWNER_SOURCE);need(m['window']==owner['window']==dict(start=START,cutoff=CUT),'same exact current source window')
 D=load(DONOR,'_mxr042_actual031_verifier')
 C=type('Reader',(),{'load':staticmethod(obj),'read':staticmethod(lambda r:checked(r,True))})
 # REAL immutable031 verify body, including every full raw Ref, guards, inputs,
 # pointer/finite/repeat, native prerequisite and original .002/.02/.999 gate.
 D.verify(C,NUMERIC,SOURCE,BUILD,n['input_ref'],h['plan_ref'],h['expected_child_argv'])
 refs=[SOURCE,OWNER_SOURCE,HOST,NUMERIC,BUILD,ORIGINAL,DONOR,*m['files'].values(),*m['dependencies'].values(),*owner['files'].values(),*owner['dependencies'].values(),b['library'],*b['header_refs_after'].values()]
 for key in('child','plan_ref','owned','actual_owner','cleanup'):refs.append(h[key])
 for item in n['native_prerequisites']:refs.extend((item['result'],item['stdout']))
 for row in n['raw_outputs']:refs.append(row['raw'])
 unique={}
 for r in refs:checked(r,True);need(r['path']not in unique or unique[r['path']]==r,'unambiguous immutable readset');unique[r['path']]=r
 child=obj(h['child'])
 lines=checked(child['stdout_ref'],True).decode().splitlines(keepends=True);marker='MAIN_MXR_Y16_NUMERIC '
 need(len(lines)==1 and lines[0].startswith(marker)and lines[0].endswith('\n')and json.loads(lines[0][len(marker):])==NUMERIC,'exact registered numeric marker')
 checked(child['stderr_ref'],True)
 owned=obj(h['owned']);cleanup=obj(h['cleanup']);actual=obj(h['actual_owner'])
 inspected=obj(cleanup['after_inspect']);ownership(h,child,owned,cleanup,actual,inspected)
 host_refs,guest_identities=reference_domains(h,n,b,raw,child,owned,cleanup,actual,inspected)
 for r in host_refs:
  checked(r,True);need(r['path']not in unique or unique[r['path']]==r,'unambiguous complete original nested Ref');unique[r['path']]=r
 return dict(schema='mxr.diag16.actual039-short-prerequisite/v1',source=SOURCE,build=BUILD,owner_source=OWNER_SOURCE,owner_result=HOST,numeric=NUMERIC,original_operation=ORIGINAL,cleanup=h['cleanup'],library=b['library'],old_binary=m['dependencies']['old_binary'],author_root=m['author_root'],rank_order=[2,0,1,3],shape=[1,129,12,64],repeats=3,maximum_launches=36,original_rank2_failure_retained=True,readset=list(unique.values()),recorded_guest_build_identities=guest_identities,source_pins_preserved=True,full_gdn_state_qualified=False,graph_qualified=False,long32768_qualified=False,model_ready=False,performance_ready=False,task_ready=False)
def gate(r):
 value=obj(r);need(value['schema']=='mxr.diag16.actual039-short-prerequisite/v1','explicit new prerequisite, NEVERlegacyPASS');current=consume();need(value==current,'complete original039 consumption identity');return current
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--consume',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.consume:print(json.dumps(dict(enabled=False,NPU=False,model_ready=False)));return 0
 value=consume();need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists()and not a.output.is_symlink(),'MAIN sole new output file')
 with a.output.open('x',encoding='utf8')as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n')
 print('MAIN_MXR_DIAG16_PREREQUISITE '+json.dumps(ref(a.output)));return 0
if __name__=='__main__':raise SystemExit(main())
