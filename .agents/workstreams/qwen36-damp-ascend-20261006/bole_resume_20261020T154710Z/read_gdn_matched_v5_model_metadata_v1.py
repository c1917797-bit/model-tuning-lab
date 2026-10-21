
"""Read only original GDN MODEL384 numerical receipts, source and stopped owners."""
import argparse,hashlib,json,math,os,resource,sys
from pathlib import Path
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
R=Path('/opt/host/vnf/austinov/bole-gdn-g1-probe-matched-v5')
O=Path('/opt/host/vnf/austinov/run-bole-gdn-g1-probe-matched-v5')
SR=dict(path=str(R/'SOURCE_BOUND.json'),bytes=117604,sha256='f5308ea9d74e92293fd00a73f156a324fab064bfb2dcca3997728054deff4831')
RR=dict(path=str(O/'RESULT.json'),bytes=238251,sha256='8bad263436d441dd1e84d0147788bd9ff2d04ccf77cb86f55c8335e41d0b5bd0')
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);a=p.stat();h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b);n+=len(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and n==z.st_size,'stable complete streaming hash')
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)in({'path','sha256'},{'path','bytes','sha256'}),'exact Ref2/Ref3')
 a=ref(r['path']);need(a['sha256']==r['sha256']and('bytes'not in r or a['bytes']==r['bytes']),'whole exact evidence')
 return a
def obj(r):checked(r);return json.loads(Path(r['path']).read_bytes())
def save(p,v):
 with p.open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
 return ref(p)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 os.sched_setaffinity(0,{166});_,hard=resource.getrlimit(resource.RLIMIT_AS);resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
 m=obj(SR);v=obj(RR);cmd=obj(ref(R/'COMMANDS.json'))
 need(v['source']==SR and v['cpu_only']is False and v['primary']is None and v['secondary']==[]and v['source_before']==v['source_after']and len(v['source_before'])==732,'actual full current MODEL complete/source equality')
 need(v['actual_host_argv']==cmd['model'][8:]and v['phase_seconds']==3600 and v['cleanup_seconds']==180 and v['elapsed']<=3600 and v['cleanup_spent']<=180 and v['entry_clock_before_source_replay']is True and v['deadline_renewed']is False,'original exact model argv and clocks')
 need(m['gdn_service_extension']['mode']=='matched_original','actual matched-original numerical control')
 sys.path.insert(0,str(R));import sourceio as C,bind_model as B,command_contract as CC,gdn_probe_runtime as GP
 for n,module in [('sourceio.py',C),('bind_model.py',B),('command_contract.py',CC),('gdn_probe_runtime.py',GP)]:need(ref(module.__file__)==m['files'][n],'exact current metadata helper')
 sv=v['summary'];refs=B.readset(SR)+m['dependencies']+CC.validate(C,SR,m)+GP.host_readset(C,SR,m)+GP.handoff_readset(C,SR,m,sv['GDN_software'])
 before={r['path']:r['sha256']for r in refs};need(before==v['source_before'],'original full actual model source readset reconstructed')
 for path,sha in before.items():need(ref(path)['sha256']==sha,'each exact complete732 source input')
 refs.extend([SR,RR,ref(__file__),ref(R/'COMMANDS.json')])
 terminal_ref=ref(T/'GDN_MATCHED_V5_MODEL_SYSTEMD_TERMINAL.json');term=obj(terminal_ref);props=term['properties']
 need(props['Id']=='bole-gdn-matched-v5-model-20261020t154710z.service'and props['ActiveState']=='active'and props['SubState']=='exited'and props['Result']=='success'and props['ExecMainStatus']==props['MainPID']==props['ControlPID']=='0','actual terminal0 and both PIDs0')
 refs.append(terminal_ref);owners=[]
 for name in ('CPU_release','model_release','independent_release'):
  release_ref=checked(sv[name]);release=obj(release_ref)
  need(release['stopped']is True and release['retained']is True and release['deleted']is False and release['errors']==[],'every original owner stopped retained')
  after=checked(release['after_inspect']);raw=obj(after);need(raw['exit_code']==0,'original complete after-inspect');items=json.loads(raw['stdout']);need(len(items)==1,'one original owned inspect');i=items[0];st=i['State'];cfg=i['HostConfig']
  leaf=Path(release_ref['path']).parent;owned_ref=ref(leaf/'OWNED.json');own=obj(owned_ref)
  need(i['Id']==release['container']==own['cid']and i['Image']==own['image']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'and own['source']==SR,'source-bound original own image/CID')
  need(st['Running']is False and st['Pid']==0 and st['OOMKilled']is False and st['Status']=='exited'and not i.get('ExecIDs'),'original stopped PID0/noOOM/emptyExecIDs')
  mounts={a['Destination']:(a['Source'],a['RW'])for a in i['Mounts']}
  need(len(mounts)==len(i['Mounts'])and mounts=={k:tuple(z)for k,z in own['mounts'].items()},'all and only original exact saved mount closure')
  need(cfg['CpusetCpus']==','.join(map(str,own['guest_cpus']))and set(own['guest_cpus'])<={0,1,2,3,144,145}and cfg['NanoCpus']==len(own['guest_cpus'])*1000000000 and cfg['ReadonlyRootfs']is True and cfg['NetworkMode']=='none'and cfg['IpcMode']=='private'and cfg['CapDrop']==['ALL']and not cfg.get('CapAdd')and cfg['SecurityOpt']==['no-new-privileges'],'original bounded source-owned CPU/security profile')
  need(cfg['Memory']==cfg['MemorySwap']==(32 if name=='model_release'else 8)*2**30,'original per-role RAM/swap')
  if name!='model_release':need(cfg['Devices']==[]and len(own['guest_cpus'])==1,'Devices[] original CPU role')
  else:
   devices={a['PathInContainer']:(a['PathOnHost'],a['CgroupPermissions'])for a in cfg['Devices']}
   wanted={'/dev/davinci%d'%n:('/dev/davinci%d'%(n+4),'rwm')for n in range(4)}
   wanted.update({n:(n,'rwm')for n in('/dev/davinci_manager','/dev/devmm_svm','/dev/hisi_hdc')})
   need(len(devices)==7 and devices==wanted and len(own['guest_cpus'])==3,'only original four physical4..7 and three controls')
  create_ref=checked(own['create_receipt']);create=obj(create_ref);need(create['exit_code']==0 and create['stdout'].strip()==own['cid'],'original actual create receipt')
  refs.extend([release_ref,after,owned_ref,create_ref,*[checked(release[k])for k in('before_inspect','stop_receipt','release_smi')]])
  owners.append(dict(role=name,cid=own['cid'],after_inspect=after,stopped_retained=True,noOOM=True,PID=0,Devices=cfg['Devices']))
 need(len({x['cid']for x in owners})==3,'three distinct original model owners')
 for name in('CPU_child','actual_software_child','canary','independent_child','GDN_independent_child'):
  child=obj(sv[name]);need(child['exit_code']==0 and child['child_termination_observed']is True,'actual original child completed '+name)
  refs.extend([checked(sv[name]),checked(child['stdout_ref']),checked(child['stderr_ref'])])
 client=obj(sv['actual_client_terminal']);need(client['exit_code']==0,'original exact HTTP client complete')
 parser=obj(sv['CPU_report']);need(parser['source']==SR and parser['pass_preflight']is True and parser['Devices']==[]and parser['native_runtime_parser_checked']is True,'actual native CPU parser')
 Gate=GP.helper(C,m).load(C,m['files']['gdn_service_gate.py'],'_gdn_model_metadata_gate')
 x,H,replay,qualification=Gate.qualify(C,m,m['gdn_service_extension']['source'],SR,sv['GDN_software'])
 report=obj(sv['GDN_independent']);base=obj(sv['independent']);bundle=obj(base['inputs'])
 need(report['schema']=='bole.gdn3-service-independent/v1'and report['source']==SR and report['base_service_report']==sv['independent']and report['qualification']==qualification and report['extension']==m['gdn_service_extension']['source']and report['new_service_prefixes_pass']is True and report['actual_GDN_frames']==384 and report['completed_request_count']==2,'actual complete384 frame source-qualified original consumer report')
 for name in('model_ready','whole_model_qualified','E2E_measured','performance_ready','formal_success','NPU'):need(report[name]is False,'honest original limits')
 need(base['source']==SR and base['schema']=='bole.actual-c1-two-request-service-independent/v1'and base['completed_request_count']==2 and all(base[k]is True for k in('service_complete','component_checks_pass','actual_all4_retirement','actual_HTTP_output_token_ID_join','scheduler_committed_independently','independent_actual_target_TP4_vocabulary_join','independent_actual_MTP_TP4_vocabulary_join')),'actual complete original service/HTTP/retirement/native vocabulary report')
 need(bundle['source']==SR and len(bundle['ranks'])==len(base['ranks'])==len(report['ranks'])==4,'exact four-rank raw and independent results')
 count=0;rank_refs=[];captured=[]
 for rank,r in enumerate(report['ranks']):
  rankv=obj(r);base_rank=obj(base['ranks'][rank]);pair=bundle['ranks'][rank];receipt=obj(pair['receipt'])
  need(rankv['source']==base_rank['source']==receipt['source']==SR and rankv['receipt']==base_rank['receipt']==pair['receipt']and rankv['raw']==base_rank['raw']==receipt['raw']==pair['raw']and receipt['rank']==rank and receipt['primary']is None,'complete rank/source/raw/receipt joins')
  need(len(rankv['requests'])==len(base_rank['requests'])==2 and[g['generation']for g in rankv['requests']]==[1,2],'exact two original generations')
  for index,q in enumerate(rankv['requests']):
   br=base_rank['requests'][index]
   need(q['schema']=='bole.gdn3-service-independent-rank/v1'and q['rank']==rank and q['new_service_prefixes_pass']is True and q['base_component_checks_pass']is True and q['base_output_token_ids']==br['output_token_ids']and br['component_checks_pass']is True and len(q['rows'])==1,'all two requests original base and supplement agree')
   need(all(q[k]is False for k in('model_ready','native_AR_greedy_comparison_performed','E2E_measured','formal_success')),'no scope promotion')
   row=q['rows'][0];need(row['ordinal']==0 and[m['layer']for m in row['metrics']]==[i for i in range(64)if i%4!=3],'all48 original GDN layers in one actual root step')
   for metric in row['metrics']:
    need(metric['passed']is True and all(metric[k]['passed']is True for k in('O','P','U','selected')),'all original O/P/U/selected numerical gates passed')
    for key in('O','P','U','selected'):
     for n,a in metric[key].items():
      if type(a)in(int,float):need(math.isfinite(a)and a>=0,'finite nonnegative original numerical metric')
    count+=1
  rank_refs.append(checked(r));captured.extend([pair['raw'],pair['receipt'],base['ranks'][rank]])
 need(count==384,'no numerical frame sampling or missing late frames')
 load=Gate.load(C,m['files']['load_consumer114.py'],'_gdn_model_metadata_mtp_load')
 expected=load.consume([obj(r)for r in sv['MTP_load_receipts']],parser['actual_checkpoint_mtp_names'],m['installed_sources']['qwen_mtp'],m['files']['load_receipt111.py'])
 need(expected==obj(sv['MTP_load']),'original all-four MTP load consumer actually reexecuted')
 installed=tuple(m['runtime_sources'].values())+tuple(m['installed_sources'].values())+tuple(m.get('projection_runtime_refs',{}).values())
 refs.extend(GP.collect(C,[sv,report,base,bundle,rank_refs,captured],installed_refs=installed))
 need(not any(n=='torch'or n.startswith(('torch.','torch_npu','acl'))for n in sys.modules),'metadata-only independent reader imports no ML/NPU')
 unique={r['path']:checked(r)for r in refs}
 output=dict(schema='bole.GDN-matched-v5-MODEL-metadata-independent-qualification/v1',source=SR,result_ref=RR,reader_ref=ref(__file__),unit_terminal_ref=terminal_ref,source_readset_count=732,actual_sameimage240_pass=True,original_source_software_and_component_gate_reexecuted=True,original_all4_MTP_load_gate_reexecuted=True,original_service_HTTP_retirement_report_pass=True,actual_GDN_frames=count,all384_original_OPU_selected_metrics_metadata_pass=True,original_numerical_child_exit0=True,rank_reports=rank_refs,all_three_owners_stopped_retained=True,owners=owners,retained_refs=list(unique.values()),saved_stopped_metadata_only=True,current_live_identity_queried=False,raw_numerical_replayed=False,Torch_imported=False,NPU=False,mode='matched_original',candidate_qualified=False,whole_model_qualified=False,normal_EOS_qualified=False,model_ready=False,task_ready=False,performance_ready=False,formal_success=False)
 rr=save(T/'GDN_MATCHED_V5_MODEL_METADATA_READBACK.json',output)
 print(json.dumps(dict(qualification_ref=rr,source=SR,source_readset_count=732,retained_refs=len(unique),actual_GDN_frames=count,all_three_owners_stopped_retained=True,mode='matched_original',candidate_qualified=False,formal_success=False)));return 0
if __name__=='__main__':raise SystemExit(main())
