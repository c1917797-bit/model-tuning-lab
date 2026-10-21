"""Source13 full-model predecessor join; saved metadata is not a new math run."""
import json
from pathlib import Path
import sourceio as C
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
ROOT=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13')
OUT=Path('/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v13')
STREAM=OUT/'dense/receipts/STREAM'
def R(p,n,h):return dict(path=str(p),bytes=n,sha256=h)
ACTUAL={
 'source':R(ROOT/'SOURCE_BOUND.json',994678,'545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345'),
 'owner_result':R(OUT/'RESULT.json',1340078,'e326a53f47c65aff4a498ac30da5568009c22e81cd9e469b2f46a28f086ebb67'),
 'qualification':R(T/'G2_V13_MODEL_METADATA_READBACK.json',1240436,'989edb4d558c0006327ee3b1e432263a7090a80cda8e196147966f102481c7a0'),
 'source_audit':R(T/'G2_V13_SOURCE_AUDIT.json',3618,'cba97cf1167c477df8035f83e5d8cde2005dc513f7f1bdcc8d0c2707a47ace64'),
 'unit_terminal_ref':R(T/'G2_V13_MODEL_SYSTEMD_TERMINAL_V2.json',314,'5e108eb1ff089e168f6f5193ec95c3a1d81c9cc052c307878ade92574a4b742a'),
 'original_attribution_ref':R(STREAM/'ATTRIBUTION.json',66000,'f78c53b8f8dd741cc6e94e892f8f2d283919ac3fa1fd061b83caaa72d544f46d'),
 'finalizer_inputs_ref':R(STREAM/'FINAL_INPUTS.json',46310,'84a05dc7e9da3b13deccaf3d50cb12b4008e409de5cb731a322e47cb050debf6'),
 'consumer_exit_ref':R(STREAM/'STREAM_CONSUMER_EXIT.json',72866,'8f38896f31f01a8f3ab105d9bf74bbd14607247592e931eced65ff8f7d974e61'),
 'reader_ref':R(T/'g2_v13_full_model_readback_v1/model_readback_bound_v2.py',21102,'4b84f54ef46a7c06783d74bd7099d51628cf5bafb52d60aa6b8b46b983cf005c'),
 'stage_qualification_ref':R(T/'G2_V13_MODEL_STAGE_READBACK.json',1729550,'e1a324b5679e80c2fc9f18f41b2faa4e8f8c2d02c17281e744c302f1578d87ed'),
 'stage_reader_ref':R(T/'g2_v13_model_stage_readback_v1/model_stage_actual_v2.py',60047,'3f42803170271f2deca7917f415914f0337fc2204638dc588fc3e3ba1f7f00c0'),
 'protocol':R(T/'g2_v13_full_model_readback_v1/metadata_protocol_v2.py',9452,'cc87c659a3c2deca4075ad3494d571dab1e94233950fe0beb010a4071ea506ae'),
 'roles':R(T/'g2_v13_full_model_readback_v1/model_owner_roles.py',9693,'5b84965a8bbba18d114d38c1765f3879a06117c3aead990ec3caee38e90d64f4'),
 'commands':R(ROOT/'COMMANDS.json',3620,'93b6cf7022a491e4d7e048c87b0bc889c18ce822da2f2c82a9111ab4be9623c3')}
SCOPE=dict(schema='bole.c1-two-request-stream-service/v2',profile='smoke4',prefix=131,request_count=2,max_steps_per_request=3,max_output_tokens=4,capture_protocol='every-frame-independent-CPU-ACK/v1')
QTRUE=('sameimage_349_and_original_MODEL_metadata_independent_readback_pass','actual_stage349_precondition_reopened','all4_worker_retirement_verified','all_four_owned_stopped_retained','component_checks_pass','every_original_frame_report_and_ACK_verified','original_numerical_consumer_completed','owned_channel_reexecuted','saved_ownership_metadata_replayed','reader_source_before_after_equal','scheduler_committed_independently','service_experiment_pass','source_nonempty_before_after_equal','stdlib_only')
QFALSE=('NPU','actual_current_processes_queried','actual_live_identity_reobserved','numerical_raw_replayed_by_this_reader','stage349_reexecuted_by_this_reader','successful_raw_replay_available','formal_success','model_ready','performance_ready','task_ready','native_AR_token_identity_compared','normal_EOS_qualified','physical_allocation_growth_proven','timing_is_formal')
QTYPED=('unit_terminal_ref','original_attribution_ref','finalizer_inputs_ref','consumer_exit_ref','reader_ref','stage_qualification_ref','stage_reader_ref')
def typed(r):
 C.need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['path'])is str and Path(r['path']).is_absolute()and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and len(r['sha256'])==64 and all(c in'0123456789abcdef'for c in r['sha256']),'exact typed Ref3');return r
def retained(refs):
 C.need(type(refs)is list,'explicit retained Ref list; never recursively harvest released raw');by_path={}
 for r in refs:
  typed(r);C.need(r['path']not in by_path or by_path[r['path']]==r,'one exact retained Ref per path');by_path[r['path']]=r
 for r in by_path.values():C.checked(r)
 return list(by_path.values())
def audit_join(sr,ar):
 wrapper=C.obj(ar);C.need(wrapper['exit_code']==0 and wrapper['stderr']==''and type(wrapper['stdout'])is str,'actual zeroexit source-audit wrapper');a=json.loads(wrapper['stdout'])
 C.need(a['schema']=='bole.G2-v13-HTTP-visibility-source-audit/v1'and a['source']==sr and a['readset_count']==4088 and a['prospective_sameimage_cases']==349,'actual source13 audited source/4088/349')
 for k,n in dict(source8_fresh_cases=279,source10_fresh_cases=25,source11_fresh_cases=18,current_ACK_cases=19,new_HTTP_cases=8).items():C.need(a[k]==n,'source13 exact suite count '+k)
 C.need(a['software_allocation_seconds']==dict(controls=60,metadata=120,parent279=120)and a['aggregate_cap_seconds']==300,'unchanged source13 staged finite allocation')
 for k in('HTTP_files_produced_in_existing_channel','all_original341_test_files_byteexact','original_finalizer_budget_selects_HTTP_files','original_math_ACK_cap_argv_transport_resources_unchanged'):C.need(a[k]is True,'source13 audit positive '+k)
 for k in('new_RW_alias','new_mounts','actual_model_executed','actual_software_executed','NPU'):C.need(a[k]is False,'source audit is source-only '+k)
 clock=a['firstentry_clock'];expected=dict(NPU=False,create_cap_seconds=60,deadline_renewal_forbidden=True,fixed_cutoff=1792597630,one_main_entry_clock=True,phase_seconds=3600,schema='bole.G2-actual-main-cold-clock-source/v9',shared_cleanup_seconds=180,source_hashes_in_phase=True)
 C.need(all(clock[k]==v for k,v in expected.items()),'same original firstentry/phase/cleanup/cutoff');return a
def qualified(sr,m,owner_ref,report_ref,*,source_audit_ref):
 for r in(sr,owner_ref,report_ref,source_audit_ref):typed(r)
 C.need(C.obj(sr)==m and m['service_experiment']==SCOPE and m['prepared_only']is False and m['default_enabled']is False and m['service_required_sameimage_software_cases']==349,'actual bound smoke4 predecessor, not new1024 or source-only')
 audit_join(sr,source_audit_ref);owner=C.obj(owner_ref);q=C.obj(report_ref)
 C.need(owner['source']==sr and owner['primary']is None and owner['secondary']==[]and owner['source_before']and owner['source_before']==owner['source_after']and owner['cpu_only']is False,'successful nonempty source-stable finite model owner')
 C.need(q['schema']=='bole.actual-G2-v13-full-MODEL-metadata-independent-qualification/v1'and q['source']==sr and q['result_ref']==owner_ref and q['source_readset_count']==4088 and q['derived_frame_count']==36,'full metadata qualification joined to this exact owner/source')
 for k in QTRUE:C.need(q[k]is True,'required predecessor qualification '+k)
 for k in QFALSE:C.need(q[k]is False,'metadata-only/nonformal scope '+k)
 for k in QTYPED:typed(q[k])
 C.need(owner['summary']['independent']==q['original_attribution_ref'],'owner independent is original ATTRIB, not new Q')
 report=C.obj(q['original_attribution_ref'])
 C.need(report['schema']=='bole.actual-G2-stream-attribution/v2'and report['source']==sr and report['scope']==SCOPE and report['service_complete']is True and report['completed_request_count']==2,'original complete two-request attribution')
 for k in('component_checks_pass','scheduler_committed_independently','all4_worker_retirement_verified','every_frame_independently_consumed'):C.need(report[k]is True,'original all-step mathematical/retirement report '+k)
 C.need(report['model_ready']is False and report['successful_raw_replay_available']is False and type(report['ranks'])is list and len(report['ranks'])==4,'four original ranks, no production/raw promotion')
 for rank,row in enumerate(report['ranks']):
  p=row['coverage_proof'];C.need(row['rank']==rank and row['all_frames_consumed']is True and p['all_coverage']is True and p['request_count']==2 and p['complete_output_tokens']==8 and p['final_pending_by_retirement']is True and len(row['requests'])==2,'complete late coverage on rank '+str(rank))
  C.need(all(2<=r['steps']<=3 and r['processed_tokens']==3 and len(r['output_token_ids'])==4 and r['next_counter_ACKs']==r['steps']-1 and r['component_checks_pass']is True for r in row['requests']),'every original request numerical/ACK completion')
 exit=C.obj(q['consumer_exit_ref'])
 C.need(exit['schema']=='bole.actual-stream-consumer-exit/v2'and exit['source']==sr and exit['completed']is True and exit['source_unchanged']is True and exit['primary']is None and exit['traceback']is None and exit['actual_frame_batches']==9 and len(exit['ACKs'])==36 and len(exit['requests'])==4,'complete zero-fault independent consumer exit')
 C.need(exit['consumer_source']==m['files']['g2_consumer.py'],'exact source-owned consumer used')
 C.need(exit['channel_ref']==report['channel'],'consumer exit and original attribution share exact saved channel');typed(report['channel']);C.checked(report['channel'])
 terminal=C.obj(q['unit_terminal_ref']);properties=terminal['properties']
 expected=dict(ActiveState='active',ControlPID='0',ExecMainStatus='0',Id='bole-g2-v13-model-20261020t154710z.service',MainPID='0',Restart='no',Result='success',SubState='exited',Type='exec')
 C.need(terminal['schema']=='bole.actual-finite-unit-terminal/v1'and all(properties[k]==v for k,v in expected.items()),'actual successful active/exited PID0 retained finite unit')
 C.need(type(q['helper_refs'])is dict and type(q['independent_readback_refs'])is list and q['independent_readback_refs'],'explicit retained reader closure')
 refs=retained([sr,owner_ref,report_ref,source_audit_ref,*[q[k]for k in QTYPED],*q['helper_refs'].values(),*q['independent_readback_refs'],*m['files'].values()])
 return dict(schema='bole.G3-source13-full-model-predecessor-join/v1',source=sr,owner_result=owner_ref,qualification=report_ref,source_audit=source_audit_ref,retained_refs=refs,original_attribution=q['original_attribution_ref'],consumer_exit=q['consumer_exit_ref'],unit_terminal=q['unit_terminal_ref'],metadata_only_readback=True,original_numerical_consumer_completed=True,raw_math_replayed_here=False,NPU=False)
def actual_qualified(sr,m,owner_ref,report_ref,*,source_audit_ref):
 C.need(sr==ACTUAL['source']and owner_ref==ACTUAL['owner_result']and report_ref==ACTUAL['qualification']and source_audit_ref==ACTUAL['source_audit'],'only the actual complete source13 predecessor may admit this G3 revision')
 q=C.obj(report_ref)
 for k in QTYPED:C.need(q[k]==ACTUAL[k],'exact actual qualified reference '+k)
 C.need(q['helper_refs']['protocol']==ACTUAL['protocol']and q['helper_refs']['roles']==ACTUAL['roles'],'exact full-metadata helper sources')
 C.need(len(q['independent_readback_refs'])==4556,'complete explicit retained qualification readset, not partial output')
 C.need(Path(m['root'])==ROOT and m['prepared_template']==R(ROOT/'SOURCE_TEMPLATE.json',994461,'bba737864f15597bd52d583c2f7cd091873b231578d96b195a7b281a23819c7d'),'exact actual13 root and original prepared-template authority')
 for r in ACTUAL.values():C.checked(r)
 proof=qualified(sr,m,owner_ref,report_ref,source_audit_ref=source_audit_ref)
 proof.update(actual_fixed_refs=True,actual_source_readset_count=4088,qualification_declared_retained_refs=4556,source13_commands=ACTUAL['commands']);return proof
