"""Validated-performance policy only. Default OFF; never grants numerical or launch admission."""
FLAG='BOLE_VALIDATED_PERFORMANCE_ENABLE'
DECLARATION=dict(schema='bole.validated-performance-elision/v1',enabled=True,
    cache_metadata_dump=False,fa_integer_dump=False,initial_gdn_diagnostic_clones=False,
    repeated_publication_readback=False,postwrite_diagnostic_readback=False,
    actual_applied_diagnostic_clones=False,consensus_CPU_snapshots=False,
    diagnostic_head_and_MTP_clones=False,
    keep_staging_and_rollback_before=True,keep_destination_prevalidation=True,
    keep_TP_decision_and_two_phase_consensus=True,keep_actual_cache_writes=True,
    keep_native_input_identity=True,keep_native_tail_witness=True,
    keep_native_retirement_and_counter_ACK=True)


def need(value,message):
    if not value:raise ValueError(message)


def select(C,manifest,environ):
    flag=environ.get(FLAG)
    declaration=manifest.get('validated_performance_profile')
    if flag in (None,'','0'):
        need(declaration is None,'declared fast policy requires explicit opt-in')
        return False
    need(flag=='1' and type(declaration)is dict and set(declaration)==set(DECLARATION)
         and all(type(declaration[k])is type(v) and declaration[k]==v for k,v in DECLARATION.items()),
         'exact source-bound validated-performance policy')
    need(C.ref(__file__)==manifest['files']['validated_performance_policy.py'],
         'actual source-owned performance policy')
    need(manifest['performance_arm']=='bole' and manifest['default_enabled']is False
         and manifest['prepared_only']is False,'only actual bound candidate, never nativeAR mutation')
    scope=manifest['performance_profile']['scope']
    need(scope['input_tokens']==131 and scope['output_tokens']==1024 and scope['concurrency']==1,
         'fixed original131/1024/C1 screening domain')
    need(all(environ.get(k) in(None,'','0') for k in (
        'BOLE_NATIVE_BOUNDARY_PROBE_ENABLE','BOLE_NATIVE_PROJECTION_PROBE_ENABLE',
        'BOLE_SHORT_STATE_DIGEST_ENABLE','BOLE_G3_STREAM_ENABLE')),
         'no diagnostic raw/state/stream modes in performance candidate')
    return True


def commit_metadata(proposal,publication):
    owner=proposal['owner']
    rows=proposal['writes']
    need(publication['owner']==owner and publication['cache_published']is True
         and publication['scheduler_ack_pending']is True and len(rows)==128,
         'actual transaction returned successful publication; ACK remains pending')
    destinations={(row['layer'],row['kind']) for row in rows}
    need(len(destinations)==128,'all unique actual destination descriptors')
    return dict(schema='bole.performance-commit-metadata/v1',
        request=owner.request,generation=owner.generation,version=owner.version,
        processed_nodes=list(publication['processed_nodes']),
        emitted_tokens=list(publication['emitted_tokens']),
        next_length=publication['next_length'],next_version=publication['next_version'],
        destination_count=128,cache_published=True,scheduler_ack_pending=True,
        tensor_readback_performed=False,numerical_qualified=False,formal_performance=False)
