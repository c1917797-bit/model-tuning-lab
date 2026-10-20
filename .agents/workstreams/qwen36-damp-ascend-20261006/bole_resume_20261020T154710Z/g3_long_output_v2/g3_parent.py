"""Actual G2 full streaming qualification is mandatory; no placeholder promotion."""
import sourceio as C


def qualified(sr,m,owner_ref,report_ref,*,source_audit_ref):
    C.need(type(sr)is dict and type(owner_ref)is dict and type(report_ref)is dict,
        'pending G2 actual source/owner/qualification Refs cannot admit G3')
    owner=C.obj(owner_ref);report=C.obj(report_ref);audit=C.obj(source_audit_ref)
    C.need(audit['schema']=='bole.G2-readonly-source-preparation-audit-supplement/v6'and
        audit['source']==sr and audit['missing']==[]and audit['original_contract_unmodified']is True and
        audit['original_source_and_COMMANDS_unmodified']is True and
        audit['source_preparation_supplement_only']is True and audit['directory_mounts_added']is False and
        audit['actual_software_cases']==258 and m['service_required_sameimage_software_cases']==258,
        'actual successful independent G2-v6 source readset/COMMANDS audit and258 controls')
    scope=dict(schema='bole.c1-two-request-stream-service/v2',profile='smoke4',prefix=131,
        request_count=2,max_steps_per_request=3,max_output_tokens=4,
        capture_protocol='every-frame-independent-CPU-ACK/v1')
    C.need(m['service_experiment']==scope and m['prepared_only']is False and m['default_enabled']is False,
        'actual bound source of separately successful smoke4 G2 protocol')
    C.need(owner['source']==sr and owner['primary']is None and owner['secondary']==[]and
        owner['source_before']==owner['source_after']and owner['cpu_only']is False and
        owner['summary']['independent']==report_ref,'actual successful finite clean G2 model owner')
    C.need(report['source']==sr and report['scope']==scope and report['service_complete']is True and
        report['completed_request_count']==2 and report['component_checks_pass']is True and
        report['scheduler_committed_independently']is True and report['all4_worker_retirement_verified']is True and
        report['every_frame_independently_consumed']is True and report['model_ready']is False and
        report['successful_raw_replay_available']is False and len(report['ranks'])==4,
        'actual independently consumed all4 all-step G2 stream, never a first-frame or source-only proof')
    for rank,row in enumerate(report['ranks']):
        C.need(row['rank']==rank and row['all_frames_consumed']is True and
            row['coverage_proof']['all_coverage']is True and len(row['requests'])==2 and
            all(2<=r['steps']<=3 and r['processed_tokens']==3 and len(r['output_token_ids'])==4 and
                r['next_counter_ACKs']==r['steps']-1 and r['component_checks_pass']is True
                for r in row['requests']),'actual G2 cross-step numerical/CPU-ACK/retirement coverage on every rank')
    for ref in m['files'].values():C.checked(ref)
    return True
