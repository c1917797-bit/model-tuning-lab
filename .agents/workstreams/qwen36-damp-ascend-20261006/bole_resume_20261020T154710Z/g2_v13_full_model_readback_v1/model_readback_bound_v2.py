"""Default-OFF full source13 MODEL metadata readback; no resource execution."""
import argparse,hashlib,importlib,importlib.util,json,math,os,re,stat,sys
from pathlib import Path
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
OUT=Path('/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v13')
SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13/SOURCE_BOUND.json',bytes=994678,sha256='545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345')
RESULT=dict(path=str(OUT/'RESULT.json'),bytes=1340078,sha256='e326a53f47c65aff4a498ac30da5568009c22e81cd9e469b2f46a28f086ebb67')
STAGE_READER=dict(path=str(T/'g2_v13_model_stage_readback_v1/model_stage_actual_v2.py'),bytes=60047,sha256='3f42803170271f2deca7917f415914f0337fc2204638dc588fc3e3ba1f7f00c0')
STAGE_PROOF=dict(path=str(T/'G2_V13_MODEL_STAGE_READBACK.json'),bytes=1729550,sha256='e1a324b5679e80c2fc9f18f41b2faa4e8f8c2d02c17281e744c302f1578d87ed')
UNIT=dict(path=str(T/'G2_V13_MODEL_SYSTEMD_TERMINAL_V2.json'),bytes=314,sha256='5e108eb1ff089e168f6f5193ec95c3a1d81c9cc052c307878ade92574a4b742a')
ATTRIBUTION=dict(path=str(OUT/'dense/receipts/STREAM/ATTRIBUTION.json'),bytes=66000,sha256='f78c53b8f8dd741cc6e94e892f8f2d283919ac3fa1fd061b83caaa72d544f46d')
OUTPUT=T/'G2_V13_MODEL_METADATA_READBACK.json'
AUXILIARY={'roles': {'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/g2_v13_full_model_readback_v1/model_owner_roles.py', 'bytes': 9693, 'sha256': '5b84965a8bbba18d114d38c1765f3879a06117c3aead990ec3caee38e90d64f4'}, 'protocol': {'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/g2_v13_full_model_readback_v1/metadata_protocol_v2.py', 'bytes': 9452, 'sha256': 'cc87c659a3c2deca4075ad3494d571dab1e94233950fe0beb010a4071ea506ae'}}
def need(value,message):
 if not value:raise ValueError(message)
def unique_object(pairs):
 value={}
 for key,item in pairs:need(key not in value,'duplicate JSON field '+key);value[key]=item
 return value
def strict_ref(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['path'])is str and Path(r['path']).is_absolute()and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and re.fullmatch('[0-9a-f]{64}',r['sha256']),'complete strict ordinary full Ref3');return r
def checked(r):
 strict_ref(r);p=Path(r['path']);st=p.lstat();need(stat.S_ISREG(st.st_mode)and not p.is_symlink(),'ordinary exact independent reader input');data=p.read_bytes();after=p.lstat()
 need((st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)and len(data)==r['bytes']and hashlib.sha256(data).hexdigest()==r['sha256'],'whole ordinary reader input bytes/SHA unchanged');return p
def full_ref(path):
 p=Path(path);st=p.lstat();need(p.is_absolute()and stat.S_ISREG(st.st_mode)and not p.is_symlink(),'ordinary absolute reader artifact');data=p.read_bytes();after=p.lstat()
 need((st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'reader artifact unchanged while hashing');return dict(path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
def module(r,name):
 need(name not in sys.modules,'fresh exact auxiliary module '+name);p=checked(r);spec=importlib.util.spec_from_file_location(name,p);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);need(full_ref(value.__file__)==r,'complete auxiliary source unchanged '+name);return value
def exact_source_module(R,m,name):
 r=m['files'][name+'.py'];R.checked(r);value=importlib.import_module(name);R.need(R.ref(value.__file__)==r,'actual original source-owned module '+name);return value
def no_accelerator_imports():
 need(not any(n=='torch'or n.startswith(('torch.','torch_npu','acl','numpy'))for n in sys.modules),'stdlib-only metadata reader; no ML/accelerator import')
def execute(sr,result_ref,unit_ref):
 need(sr==SOURCE and result_ref==RESULT and unit_ref==UNIT,'only actual fixed source13 successful MODEL and V2 unit')
 need(type(AUXILIARY)is dict and set(AUXILIARY)=={'roles','protocol'},'source-bound new helper pins pending; unbound source never qualifies')
 for r in(SOURCE,RESULT,UNIT,STAGE_READER,STAGE_PROOF,ATTRIBUTION,*AUXILIARY.values()):checked(r)
 no_accelerator_imports();R=module(STAGE_READER,'_g2_v13_actual_stage349_metadata_authority')
 need(R.SOURCE==SOURCE and R.RESULT==RESULT and R.UNIT_REF==UNIT and R.OUT==OUT and R.CPU_OUT==OUT,'actual bound MODEL-stage context, no CPU shadow assignment')
 m,mods,complete,commands,clock,snapshot=R.source_gate(SOURCE);R.need(len(complete)==4088,'actual complete source13 closed readset');stage=R.obj(STAGE_PROOF)
 R.need(stage['schema']=='bole.actual-G2-v13-MODEL-stage-independent-readback/v1'and stage['source']==SOURCE and stage['result_ref']==RESULT and stage['reader_ref']==STAGE_READER and stage['reader_source_before_after_equal']is True and stage['sameimage_349_parser_and_actual_cold_handoff_stage_pass']is True and stage['two_stage_CPU_helpers_stopped_retained']is True and stage['stage_only']is True and stage['numerical_model_qualification']is False and stage['model_ready']is False and stage['NPU']is False and stage['source_nonempty_before_after_equal']is True and stage['source_readset_count']==len(complete)and stage['firstentry_clock']==clock,'actual independent stage349 prerequisite, never math/model projection')
 R.need(type(stage['full_evidence_refs'])is list and stage['full_evidence_refs'],'complete actual stage349 readback evidence inventory')
 for r in stage['full_evidence_refs']:R.checked(strict_ref(r))
 unit=R.unit_gate(UNIT);result=R.obj(RESULT)
 R.need(result['schema']=='bole.actual-three-node-model-owned/v131'and result['source']==SOURCE and result['cpu_only']is False and result['primary']is None and result['secondary']==[]and result['source_before']and result['source_before']==result['source_after']==complete and result['phase_seconds']==3600 and result['cleanup_seconds']==180 and R.finite(result['elapsed'])and 0<=result['elapsed']<=3600 and R.finite(result['cleanup_spent'])and 0<=result['cleanup_spent']<=180 and result['actual_host_argv']==commands['model'][3:]and result['model_ready']is False and result['timing_is_formal']is False and result['formal_performance']is False and result['task_accuracy']is False,'actual complete successful original MODEL owner/source/argv/cold clock, diagnostic only')
 R.model_summary(result['summary']);summary=result['summary'];roles=module(AUXILIARY['roles'],'_g2_v13_exact_new_model_owner_roles');protocol=module(AUXILIARY['protocol'],'_g2_v13_exact_metadata_protocol')
 for r in(*AUXILIARY.values(),STAGE_READER,STAGE_PROOF,UNIT):R.checked(r)
 C=exact_source_module(R,m,'contract090');G1=exact_source_module(R,m,'g1_contract');G2=exact_source_module(R,m,'g2_contract');CH=exact_source_module(R,m,'g2_channel');O=exact_source_module(R,m,'identity_oracle');coverage=exact_source_module(R,m,'g2_coverage');no_accelerator_imports()
 c=R.module(m['g2_callee_contract_v10']['original025_sources']['model_contract'],'_g2_full_MODEL_original025_readback_facade');R.need(not hasattr(c,'need')and callable(c.require),'genuine whole original025 callee facade')
 validator=roles.model_role_validator(R,m,mods,c,C)
 dense,dense_owned,dense_before=roles.model_role_owner_chain(R,m,SOURCE,'dense',summary['model_release'],c,validator,mods)
 consumer,consumer_owned,consumer_before=roles.model_role_owner_chain(R,m,SOURCE,'stream-consumer',summary['independent_release'],c,validator,mods)
 old_owners=stage['CPU_owners'];R.need(len(old_owners)==2 and len({x['cid']for x in[*old_owners,dense,consumer]})==4,'four distinct actual original owners, including both CPU stage helpers')
 deadlines={x['formal_deadline_monotonic']for x in[*old_owners,dense,consumer]};R.need(len(deadlines)==1,'all four owners retain one original MAIN phase deadline')
 root=Path(m['stream_channel_root']);R.need(root==OUT/'dense/receipts/STREAM'and Path(m['model_receipt_root'])==root.parent,'only exact original shared stream capability')
 R.need(summary['independent']==ATTRIBUTION,'actual original successful finalizer output Ref in MODEL summary')
 bundle_ref=R.ref(root/'FINAL_INPUTS.json');bundle=R.obj(bundle_ref);R.need(bundle['schema']=='bole.actual-stream-final-inputs/v2'and bundle['source']==SOURCE and type(bundle['ranks'])is list and len(bundle['ranks'])==4,'actual complete original finalizer inputs')
 channel_ref=bundle['channel'];strict_ref(channel_ref);R.need(channel_ref['path']==str(root/'CHANNEL.json'),'actual canonical shared channel descriptor');channel=R.obj(channel_ref)
 R.need(channel_ref==summary['stream_channel']and channel['schema']=='bole.owned-independent-stream-channel/v2'and channel['source']==SOURCE and channel['scope']==G2.SCOPE and channel['consumer_source']==m['stream_consumer_source']and channel['consumer_container_independent']is True and channel['consumer_Devices']==[]and channel['host_ownership_audited']is True and channel['metadata_handoff']==summary['metadata_handoff'],'actual current channel/source/scope/independent Devices[] and exact host handoff join')
 owner_copy_proof=[]
 for field,actual,actual_owned,wanted_bytes,wanted_sha in(('model_owner_ref',dense,dense_owned,752588,'ade14a384fdc45854720edb4597e5d2d0103d3316c12fe587ef915f16ecb4e21'),('consumer_owner_ref',consumer,consumer_owned,752722,'7399f8c44c59530bb3edbeca4f48df280a507540661a3b50736d59fd561be542')):
  alias=strict_ref(channel[field]);original_owner=actual['owner_ref'];R.need(alias['path']!=original_owner['path']and Path(alias['path']).parent==root and(alias['bytes'],alias['sha256'])==(wanted_bytes,wanted_sha)and(original_owner['bytes'],original_owner['sha256'])==(wanted_bytes,wanted_sha),'exact actual role-specific original OWNED to shared fullRef metadata alias')
  R.need(R.checked(alias).read_bytes()==R.checked(original_owner).read_bytes()and R.obj(alias)==actual_owned,'actual original and shared owner copy whole bytes and decoded record identical');owner_copy_proof.append(dict(role=actual['role'],original_ref=original_owner,shared_alias_ref=alias,whole_bytes_equal=True,decoded_owner_equal=True))
 R.need(Path(channel['root'])==root and type(channel['nonce'])is str and 0<len(channel['nonce'])<=4096 and len(channel['actual_worker_identities'])==4,'actual retained metadata channel path/nonce/four worker identities')
 identity=channel['actual_consumer_identity'];R.need(type(identity)is dict and type(identity['pid'])is int and identity['pid']>0 and type(identity['start_ticks'])is int and identity['start_ticks']>0 and type(identity['cgroup'])is str and '/docker/'+consumer['cid']in identity['cgroup'],'original consumer process metadata belongs to exact retained consumer owner')
 for identity in channel['actual_worker_identities']:R.need(type(identity)is dict and type(identity['pid'])is int and identity['pid']>0 and type(identity['start_ticks'])is int and identity['start_ticks']>0 and type(identity['cgroup'])is str and '/docker/'+dense['cid']in identity['cgroup'],'original target worker metadata belongs to exact dense owner')
 R.need(len({v['pid']for v in channel['actual_worker_identities']})==4 and bundle['frontend_binding']['owned_cid']==dense['cid'],'distinct all4 target workers and original independently bound frontend owner')
 final_stdout_ref=R.ref(OUT/'cpu-consumer/FINAL.stdout');final_stderr_ref=R.ref(OUT/'cpu-consumer/FINAL.stderr');wire=R.checked(final_stdout_ref).read_bytes();lines=wire.splitlines()
 R.need(len(wire)<=4096 and len(lines)==1 and wire==lines[0]+b'\n'and json.loads(lines[0],object_pairs_hook=unique_object)==ATTRIBUTION and R.checked(final_stderr_ref).read_bytes()==b'','actual original FINAL complete stdout is unique ATTRIBUTION Ref, stderr empty; no invented child terminal')
 final_argv=c.docker_argv(consumer['cid'],[str(R.ROOT/'g2_finalize.py'),'--execute','--source-ref',json.dumps(SOURCE),'--inputs-ref',json.dumps(bundle_ref),'--output',str(root)]);final_argv[2:2]=['--env',G2.FLAG+'=1']
 final_branch=dict(original_host_ref=m['files']['host_service.py'],original_finalizer_ref=m['files']['g2_finalize.py'],inputs_ref=bundle_ref,attribution_ref=ATTRIBUTION,stdout_ref=final_stdout_ref,stderr_ref=final_stderr_ref,source_reconstructed_inner_exec_argv=final_argv,zero_return_required_by_original_success_branch=True,successful_branch_joined_to_exact_MODEL_RESULT_and_unit=True,standalone_FINAL_child_receipt_exists=False,actual_Popen_argv_separately_observed=False)
 metadata_exports=[];PT_proofs=[];R.need(len({r['raw']['path']for r in bundle['ranks']})==4,'four distinct exact final metadata PT exports')
 for entry in bundle['ranks']:
  strict_ref(entry['raw']);strict_ref(entry['receipt']);R.checked(entry['receipt']);exported,proof=protocol.final_metadata_export(R,entry['raw']);metadata_exports.append(exported);PT_proofs.append(proof)
 recompute,adapter,replay_saved_ownership=protocol.original_protocol(R,m,C,G1,G2,CH,O,coverage)
 canonical=mods.sourceio.ref(SOURCE['path']);R.need(canonical==SOURCE,'same source-owned canonical source Ref/key ordering')
 saved_channel=protocol.observed_original_reads(R,(C,CH,mods.sourceio),lambda:replay_saved_ownership(m,canonical,channel_ref));R.need(saved_channel==channel,'unaltered original CH.contract/handoff ledger/saved-owner-inspect/lifetime predicates replayed exactly')
 original_commands=mods.command_contract.validate(C,canonical,m)
 recomputed=protocol.observed_original_reads(R,(C,CH,mods.sourceio),lambda:recompute(canonical,bundle,channel,metadata_exports,original_commands))
 original=R.obj(ATTRIBUTION);compared=dict(recomputed);compared['ranks']=[];budget_rows=[];R.need(len(original['ranks'])==len(recomputed['ranks'])==4,'all4 original and independently recomputed protocol reports')
 for old,new in zip(original['ranks'],recomputed['ranks']):
  used=new['final_metadata_bytes'];previous=old['final_metadata_bytes'];R.need(type(used)is int and type(previous)is int and 0<=previous<=used<=G2.METADATA_CAP,'complete posthoc metadata includes late JSON, never lowers original64MiB bound')
  adjusted=dict(new);adjusted['final_metadata_bytes']=previous;compared['ranks'].append(adjusted);budget_rows.append(dict(rank=new['rank'],original_reported_bytes=previous,independently_recomputed_current_bytes=used,additional_retained_metadata_bytes=used-previous,unchanged_cap_bytes=G2.METADATA_CAP,current_full_budget_pass=True))
 R.need(compared==original,'all original ATTRIBUTION fields, requests, coverage and flags exact; only explicit temporal byte accounting differs')
 R.need(original['service_complete']is True and original['component_checks_pass']is True and original['scheduler_committed_independently']is True and original['all4_worker_retirement_verified']is True and original['every_frame_independently_consumed']is True and original['completed_request_count']==2 and original['successful_raw_replay_available']is False and all(original[k]is False for k in('physical_allocation_growth_proven','normal_EOS_qualified','native_AR_token_identity_compared','model_ready','task_ready','performance_ready','formal_success','timing_is_formal')),'actual full bounded diagnostic attribution, no formal/task/AR/growth promotion')
 exit_ref=R.ref(root/'STREAM_CONSUMER_EXIT.json');consumed=R.obj(exit_ref);frame_rows=[];all_ack_refs=[];all_report_refs=[]
 for rank,exported in enumerate(metadata_exports):
  events=exported['payload']['stream_events'];completed=consumed['requests'][rank];expected=[]
  for item in completed:expected+=['open']+['step']*item['steps']+['retire']
  expected+=['close'];R.need([v['kind']for v in events]==expected,'frame counts derive from every actual consumed request/step');rows=[]
  for event in events:
   ack_ref=strict_ref(event['ack']);R.need(ack_ref['bytes']<=3072,'original unchanged complete ACK wire cap');ack=protocol.observed_original_reads(R,(C,CH,mods.sourceio),lambda ar=ack_ref:CH.load(ar));report_ref=strict_ref(ack['oracle_report']);R.checked(report_ref);all_ack_refs.append(ack_ref);all_report_refs.append(report_ref)
   rows.append(dict(kind=event['kind'],sequence=event['sequence'],manifest_ref=event['manifest'],ack_ref=ack_ref,oracle_report_ref=report_ref,release_ref=event['release'],coverage=event['coverage']))
  frame_rows.append(dict(rank=rank,events=rows,event_count=len(events),target_step_count=sum(v['kind']=='step'for v in events),derived_expected_kinds=expected))
 R.need(len({r['path']for r in all_ack_refs})==len(all_ack_refs)and len({r['path']for r in all_report_refs})==len(all_report_refs),'every derived frame has a distinct original durable ACK and oracle report')
 for r in list(R.READS.values()):R.checked(r)
 canonical=mods.sourceio.ref(SOURCE['path']);attachments=[*mods.bind_model.readset(canonical),*m['dependencies'],*mods.command_contract.validate(mods.sourceio,canonical,m)];after={}
 for r in attachments:R.checked(r);R.need(r['path']not in after or after[r['path']]==r['sha256'],'no conflicting final source/command Ref');after[r['path']]=r['sha256']
 R.need(after==complete and complete,'complete original source/command closure unchanged after independent metadata readback')
 for r in(STAGE_READER,STAGE_PROOF,UNIT,*AUXILIARY.values()):R.checked(r)
 no_accelerator_imports()
 return dict(schema='bole.actual-G2-v13-full-MODEL-metadata-independent-qualification/v1',source=SOURCE,result_ref=RESULT,unit_terminal_ref=UNIT,stage_reader_ref=STAGE_READER,stage_qualification_ref=STAGE_PROOF,actual_stage349_precondition_reopened=True,stage349_reexecuted_by_this_reader=False,sameimage_349_and_original_MODEL_metadata_independent_readback_pass=True,service_experiment_pass=True,component_checks_pass=True,scheduler_committed_independently=True,all4_worker_retirement_verified=True,original_numerical_consumer_completed=True,every_original_frame_report_and_ACK_verified=True,derived_frame_count=len(all_ack_refs),rank_frame_evidence=frame_rows,original_attribution_ref=ATTRIBUTION,consumer_exit_ref=exit_ref,finalizer_inputs_ref=bundle_ref,original_FINAL_branch=final_branch,original_finalizer_metadata_adapter=adapter,final_metadata_exports=PT_proofs,posthoc_metadata_budget=budget_rows,all_four_owned_stopped_retained=True,CPU_stage_owners=old_owners,MODEL_role_owners=[dense,consumer],channel_owner_metadata_aliases=owner_copy_proof,shared_original_formal_deadline_monotonic=next(iter(deadlines)),firstentry_clock=clock,source_nonempty_before_after_equal=True,source_readset_count=len(complete),original_MODEL_elapsed=result['elapsed'],original_MODEL_cleanup_spent=result['cleanup_spent'],helper_refs=AUXILIARY,independent_readback_refs=list(R.READS.values()),reader_ref=full_ref(__file__),stdlib_only=True,owned_channel_reexecuted=True,saved_ownership_metadata_replayed=True,actual_current_processes_queried=False,actual_live_identity_reobserved=False,numerical_raw_replayed_by_this_reader=False,successful_raw_replay_available=False,physical_allocation_growth_proven=False,normal_EOS_qualified=False,native_AR_token_identity_compared=False,model_ready=False,task_ready=False,performance_ready=False,formal_success=False,timing_is_formal=False,NPU=False)
def write_exclusive(path,value):
 p=Path(path);need(p==OUTPUT and p.is_absolute()and p.parent==T and p.parent.is_dir()and not p.exists()and not p.is_symlink(),'only exact new MODEL metadata qualification path, never overwrite')
 wire=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();descriptor=os.open(str(p),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(descriptor,'wb')as stream:stream.write(wire);stream.flush();os.fsync(stream.fileno())
 return full_ref(p)
def main():
 parser=argparse.ArgumentParser(allow_abbrev=False);parser.add_argument('--execute',action='store_true');parser.add_argument('--source-ref');parser.add_argument('--result-ref');parser.add_argument('--unit-terminal-ref');parser.add_argument('--output');args=parser.parse_args()
 if not args.execute:print('{"enabled":false,"NPU":false}');return 0
 need(args.source_ref and args.result_ref and args.unit_terminal_ref and args.output,'actual fixed source/result/unit fullRefs and exact exclusive output required');parse=lambda s:strict_ref(json.loads(s,object_pairs_hook=unique_object));before=full_ref(__file__);value=execute(parse(args.source_ref),parse(args.result_ref),parse(args.unit_terminal_ref))
 need(full_ref(__file__)==before==value['reader_ref'],'independent metadata reader source unchanged');value['reader_source_before_after_equal']=True;qualification=write_exclusive(args.output,value)
 print(json.dumps(dict(qualification_ref=qualification,source=SOURCE,result_ref=RESULT,sameimage_349_and_original_MODEL_metadata_independent_readback_pass=True,all_four_owned_stopped_retained=True,numerical_raw_replayed_by_this_reader=False,actual_live_identity_reobserved=False,formal_success=False,NPU=False)));return 0
if __name__=='__main__':raise SystemExit(main())
