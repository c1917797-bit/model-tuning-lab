"""MAIN source-only CPU14 getter and HTTPv3 preparation. Default OFF.

Run in a fresh stdlib interpreter. It reads fixed actual files and writes only
new report/plan/HTTP source leaves. It never invokes a model/container/decoder.
"""
import time
COLD_ENTRY = time.monotonic()
import argparse
import ast
import hashlib
from pathlib import Path
import signal
import sys
import traceback

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P))
import audit_common as A


def frozen_request_body(reference, contract):
    """Compile only this exact pure frozen function, with its real C helper.

    Loading score_tokens would also import decoder. No such import is needed
    for prompt-only source construction, and no CPU namespace is claimed here.
    """
    path = A.checked(reference)
    tree = ast.parse(path.read_bytes(), filename=str(path))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'request_body']
    A.need(len(nodes) == 1 and not nodes[0].decorator_list and not nodes[0].args.defaults,
           'unique unchanged top-level pure request_body')
    namespace = {'C': contract, '__builtins__': __builtins__}
    projection = ast.Module(body=nodes, type_ignores=[])
    exec(compile(projection, str(path), 'exec'), namespace)
    A.checked(reference)
    return namespace['request_body'], hashlib.sha256(ast.dump(nodes[0], include_attributes=False).encode()).hexdigest()


def select_existing(contract, effective, array):
    """Stream the unchanged full arrays within MAIN's small metadata budget.

    Retain the original select IDs/order/token checks and independently recompute
    each frozen row chain/count/max. Only six existing rows remain in memory.
    No renderer/decoder/tokenizer is called and no source gold is reinterpreted.
    """
    A.need(set(effective['tasks']) == set(contract.COUNTS), 'all three unchanged cohorts')
    selected = []
    measured = {}
    for task, expected_count in contract.COUNTS.items():
        meta = effective['tasks'][task]
        path = contract.checked(meta['rows_ref'])
        seen = set()
        chosen = []
        chain = hashlib.sha256()
        maximum = 0
        for row in array(path):
            A.need(row['id'] not in seen, 'whole cohort contains no duplicate ID')
            seen.add(row['id'])
            chain.update(bytes.fromhex(contract.digest(row)))
            ids = row['prompt_token_ids']
            maximum = max(maximum, len(ids))
            if row['id'] in contract.SMOKE[task]:
                A.need(type(ids) is list and 0 < len(ids) <= 3151
                    and all(type(t) is int and 0 <= t < 248320 for t in ids)
                    and row['render_protocol'] == contract.TASK_PROTOCOLS[task], 'whole unchanged selected token-list protocol')
                if task == 'MMLU':
                    A.need(row['ntrain'] == 5, 'same original five-shot prompt')
                chosen.append((task, row))
        A.need(len(seen) == expected_count == meta['count']
            and maximum == meta['max_prompt_tokens'] and chain.hexdigest() == meta['ordered_row_hash_chain'],
            'complete existing whole cohort row-chain/count/maximum ' + task)
        A.need([row['id'] for _, row in chosen] == contract.SMOKE[task], 'same frozen selection order')
        measured[task] = len(seen)
        selected.extend(chosen)
    return selected, measured


def prepare_plan(contract, source_ref, selected_cases, arm, model, root):
    A.need(arm in {'OFF', 'ON'} and type(model) is str and model, 'explicit arm and model label; runtime still pending')
    source = contract.obj(source_ref)
    body, body_ast_sha = frozen_request_body(source['files']['score_tokens.py'], contract)
    selected = []
    for task, row in selected_cases:
        selected.append(dict(task=task, id=row['id'], frozen_row_sha256=contract.digest(row), body=body(row, model)))
    A.need(len(selected) == 6 and [len(r['body']['prompt']) for r in selected] == [89, 50, 134, 126, 362, 377], 'exact six existing full token-list prompts')
    directory = A.new_leaf(root)
    path = directory / 'requests.jsonl'
    with path.open('xb') as stream:
        for value in selected:
            stream.write(contract.canonical(value) + b'\n')
        stream.flush()
        __import__('os').fsync(stream.fileno())
    result = A.write(directory / 'REQUEST_PLAN.json', dict(schema='bole.three-task-prompt-only-request-plan/v1',
        source_ref=source_ref, effective_inputs_ref=source['effective_inputs_ref'], phase='smoke', arm=arm,
        model=model, count=len(selected), requests_ref=A.ref(path), minimum_model_context_tokens=5199,
        concurrency=1, HTTP_executed=False, model_ready=False, task_ready=False))
    return result, selected, body_ast_sha


def creation_argv(owned, creation, image):
    """Original create argv is a typed list, never a file reference."""
    argv = creation['requested_argv']
    A.need(type(argv) is list and 3 <= len(argv) <= 8192
        and all(type(v) is str and v and '\x00' not in v and len(v) <= 65536 for v in argv),
        'actual create requested_argv is a bounded complete list of strings')
    A.need(argv[:2] == ['/usr/bin/docker', 'create'] and argv.count(image) == 1
        and argv.count('--name') == 1 and not any(v.startswith('--name=') for v in argv),
        'one original docker create/image/name in actual list')
    at = argv.index('--name')
    A.need(at+1 < len(argv) and argv[at+1] == owned['name'], 'actual original create name belongs to exact owner')
    A.need(type(creation['exit_code']) is int and creation['exit_code'] == 0
        and type(creation['stdout']) is str and creation['stdout'].strip() == owned['cid']
        and len(owned['cid']) == 64 and all(c in '0123456789abcdef' for c in owned['cid'])
        and owned['image'] == image and owned['guest_cpus'] == [145] and owned['arm'] == 'cpu-preflight',
        'actual successful same fullCID/image/CPU145 owner create receipt')
    A.need(set(creation) == {'argv', 'exit_code', 'observed_utc', 'requested_argv', 'stderr', 'stdout'}
        and type(creation['observed_utc']) is str and type(creation['stderr']) is str
        and creation['argv'] == ['/usr/bin/prlimit', '--as=unlimited', '--', *argv],
        'actual complete original create receipt schema and unchanged prlimit wrapper argv')
    return argv


def verify_HE_create(owned, creation, he, actual_argv, policy, stage, inspect_rows, binding, created_stdout, image):
    argv = creation_argv(owned, creation, image)
    for value in (owned['create_argv'], actual_argv):
        A.need(type(value) is list and all(type(v) is str for v in value), 'HE actual argv fields are real string lists, not Refs/tuples')
    expected = policy.argv(owned['name'], image, stage['source_root'], stage['suite_root'], stage['input_root'], stage['capsule_ref']['sha256'], 'controls')
    A.need(argv == owned['create_argv'] == actual_argv == expected,
        'actual requested/OWNED/file HE argv equals unchanged source-bound original policy')
    A.need(he['schema'] == 'bole.actual-HE-sandbox-owner-evidence/v2'
        and he['container_id'] == owned['cid'] == binding['container_id']
        and he['name'] == owned['name'] and stage['source_ref'] == owned['source']
        and created_stdout.decode().strip() == owned['cid']
        and created_stdout.decode() == creation['stdout'], 'same actual HE owner/stage/source/fullCID/create stdout')
    policy.inspect_actual(inspect_rows, expected_id=owned['cid'], expected_image=image, expected_argv=expected,
        source_root=stage['source_root'], suite_root=stage['suite_root'], input_root=stage['input_root'])
    A.need(expected.count('python3') == 1 and binding['argv'] == expected[expected.index('python3'):]
        and binding['uid'] == 65534 and binding['Devices'] == [],
        'actual whole HE child argv/uid/Devices binding matches exact env-i create')
    return dict(actual_create_argv_list_verified=True, source_policy_argv_verified=True,
        actual_inspect_and_live_binding_join_verified=True, container_id=owned['cid'], argv_sha256=hashlib.sha256(A.canonical(argv)).hexdigest())


def additional_primary_closure(owner, inventory, expected, inputs, task):
    """Fixed actual39 records plus exact direct OWNED/create/quiescence links.

    CPU_proof already adds its full explicit validation readset. This supplements
    the known actual primary exports; it is not a recursive arbitrary Ref walker.
    """
    inventory.extend(expected.values(), 'CPU14_actual_primary')
    for r in owner['quiescence_observations']:
        inventory.add(r, 'CPU14_actual_quiescence')
    joins = {}
    for phase in ('cpu-preflight', 'he-controls', 'cpu-consumer'):
        owned_ref = expected[phase + '/OWNED.json']
        owned = A.obj(owned_ref)
        creation_ref = inventory.add(owned['create_receipt'], 'CPU14_actual_create')
        frozen_create = A.obj(A.ref(P/'CPU14_CREATE_PRIMARY_EXPECTED.json'))
        A.need(creation_ref == frozen_create[phase], 'same full actual CPU14 create Ref2 to whole Ref3 join')
        creation = A.obj(creation_ref)
        owner_image = 'sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
        creation_argv(owned, creation, owner_image)
        expected_source = task if phase == 'he-controls' else inputs['task_source_unbound_ref']
        A.need(owned['source'] == expected_source, 'same actual bound HE / unbound CPU owner source')
        if phase == 'he-controls':
            he_ref = inventory.add(owner['summary']['HE_owner_ref'], 'CPU14_actual_HE_create_join')
            he = A.obj(he_ref)
            stage = A.obj(inventory.add(he['stage_ref'], 'CPU14_actual_HE_create_join'))
            argv_ref = inventory.add(he['create_argv_ref'], 'CPU14_actual_HE_create_join')
            actual_argv = A.obj(argv_ref)
            binding = A.obj(inventory.add(owner['summary']['HE_binding'], 'CPU14_actual_HE_create_join'))
            inspect_rows = A.obj(inventory.add(he['inspect_ref'], 'CPU14_actual_HE_create_join'))
            stdout = A.checked(inventory.add(he['created_id_ref'], 'CPU14_actual_HE_create_join')).read_bytes()
            bound = A.obj(task)
            policy_ref = inventory.add(bound['files']['he_policy.py'], 'CPU14_actual_HE_policy')
            policy = A.load(policy_ref, '_HTTPv3_exact_CPU14_HE_create_policy')
            joins[phase] = verify_HE_create(owned, creation, he, actual_argv, policy, stage, inspect_rows, binding, stdout, owner_image)
        else:
            phase_key = 'CPU' if phase == 'cpu-preflight' else 'independent'
            binding = A.obj(inventory.add(owner['summary'][phase_key]['binding'], 'CPU14_actual_CPU_create_join'))
            A.need(binding['container_id'] == owned['cid'], 'actual CPU owner create belongs to actual live phase binding')
            joins[phase] = dict(actual_create_argv_list_verified=True, container_id=owned['cid'], actual_live_binding_join_verified=True)
    return joins


def pending_model_gates():
    return dict(expected_parent='actual successful G2v11', actual_G2_source_ref=None,
        actual_G2_owner_ref=None, actual_G2_independent_ref=None, actual_G2_consumer_exit_ref=None,
        model_construction_admitted=False, actual_HTTP_executed=False, BOLE_activation_proven=False,
        native_AR_identity_proven=False, formal_task_accuracy_accepted=False, performance_ready=False, model_ready=False)


def run(request_ref, manifest_ref, *, prepare):
    manifest, own_refs = A.verify_manifest(manifest_ref, P)
    A.need(manifest['schema'] == 'bole.MAIN-HTTPv3-source-audit-advisory/v2', 'exact new source audit packet')
    A.need(A.ref(__file__) == dict(manifest['files']['source_audit.py'], path=str(P/'source_audit.py')), 'actual exact source-owned entry')
    request = A.obj(request_ref)
    A.need(set(request) == {'schema', 'HTTP_packet_manifest_ref', 'authority_ref', 'native_snapshot_manifest_ref',
        'generation_config_ref', 'arm', 'model', 'report_root', 'plan_root', 'HTTP_root'}, 'explicit source-only request fields; no G2 filler')
    A.need(request['schema'] == 'bole.MAIN-HTTPv3-source-audit-request/v2', 'source-only request schema')
    elapsed = time.monotonic() - COLD_ENTRY
    A.need(elapsed < A.SECONDS, 'cold-entry finite clock precedes manifest/readset replay')
    A.authority(request['authority_ref'], A.SECONDS-elapsed)
    if prepare:
        A.need(all(type(request[k]) is str for k in ('plan_root', 'HTTP_root')), 'two explicit new preparation leaves')
    else:
        A.need(request['plan_root'] is None and request['HTTP_root'] is None, 'read-only audit does not allocate a plan/source')
    report_root = A.new_leaf(request['report_root'])
    report = dict(schema='bole.actual-MAIN-CPU14-HTTPv3-source-audit/v2', request_ref=request_ref,
        manifest_ref=manifest_ref, primary=None, completed=False, pending_model=pending_model_gates())
    try:
        forbidden = A.install_read_only_import_guard()
        inventory = A.Inventory()
        inventory.extend(own_refs, 'new_audit_source')
        inventory.extend((request_ref, request['authority_ref']), 'MAIN_request_authority')
        mr = request['HTTP_packet_manifest_ref']
        HTTP_root = A.checked(mr).parent
        parent, parent_refs = A.verify_manifest(mr, HTTP_root, A.HTTP_SHA)
        inventory.extend(parent_refs, 'frozen_HTTPv3_source')
        A.need(parent['supported_decoder4_manifest_sha256'] == A.DECODER_SHA, 'unchanged decoder4 parent')
        C = A.load(A.ref(HTTP_root/'http_common.py'), 'http_common')
        owner = C.obj(C.SUPPORTED_CPU_OWNER_REF)
        first = C.obj(owner['summary']['CPU']['report'])
        source_ref = first['payload']['bound_task_source_ref']
        evidence = []
        owner = C.CPU_proof(C.SUPPORTED_CPU_OWNER_REF, source_ref, evidence_refs=evidence)
        inventory.extend(evidence, 'actual_CPU14_validation_closure')
        expected = A.obj(A.ref(P/'CPU14_ACTUAL_PRIMARY_EXPECTED.json'))
        A.need(len(expected) == 39 and expected['RESULT.json'] == C.SUPPORTED_CPU_OWNER_REF, 'fixed actual39 primary whole records')
        inputs = C.obj(owner['inputs_ref'])
        create_joins = additional_primary_closure(owner, inventory, expected, inputs, source_ref)
        O = A.load(inputs['files']['owner_common.py'], '_HTTPv3_exact_CPU14_owner_readset')
        base, tokenizer_routes = O.task_readset(source_ref, host=True)
        inventory.extend(base, 'actual_task_input_source')
        inventory.extend(O.tokenizer_sources(inputs, host=True), 'actual_tokenizer_source_snapshots')
        task = C.obj(source_ref)
        for key in ('effective_inputs_ref', 'input_preparation_source_ref'):
            inventory.add(task[key], 'actual_v012_bound_inputs')
        effective = C.obj(task['effective_inputs_ref'])
        for value in effective['tasks'].values():
            inventory.add(value['rows_ref'], 'actual_v012_rows')
        # Original host route is source-owned; never invent /models assets here.
        A.need(len(tokenizer_routes) == 7, 'all seven actual tokenizer host/guest bindings')
        native_ref = request['native_snapshot_manifest_ref']
        inventory.add(native_ref, 'actual_native_snapshots')
        native = C.obj(native_ref)
        expected_native = C.obj(C.ref(HTTP_root/'NATIVE_SOURCE_EXPECTED.json'))
        A.need(set(native) == set(expected_native) and len(native) == 14, 'all fourteen actual native source routes')
        for key, pair in native.items():
            A.need(set(pair) == {'runtime_ref', 'snapshot_ref'} and pair['runtime_ref'] == expected_native[key], 'exact native runtime declaration ' + key)
            actual = inventory.add(pair['snapshot_ref'], 'actual_native_snapshots')
            A.need((actual['bytes'], actual['sha256']) == (pair['runtime_ref']['bytes'], pair['runtime_ref']['sha256']), 'same stopped-image native whole bytes ' + key)
        generation = inventory.add(request['generation_config_ref'], 'actual_original_generation_config')
        A.need((generation['bytes'], generation['sha256']) == (202, 'e70c136c1b78ddc1fb0905bac8e733a4dc448d4f852a5dd75143fffc70be550e'), 'unchanged original generation config')
        constructor = C.obj(task['files']['DECODER_CONSTRUCTOR.json'])
        image_sources = [*constructor['native_sources'].values(), *C.obj(task['original_inputs_ref'])['library_refs']]
        # These are guest-runtime checks for the future same-image executor.
        # Host audit verifies exact snapshots above, never guesses these paths.
        T = A.load(task['files']['task_contract.py'], '_HTTPv3_exact_decoder4_contract')
        T.source(source_ref)
        frozen_array = A.load(task['files']['frozen/gsm_scorer.py'], '_HTTPv3_exact_frozen_stream_array')
        selected, cohort_counts = select_existing(T, effective, frozen_array.array)
        A.need([(t, r['id']) for t, r in selected] == C.SMOKE, 'frozen ordered six-case selection')
        lengths = [len(r['prompt_token_ids']) for t, r in selected]
        A.need(lengths == [89, 50, 134, 126, 362, 377], 'unchanged full prompt lengths')
        input_before = inventory.snapshot()
        report['source_input_before'] = input_before
        report['complete_input_before_captured_before_prepare'] = True
        created = []
        plan_ref = HTTP_ref = None
        projection_sha = None
        if prepare:
            # The successful CPU14 qualification is reused. This does not call
            # request_plan.run, cpu_runtime, verify_inputs, decoder, or tokenizer.
            plan_ref, rows, projection_sha = prepare_plan(T, source_ref, selected, request['arm'], request['model'], request['plan_root'])
            C.plan(plan_ref)
            H = A.load(A.ref(HTTP_root/'prepare_http.py'), '_HTTPv3_exact_prepare')
            HTTP_ref = H.prepare(plan_ref, C.SUPPORTED_CPU_OWNER_REF, request['authority_ref'],
                native_ref, generation, Path(request['HTTP_root']))
            new_source = C.obj(HTTP_ref)
            A.need(set(new_source['files']) == set(C.FILES) and len(new_source['files']) == 8, 'exact new eight-file HTTPv3 source')
            created = [plan_ref, C.obj(plan_ref)['requests_ref'], HTTP_ref, *new_source['files'].values(),
                new_source['native_expected_ref'], C.ref(Path(request['HTTP_root'])/'CPU_OWNER_EXPECTED.json'), new_source['generation_config_ref']]
            # A fresh module sees its own copied paths; original C is packet-bound.
            fresh = A.load(new_source['files']['http_common.py'], '_HTTPv3_new_exact_common')
            fresh.source(HTTP_ref, native_runtime=False)
            fresh.plan(plan_ref)
        inventory.recheck()
        report['source_input_after'] = inventory.snapshot()
        A.need(input_before == inventory.snapshot(), 'all original source/evidence paths unchanged')
        A.authority(request['authority_ref'], 0)
        A.need(not forbidden and not any(k.split('.')[0] in A.FORBIDDEN for k in sys.modules), 'no tokenizer/inference/model import attempted or loaded')
        elapsed = time.monotonic()-COLD_ENTRY
        A.need(elapsed < A.SECONDS, 'whole finite source-only audit including complete before/after reads')
        reused_bytes = {(r['bytes'], r['sha256']) for r in inventory.files.values()}
        created_provenance = [dict(ref=r, provenance='byte-reused-copy' if (r['bytes'], r['sha256']) in reused_bytes else 'new-metadata') for r in created]
        report.update(completed=True, supported_CPU14_owner_ref=C.SUPPORTED_CPU_OWNER_REF,
            supported_CPU14_inputs_ref=owner['inputs_ref'], bound_task_source_ref=source_ref,
            CPU14_validation_recomputed_by_frozen_HTTPv3=True, CPU14_full_execution_reused=True,
            actual_CPU14_create_joins=create_joins, complete_input_before_captured_before_prepare=True,
            actual_CPU14_phases_rerun=0, tokenizer_constructions=0, rendered_or_retokenized_rows=0,
            fresh_model_requests=0, fresh_task_scores=0, selected_existing_prompt_rows=len(selected),
            selected_prompt_lengths=lengths, all_cohort_source_gold_template_qualification_reused=True,
            reused_qualified_cohort_counts=cohort_counts, fresh_existing_cohort_row_chain_recomputed=True,
            fresh_source_gold_template_qualification=False,
            readset_counts=inventory.counts(), source_input_before=input_before, source_input_after=inventory.snapshot(),
            complete_explicit_host_readset=list(inventory.files.values()), tokenizer_host_guest_routes=tokenizer_routes,
            decoder_image_runtime_refs=image_sources, image_runtime_refs_opened_on_host=False,
            plan_ref=plan_ref, HTTP_source_ref=HTTP_ref, created_file_refs=created, fresh_files_created=len(created),
            created_file_provenance=created_provenance,
            copied_unchanged_files=sum(r['provenance']=='byte-reused-copy' for r in created_provenance),
            new_metadata_files=sum(r['provenance']=='new-metadata' for r in created_provenance),
            report_files_excluded_from_fresh_artifact_count=True, request_body_exact_function_AST_sha256=projection_sha,
            original_request_plan_CLI_executed=False, Devices_empty_namespace_claimed=False,
            requested_model_label=request['model'], model_label_runtime_observed=False,
            forbidden_import_attempts=forbidden, elapsed_seconds=elapsed)
    except BaseException as error:
        text = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        raw = text.encode()
        report['primary'] = dict(type=type(error).__name__, message=str(error)[:4096], traceback=raw[:262144].decode('utf-8', errors='replace'),
            traceback_bytes=len(raw), traceback_sha256=hashlib.sha256(raw).hexdigest(), traceback_complete=len(raw)<=262144)
        report['elapsed_seconds'] = time.monotonic()-COLD_ENTRY
        if 'inventory' in locals():
            report['partial_verified_readset_counts'] = inventory.counts()
            report['partial_verified_input_refs'] = list(inventory.files.values())
            report['complete_input_before_captured_before_prepare'] = 'input_before' in locals()
    reference = A.write(report_root/'SOURCE_AUDIT.json', report)
    return reference, report


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--audit', action='store_true')
    mode.add_argument('--prepare', action='store_true')
    parser.add_argument('--manifest-ref')
    parser.add_argument('--request-ref')
    args = parser.parse_args()
    if not (args.audit or args.prepare):
        print('{"enabled":false,"model_executed":false,"CPU14_rerun":false}')
        return 0
    A.need(args.manifest_ref and args.request_ref, 'exact source-bound manifest and new actual request Refs')
    def expired(signum, frame):
        raise TimeoutError('original cold-entry source-audit finite600seconds exhausted')
    signal.signal(signal.SIGALRM, expired)
    remaining = A.SECONDS-(time.monotonic()-COLD_ENTRY)
    A.need(remaining > 0, 'cold-entry admission')
    signal.setitimer(signal.ITIMER_REAL, remaining)
    reference, report = run(A.parse(args.request_ref), A.parse(args.manifest_ref), prepare=args.prepare)
    print(A.canonical(dict(result_ref=reference, completed=report['completed'], model_ready=False)).decode())
    return 0 if report['completed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
