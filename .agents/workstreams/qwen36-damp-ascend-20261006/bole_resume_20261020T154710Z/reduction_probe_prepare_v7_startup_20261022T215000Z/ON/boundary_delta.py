"""Exact, single-occurrence observer delta after the unchanged short overlay.

runtime(old, short_out) is consumed by the separately source-pinned child
validator.  It never reads a source file, imports torch, launches, or writes.
The mathematical modules and native lifecycle implementation are absent from
this edit set.  The parent builder must prove every complete resulting file.
"""
EXTRA_RUNTIME = ('prefill_tail.py', 'model_process_calibration.py', 'g3_budget.py')
EDITED_RUNTIME = ('service_runner.py', 'host_service.py', 'command_contract.py', 'performance_host.py', *EXTRA_RUNTIME)


def once(text, before, after):
    if text.count(before) != 1:
        raise ValueError('exact one source fragment required: ' + before[:100])
    return text.replace(before, after, 1)


def runtime(old, short_out):
    out = dict(short_out)
    s = out['service_runner.py']
    s = once(s, 'import snapshot_publication as SP',
                'import snapshot_publication as SP\nimport boundary_probe_v1 as BP')
    s = once(s, '    restore_tail = T.install_capture(worker, torch, C,',
        "    boundary = BP.create(torch, C, source_ref, m, os.environ, group.rank_in_group, worker, inner)\n"
        "    calibration.boundary_probe = boundary\n"
        "    if boundary is not None:\n"
        "        state.restorers.append(boundary.uninstall)\n"
        '    restore_tail = T.install_capture(worker, torch, C,')
    s = once(s, "        get_forward_context=get_forward_context, gdn_ref=refs['gdn'], context_ref=refs['forward_context'])",
                "        get_forward_context=get_forward_context, gdn_ref=refs['gdn'], context_ref=refs['forward_context'], boundary_probe=boundary)")
    s = once(s, "            get_attention_context=get_attention_context, refs=refs, length=131, request_epoch=state.generation)\n        root_hidden = kw['hidden']",
        "            get_attention_context=get_attention_context, refs=refs, length=131, request_epoch=state.generation)\n"
        "        if boundary is not None:\n"
        "            boundary.registered(bindings, window)\n"
        "        root_hidden = kw['hidden']")
    s = once(s, '        drafter.num_speculative_tokens = 1\n        try:\n            result = old_mtp(*args, **kwargs)',
        '        drafter.num_speculative_tokens = 1\n'
        '        observe_initial_mtp = boundary is not None and state.live.frame is None\n'
        '        try:\n'
        '            if observe_initial_mtp:\n'
        "                E.need(state.initial_draft is None, 'one genuine initial MTP boundary')\n"
        "                boundary.capture('initial_mtp_before', draft=boundary.mtp_inventory(drafter))\n"
        '            result = old_mtp(*args, **kwargs)\n'
        '            if observe_initial_mtp:\n'
        "                boundary.capture('initial_mtp_after', draft=boundary.mtp_inventory(drafter))")
    s = once(s, "                        context_ref=refs['forward_context']),",
                "                        context_ref=refs['forward_context'], boundary_probe=boundary),")
    s = once(s, "                    emit_retirement=lambda row: (probe.retire(row), performance_metadata('RETIRE', row)))",
                "                    emit_retirement=lambda row: (probe.retire(row), performance_metadata('RETIRE', row),\n"
                "                        None if boundary is None else boundary.retire(row)))")
    s = once(s, '                if performance is not None:\n                    state.failed = True\n                    if not state.published:',
        '                if performance is not None:\n'
        '                    state.failed = True\n'
        '                    if boundary is not None:\n'
        '                        try:\n'
        '                            boundary.uninstall()\n'
        '                        except BaseException as observer_restore_error:\n'
        "                            primary.add_note('boundary observer restoration: '+repr(observer_restore_error))\n"
        '                    if not state.published:')
    out['service_runner.py'] = s

    s = old['prefill_tail.py']
    s = once(s, '                    context_ref):', '                    context_ref, boundary_probe=None):')
    s = once(s, '  def core(this,mixed_qkv,b,a,core_attn_out,_old=old,_module=native_module):',
                '  def core(this,mixed_qkv,b,a,core_attn_out,_old=old,_module=native_module,_index=layer.layer_idx):')
    s = once(s, '   extra=arena[slot,3:].clone()\n   result=_old(mixed_qkv=mixed_qkv,b=b,a=a,core_attn_out=core_attn_out)',
        '   extra=arena[slot,3:].clone()\n'
        '   if boundary_probe is not None:\n'
        '    boundary_probe.native_core_enter(_index,this,meta,slot,ids[0],runner.requests[ids[0]],mixed_qkv,b,a)\n'
        '   result=_old(mixed_qkv=mixed_qkv,b=b,a=a,core_attn_out=core_attn_out)')
    s = once(s, '      actual_native_forward_returned=True)\n   return result',
        '      actual_native_forward_returned=True)\n'
        '   if boundary_probe is not None:\n'
        '    boundary_probe.native_core_return(_index,this,meta,slot,runner.requests[ids[0]],core_attn_out)\n'
        '   return result')
    out['prefill_tail.py'] = s

    s = old['model_process_calibration.py']
    s = once(s, '        self.proofs = []', '        self.proofs = []\n        self.boundary_probe = None')
    s = once(s, '        created = self.ref is None\n        if created:',
        '        created = self.ref is None\n'
        '        if self.boundary_probe is not None:\n'
        "            self.boundary_probe.capture('calibration_before', generation=request_epoch, created=created)\n"
        '        if created:')
    s = once(s, '        self.proofs.append(copy.deepcopy(proof))\n        return ref, value, proof',
        '        self.proofs.append(copy.deepcopy(proof))\n'
        '        if self.boundary_probe is not None:\n'
        "            self.boundary_probe.capture('calibration_after', generation=request_epoch, created=created, calibration_ref=ref)\n"
        '        return ref, value, proof')
    out['model_process_calibration.py'] = s

    s = old['g3_budget.py']
    s = once(s, '    sets=dict(calibration=cal,identity=journals,events=events,other=other,final=finals)',
        "    short_digest=set()\n"
        "    if m.get('boundary_probe_profile') is not None:\n"
        "        import boundary_probe_v1 as BP\n"
        "        C_.need(C_.ref(BP.__file__)==m['files']['boundary_probe_v1.py'], 'exact source-bound accounting observer')\n"
        "        C_.need(BP.canonical(m['boundary_probe_profile'])==BP.canonical(BP.DECLARATION), 'exact bounded observer declaration')\n"
        "        other.update(BP.retained_files(C_,m,rank))\n"
        "        other.update(base.glob('MTP-LOAD-*'))\n"
        "        other.update(base.glob('.MTP-LOAD-*'))\n"
        "        other.update(base.glob('worker-*-snapshot-*.json*'))\n"
        "        other.update(base.glob('.worker-*-snapshot-*.json.pending-*'))\n"
        "        short_digest.update(base.glob('STATE-*-R%d.json'%rank))\n"
        "        short_digest.update(base.glob('.STATE-*-R%d.json.pending-*'%rank))\n"
        "    sets=dict(calibration=cal,identity=journals,events=events,other=other,final=finals)\n"
        "    if m.get('boundary_probe_profile') is not None:sets['short_digest']=short_digest")
    out['g3_budget.py'] = s

    s = out['host_service.py']
    s = once(s, 'import bole_performance_profile as PERF',
                'import bole_performance_profile as PERF\nimport boundary_probe_v1 as BP\nimport projection_probe_v1 as PP')
    s = once(s, "  if performance:argv[2:2]=['--env',PERF.FLAG+'=1','--env','BOLE_SHORT_STATE_DIGEST_ENABLE=1','--env','BOLE_OBSERVATION_ONLY_OFF='+('1' if m['short_state_digest_profile']['observation']=='OFF' else '0')]",
                "  if performance:argv[2:2]=['--env',PERF.FLAG+'=1','--env','BOLE_SHORT_STATE_DIGEST_ENABLE=1','--env',BP.FLAG+'=1','--env',PP.FLAG+'=1','--env','BOLE_OBSERVATION_ONLY_OFF='+('1' if m['short_state_digest_profile']['observation']=='OFF' else '0')]")
    s = once(s, " performance=PERF.select(os.environ,m.get('performance_profile'))\n C.need(performance is not None,'explicit performance runtime opt-in')",
                " performance=PERF.select(os.environ,m.get('performance_profile'))\n"
                " C.need(C.ref(BP.__file__)==m['files']['boundary_probe_v1.py'] and BP.select(os.environ,m.get('boundary_probe_profile')) is not None,'exact source and explicit boundary host flag')\n"
                " C.need(C.ref(PP.__file__)==m['files']['projection_probe_v1.py'] and PP.select(os.environ,m.get('projection_probe_profile')) is not None,'exact source and explicit projection host flag')\n"
                " C.need(performance is not None,'explicit performance runtime opt-in')")
    out['host_service.py'] = s
    out['command_contract.py'] = once(out['command_contract.py'],
        "'BOLE_SHORT_STATE_DIGEST_ENABLE=1',", "'BOLE_SHORT_STATE_DIGEST_ENABLE=1','BOLE_NATIVE_BOUNDARY_PROBE_ENABLE=1','BOLE_NATIVE_PROJECTION_PROBE_ENABLE=1',")
    out['performance_host.py'] = once(out['performance_host.py'],
        "    summary['worker_snapshots'] = rows\n    summary['streaming_validation'] = performance_client_consumer.consume(",
        "    summary['worker_snapshots'] = rows\n"
        "    import boundary_probe_v1 as BP\n"
        "    C.need(C.ref(BP.__file__)==m['files']['boundary_probe_v1.py'], 'exact final boundary budget reader')\n"
        "    summary['boundary_terminal_budget'] = BP.terminal_accounting(C,m)\n"
        "    summary['streaming_validation'] = performance_client_consumer.consume(")
    s = out['g3_budget.py']
    s = once(s, 'OTHER=3*2**20\n', 'OTHER=3*2**20\nPROJECTION_RAW=8*2**20\n')
    s = once(s, '    total=event+CAL+JOURNAL+OTHER+FINAL', '    total=event+CAL+JOURNAL+OTHER+FINAL+PROJECTION_RAW')
    s = once(s, '        other_rank_bytes=OTHER,final_global_and_summary_bytes=FINAL,',
                '        other_rank_bytes=OTHER,projection_raw_bytes=PROJECTION_RAW,final_global_and_summary_bytes=FINAL,')
    s = once(s, '    sets=dict(calibration=cal,identity=journals,events=events,other=other,final=finals)',
                "    projection_raw=set()\n"
                "    if m.get('projection_probe_profile') is not None:\n"
                "        import projection_raw_v1 as PR\n"
                "        C_.need(C_.ref(PR.__file__)==m['files']['projection_raw_v1.py'],'exact raw accounting source')\n"
                "        projection_raw=PR.retained_files(C_,m,rank)\n"
                "    sets=dict(calibration=cal,identity=journals,events=events,other=other,final=finals,projection_raw=projection_raw)")
    s = once(s, "    C_.need(values['calibration']<=CAL and values['identity']<=JOURNAL and values['other']<=OTHER and values['final']<=FINAL,",
                "    C_.need(values['calibration']<=CAL and values['identity']<=JOURNAL and values['other']<=OTHER and values['final']<=FINAL and values['projection_raw']<=PROJECTION_RAW,")
    out['g3_budget.py'] = s

    # Only the proven production health-call deadline changes. TimeoutExpired
    # still escapes to the original retained cleanup; no overlapping retry.
    out['performance_host.py'] = once(out['performance_host.py'],
        "        value = ctl.h.run(ctl.wrapper(argv), min(4, ctl.remaining(cap=4)))\n",
        "        health_limit = min(30, end - time.monotonic(), ctl.remaining(cap=30))\n        C.need(health_limit > 0, 'bounded remaining native startup health budget')\n        value = ctl.h.run(ctl.wrapper(argv), health_limit)\n")

    for name, text in out.items():
        compile(text, name, 'exec')
    return out
