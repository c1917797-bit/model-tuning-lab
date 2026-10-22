"""Exact source_inputs function snapshot for software contract testing; no executable entry."""
def source_inputs(readset, config):
    sr = config['source_ref']
    need(typed_ref(sr) == SOURCE/'SOURCE_BOUND.json', 'new exact source root')
    manifest, audit, commands = [readset.obj(config[key])
        for key in ('source_ref', 'source_audit_ref', 'commands_ref')]
    need(manifest['root'] == str(SOURCE) and manifest['output_root'] == str(OUTPUT) and
         manifest['default_enabled'] is False and manifest['prepared_only'] is False,
         'fresh default-OFF bound source and output identity')
    need(manifest['text_only_config'] == TEXT_ONLY_CONFIG,
         'explicit native text-only service configuration, never implicit profile bypass')
    need(audit['schema'] == 'bole.boundary-source-admission/v1' and audit['source'] == sr and
         audit['source_validated'] is True and audit['original_inputs_unchanged'] is True and
         audit['host_readset_exact'] is True and audit['hard_cutoff'] == CUT and
         audit['historical_report_cutoff'] == OLD_REPORT_CUT and audit['old_window_extended'] is False,
         'actual new source audit with separate unchanged old report deadline')
    need(audit['audit_program_unchanged'] is True and audit['tests_executed'] is False and
         audit['NPU'] is False and audit['paired_gate_pass'] is False and
         audit['numerical_qualified'] is False and audit['performance_admitted'] is False and
         audit['formal_performance'] is False and len(audit['original_twenty_controls']) == 20,
         'source audit is complete source-only evidence, never numerical or device admission')
    need(audit['audit_program_ref'] == config['source_audit_program_ref'], 'exact current auditor identity')
    readset.read(audit['audit_program_ref'], keep=False)
    readset.read(audit['original_audit_source'], keep=False)
    build = readset.obj(config['build_record_ref'])
    need(build['schema'] == 'bole.boundary-probe-source-freeze/v1' and build['source'] == sr and
         build['commands'] == config['commands_ref'] and build['source_only'] is True and
         build['original_inputs_unchanged'] is True and build['fixed_cutoff'] == CUT and
         build['historical_report_cutoff'] == OLD_REPORT_CUT and build['old_window_extended'] is False and
         build['phase_seconds'] == PHASE and build['cleanup_seconds'] == CLEANUP and
         all(build[key] is False for key in ('owner_created', 'NPU', 'paired_gate_pass',
                                           'performance_admitted', 'formal_performance')),
         'actual complete freeze record binds new source and unchanged scope/qualification')
    readset.read(build['parent'], keep=False)
    readset.read(build['review'], keep=False)
    for reference in build['original_readset']:
        readset.read(reference, keep=False)
    audited = {}
    for reference in audit['readset']:
        path = typed_ref(reference)
        need(str(path) not in audited or audited[str(path)] == reference, 'one source readset identity')
        audited[str(path)] = reference
        readset.read(reference, keep=False)
    for reference in [sr, config['commands_ref'], manifest['authority_ref'],
                      *manifest['files'].values(), *manifest['dependencies']]:
        need(audited.get(reference['path']) == reference, 'all source/authority/commands in exact audited readset')
    authority = readset.obj(manifest['authority_ref'])
    need(authority['start_epoch'] == START and authority['cutoff_epoch'] == CUT and
         authority['cutoff_iso'] == '2026-10-22T23:10:00+00:00' and
         authority['phase_seconds'] == PHASE and authority['cleanup_seconds'] == CLEANUP and
         authority['user_authorization_ref'] == config['authorization_ref'],
         'separate real new authorization, unchanged individual phase and cleanup')
    authorization = readset.obj(config['authorization_ref'])
    need(authorization['old_window_extended'] is False and
         authorization['old_hard_report_deadline_utc'] == '2026-10-22T12:38:41+00:00' and
         authorization['internal_batch_start_epoch'] == START and
         authorization['internal_batch_cutoff_epoch'] == CUT and
         authorization['whole_prepare_admission_seconds'] == PREPARE,
         'no automatic extension of original window')
    need(audited.get(config['authorization_ref']['path']) == config['authorization_ref'] and
         audited.get(authorization['document']['path']) == authorization['document'],
         'entire explicit authorization document and JSON in audited source readset')
    readset.read(authorization['document'], keep=False)
    need(commands['bound_source'] == sr and type(commands['model']) is list,
         'one actual source-bound model command')
    sys.path.insert(0, str(SOURCE))
    C = load_exact(readset, manifest['files']['contract090.py'], 'contract090')
    current = C.source(sr)
    need(current == manifest, 'genuine original current source gate')
    import performance_validate, command_contract
    proof = performance_validate.validate(sr)
    need(proof['source'] == sr and proof['source_validated'] is True, 'original full successor source validator')
    command_contract.validate(C, sr, manifest)
    need(os.environ.get('DENSE090_EXTERNAL_OUTPUT_ENABLE') == '1',
         'original external-output opt-in required in launcher environment before source load')
    from owned_substrate import load
    from g2_host_adapter import install
    c, S, H, pairs = load(OUTPUT)
    install(C, c, S, H, manifest)
    need(S.PHASE == PHASE and S.CLEANUP == CLEANUP and c.CUTOFF == CUT and
         S.PHYSICAL == (4, 5, 6, 7) and S.MEM == 32 * 2**30 and
         S.HOST_MEM == 512 * 2**20 and S.RESERVE == 8 * 2**30 and S.WORKSPACE == 32 * 2**30,
         'genuine original controller with unchanged CPU/RAM/disk/phase/cleanup reserve')
    return manifest, commands, C, c, S, H
