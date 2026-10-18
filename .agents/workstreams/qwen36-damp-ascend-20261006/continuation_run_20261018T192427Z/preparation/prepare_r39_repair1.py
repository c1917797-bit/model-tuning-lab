"""R39 repair1 immutable preparation; default OFF, read-only emit only.

Preserve failed v1: its narrow prefix seam collided with the current OUTPUT.
This version rewrites the authenticated complete IDENTITY assignment instead.

The frozen R38 preparer composes its authenticated predecessor in memory.
This successor changes declared active clocks/authority/identities and exact
current metadata joins, with whole-body inverses. Original mathematical,
resource, historical seal and failure evidence remains original bytes.
No controller, subprocess, raw loader, ledger or destination tree is opened.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import ast
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import types

PREP = '/cache/cch/qwen36-paper-preparation-20261007/lowbit/'
OPT = '/opt/host/vnf/austinov/'
STAMP = '20261018T192427Z'
BATCH = 'MAIN-CONTINUE-' + STAMP + '-v1'
START, CUT = 1792351467, 1792437867
OLD_START, OLD_CUT = 1792226600, 1792313000
AUTH_SCHEMA = 'ascend.paper-portfolio.explicit-continuation-batch/v1'
REUSE_SCHEMA = 'ascend.continuation-batch.historical-artifact-reuse/v1'
AUTH_ROOT = OPT + 'model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/continuation_run_' + STAMP
AUTHORITY = dict(path=AUTH_ROOT + '/AUTHORITY.json', bytes=5610, sha256='12644bad0403760aa7e976411572251f89c021e0182184c847b3c841ab6bab52')
REUSE = dict(path=AUTH_ROOT + '/REUSE_SCOPE.json', bytes=3394, sha256='99ba96aef815229a2db96cd977f3d1fe12b46774d42bcb79e765d74bfe192259')
GENERATOR = dict(path=OPT + 'model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/continuation_20261018/source/deltalog_r38_preparation/prepare_r38.py', bytes=23738, sha256='ad622334b9d3d5df0c225f687f23a67c00af93ed5b1a9e185df1a9e2678d1648')
PATCH = dict(path=PREP + 'deltalog-r37-preparation-MAIN-renew24h-20261018-001/PATCHES.json', bytes=1885, sha256='0bd70da9feea656e0146853d90078fcd3e7684c6ec42551129b3738edfc18b1f')
PAYLOAD_OLD = dict(path=PREP + 'deltalog-selected-firstdecode-renew24h-20261018-001-r36-all4-publication/SOURCE_MANIFEST.json', bytes=22730, sha256='75330c840e308aa9946a729f8a0948b39f13f213e9a1bcf3560f25a9560a50b4')
MODEL_ROOT = PREP + 'deltalog-first-real-decode-owned-continuation-v1-101-r39-' + STAMP + '-001'
EARLY_ROOT = PREP + 'deltalog-early-software-owned-continuation-v1-r39-' + STAMP + '-001'
PAYLOAD_ROOT = PREP + 'deltalog-selected-firstdecode-continuation-r39-' + STAMP + '-001'
CONSUMER_ROOT = PREP + 'deltalog-geometry-consumer-continuation-r39-' + STAMP + '-001'
MODEL_OUT = OPT + 'run-deltalog-CONT-R39-' + STAMP + '-001'
POST_OUT = OPT + 'run-deltalog-CONT-R39-postconsumer-' + STAMP + '-001'
CONSUMER_OUT = OPT + 'run-deltalog-CONT-R39-geometry-consumer-' + STAMP + '-001'
EARLY_OUT = OPT + 'run-dl-CONT-R39-early-' + STAMP + '-001'
P_PARENT = '/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/'
P_NAME = 'first-real-decode-model-snapshots-CONT-R39-' + STAMP + '-001'
J_NAME = 'MODEL_SNAPSHOTS_LEDGER.CONT-R39-' + STAMP + '-001.json'
IDENTITY = dict(owner='MAIN-CONTINUE-DL-R39-' + STAMP + '-001', run_id='MAIN-CONTINUE-DL-R39-' + STAMP + '-001', container_prefix='deltalog-CONT-R39-' + STAMP + '-')
EARLY_OWNER = 'deltalog-CONT-R39-early-' + STAMP + '-001'
EARLY_PREFIX = 'dl-CONT-R39-early-' + STAMP + '-'
MARK = '__R21_REVIEWED_TEMPLATE_SHA256__'
PAYLOAD_CHANGED_PY = ('firstdecode_gate.py', 'publication_barrier.py', 'renewal_authority.py')
OLD_TOKENS = (str(OLD_START), str(OLD_CUT), '2026-10-18T08:43:20', '20261017_084320',
              'explicit-renewed24h', 'renewed24h.historical-artifact-reuse')


def need(value, reason):
    if not value:
        raise ValueError(reason)


def serial(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode('utf8')


def ref(path, raw):
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def checked(value):
    need(type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}, 'exact Ref3')
    p = Path(value['path'])
    need(type(value['bytes']) is int and 0 < value['bytes'] <= 4 * 2**20 and p.is_absolute()
         and str(p) == value['path'] and '..' not in p.parts
         and not any(q.is_symlink() for q in (p, *p.parents)), 'bounded ordinary immutable source')
    before = p.lstat()
    need(stat.S_ISREG(before.st_mode), 'regular source')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        with os.fdopen(fd, 'rb', closefd=False) as handle:
            raw = handle.read(value['bytes'] + 1)
        opened = os.fstat(fd)
    finally:
        os.close(fd)
    after = p.lstat()
    key = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    need(key(before) == key(opened) == key(after) and ref(p, raw) == value, 'whole stable source bytes')
    return raw


def obj(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('nonfinite JSON constant ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def module(raw, filename, name):
    result = types.ModuleType(name)
    result.__file__ = filename
    exec(compile(raw, filename, 'exec'), result.__dict__)
    return result


def authority_documents(a, reuse):
    need(a['schema'] == AUTH_SCHEMA and a['batch_id'] == BATCH
         and a['start_epoch'] == START and a['cutoff_epoch'] == CUT,
         'exact new source-bound continuation batch')
    need(CUT - START == 86400 and START > OLD_CUT
         and a['batch_limit']['duration_seconds'] == 86400
         and a['batch_limit']['duration_was_explicitly_specified_by_user'] is False
         and a['batch_limit']['this_immutable_cutoff_cannot_be_extended'] is True,
         'finite MAIN-selected new batch, not an extension or a fabricated user duration')
    need(a['old_window_immutable']['not_retroactive'] is True
         and a['resource_limits']['original_storage_limits_unchanged'] is True
         and a['acceptance_unchanged'] is True and a['qualification'] is False
         and a['physical_npus'] == [4, 5, 6, 7] and a['protected_npus'] == [0, 1, 2, 3],
         'unchanged original resource, device and acceptance boundaries')
    need(reuse['schema'] == REUSE_SCHEMA and reuse['batch_id'] == BATCH
         and reuse['base_authority'] == AUTHORITY and reuse['start_epoch'] == START
         and reuse['cutoff_epoch'] == CUT and reuse['qualification'] is False
         and reuse['numeric_qualified'] is False and reuse['not_retroactive'] is True
         and reuse['storage']['original_authority_kept_as_legacy_ledger_identity'] is True
         and reuse['storage']['original_storage_limits_unchanged'] is True,
         'exact separate historical reuse scope without promotion or new capacity')


def edit(raw, changes, label):
    """Exact occurrence counts and complete reverse equality, never a tree-wide replace."""
    original = raw
    for before, after, count in changes:
        before, after = before.encode('utf8'), after.encode('utf8')
        need(before != after and raw.count(before) == count and after not in raw,
             'reviewed exact source seam ' + label + ': ' + before.decode('utf8'))
        raw = raw.replace(before, after)
    inverse = raw
    for before, after, count in reversed(changes):
        before, after = before.encode('utf8'), after.encode('utf8')
        need(inverse.count(after) == count, 'unique inverse seam ' + label)
        inverse = inverse.replace(after, before)
    need(inverse == original, 'complete source inverse ' + label)
    if label.endswith('.py'):
        ast.parse(raw)
    return raw


def assignment(raw, name, value, label):
    text = raw.decode('utf8')
    rows = [n for n in ast.parse(text).body if isinstance(n, ast.Assign)
            and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == name]
    need(len(rows) == 1, 'one source-bound constant ' + label + '/' + name)
    before = ast.get_source_segment(text, rows[0])
    return edit(raw, [(before, name + '=' + repr(value), 1)], label)


def clock(raw, label, start_count=1, cut_count=1, authorities=False, schema=False, iso=False):
    changes = []
    if start_count:
        changes.append((str(OLD_START), str(START), start_count))
    if cut_count:
        changes.append((str(OLD_CUT), str(CUT), cut_count))
    if schema or authorities:
        changes.append(('ascend.paper-portfolio.explicit-renewed24h/v1', AUTH_SCHEMA, 1))
    if authorities:
        changes.append(('ascend.renewed24h.historical-artifact-reuse/v1', REUSE_SCHEMA, 1))
    if iso:
        changes.append(('2026-10-18T08:43:20+00:00', '2026-10-19T19:24:27+00:00', 1))
    result = edit(raw, changes, label)
    if authorities:
        result = assignment(result, 'AUTHORITY', AUTHORITY, label)
        result = assignment(result, 'REUSE', REUSE, label)
    return result


def source_refs(root, tree, names=None):
    return {name: ref(root + '/' + name, tree[name]) for name in sorted(names if names is not None else tree)}


def rewrite_refs(value, replacements):
    if type(value) is dict:
        if set(value) == {'path', 'bytes', 'sha256'} and value['path'] in replacements:
            before, after = replacements[value['path']]
            need(value == before, 'no stale same-path source Ref')
            return copy.deepcopy(after)
        return {k: rewrite_refs(v, replacements) for k, v in value.items()}
    if type(value) is list:
        return [rewrite_refs(v, replacements) for v in value]
    return value


def map_refs(before, after):
    return {r['path']: (r, after[name]) for name, r in before.items()}


def command_strings(value, replacements, pairs):
    if type(value) is dict:
        value = rewrite_refs(value, replacements)
        return {k: command_strings(v, replacements, pairs) for k, v in value.items()}
    if type(value) is list:
        return [command_strings(v, replacements, pairs) for v in value]
    if type(value) is str:
        if value.startswith('{'):
            try:
                parsed = obj(value)
            except (ValueError, TypeError):
                parsed = None
            if type(parsed) is dict and set(parsed) == {'path', 'bytes', 'sha256'}:
                replaced = rewrite_refs(parsed, replacements)
                if replaced != parsed:
                    return json.dumps(replaced, separators=(',', ':'))
        for before, after in pairs:
            value = value.replace(before, after)
    return value


def inverse_row(before, after, original_ref, new_path):
    need(ref(original_ref['path'], before) == original_ref, 'whole original inverse source')
    return dict(original_ref=original_ref, after_ref=ref(new_path, after),
                before_utf8=before.decode('utf8'), after_utf8=after.decode('utf8'),
                complete_inverse=True, numerical_changes=False)


def refresh_phase_inverse(tree, old):
    note = obj(old['PHASE_EDITS_R21.json'])
    need(set(note['files']) == {'window_overlay.py', 'postconsume_recipe.py', 'postwork_verify.py'},
         'exact original full phase inverse membership')
    for name, row in note['files'].items():
        before = ''.join(difflib.restore(row['ndiff'], 1)).encode('utf8')
        previous = ''.join(difflib.restore(row['ndiff'], 2)).encode('utf8')
        need(ref(row['original_ref']['path'], before) == row['original_ref'] and previous == old[name],
             'original phase inverse and current defining body')
        if tree[name] != previous:
            row['ndiff'] = list(difflib.ndiff(before.decode('utf8').splitlines(keepends=True),
                                            tree[name].decode('utf8').splitlines(keepends=True)))
        need(''.join(difflib.restore(row['ndiff'], 1)).encode('utf8') == before
             and ''.join(difflib.restore(row['ndiff'], 2)).encode('utf8') == tree[name],
             'complete original-to-current phase inverse remains exact')
    tree['PHASE_EDITS_R21.json'] = serial(note)


def prepare_payload(G, authority_raw, reuse_raw):
    previous = obj(checked(PAYLOAD_OLD))
    tree = G.own_bytes(previous)
    need(len(tree) == 37 and previous['software_cases'] == 26,
         'complete original payload source and all26 controls')
    old = dict(tree)
    tree['firstdecode_gate.py'] = clock(tree['firstdecode_gate.py'], 'payload/firstdecode_gate.py')
    tree['publication_barrier.py'] = clock(tree['publication_barrier.py'], 'payload/publication_barrier.py', 0, 1)
    tree['renewal_authority.py'] = clock(tree['renewal_authority.py'], 'payload/renewal_authority.py', authorities=True)
    tree['renewal_authority_snapshot.json'] = authority_raw
    tree['renewal_reuse_scope_snapshot.json'] = reuse_raw
    changed = set(PAYLOAD_CHANGED_PY) | {'renewal_authority_snapshot.json', 'renewal_reuse_scope_snapshot.json'}
    need({n for n in old if old[n] != tree[n]} == changed, 'only declared payload authority/clock delta')
    source = copy.deepcopy(previous)
    source['root'] = PAYLOAD_ROOT
    source['files'] = source_refs(PAYLOAD_ROOT, tree)
    source['renewal_authority'] = AUTHORITY
    source['continuation_batch'] = dict(batch_id=BATCH, authority_ref=AUTHORITY, reuse_scope_ref=REUSE,
                                      start_epoch=START, cutoff_epoch=CUT, predecessor_payload=PAYLOAD_OLD,
                                      authority_clock_identity_only=True, mathematical_bytes_unchanged=True,
                                      actual_sameimage_26_pass=None, qualified=False)
    source_raw = serial(source)
    tree['SOURCE_MANIFEST.json'] = source_raw
    return tree, source, ref(PAYLOAD_ROOT + '/SOURCE_MANIFEST.json', source_raw), previous


def prepare_early(G, prior_tree, prior, authority_raw):
    tree = dict(prior_tree)
    old_owner = tree['owner.py']
    changes = [(G.EARLY_NEW, EARLY_ROOT, 1), (G.EARLY_OUT_NEW, EARLY_OUT, 1),
               ('deltalog-R38identity-early-software', EARLY_OWNER, 1),
               (repr('dl-software38identity-cpu-'), repr(EARLY_PREFIX), 1)]
    tree['owner.py'] = clock(edit(old_owner, changes, 'early/owner.py'), 'early/owner.py', schema=True)
    tree['recover.py'] = edit(tree['recover.py'], [(G.MODEL_NEW, MODEL_ROOT, 1)], 'early/recover.py')
    inverse = obj(tree['OWNER_EDITS.json'])
    need(len(inverse['edits']) == 1 and inverse['edits'][0]['after'].encode('utf8') == old_owner
         and inverse['edits'][0]['before'].encode('utf8') == tree['DONOR_OWNER.py']
         and inverse['edits'][0]['count'] == 1,
         'complete original historical donor inverse')
    inverse['edits'][0]['after'] = tree['owner.py'].decode('utf8')
    inverse['after'] = {k: ref('', tree['owner.py'])[k] for k in ('bytes', 'sha256')}
    tree['OWNER_EDITS.json'] = serial(inverse)
    source = copy.deepcopy(prior)
    source['root'] = EARLY_ROOT
    source['output_root'] = EARLY_OUT + '/software'
    source['authority_ref'] = AUTHORITY
    source['files'] = source_refs(EARLY_ROOT, tree, prior['files'])
    source['continuation_batch'] = dict(batch_id=BATCH, authority_ref=AUTHORITY,
                                      start_epoch=START, cutoff_epoch=CUT, qualified=False)
    raw = serial(source)
    tree['SOURCE_TEMPLATE.json'] = raw
    return tree, source, ref(EARLY_ROOT + '/SOURCE_TEMPLATE.json', raw)


def test_case_counts(tree):
    counts = {}
    for name, raw in tree.items():
        if name.startswith('test_') and name.endswith('.py'):
            parsed = ast.parse(raw)
            count = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test_')
                        for c in parsed.body if isinstance(c, ast.ClassDef) for n in c.body)
            counts[name] = count
    return counts


def audit(G, old_trees, trees, model, early, payload, model_ref, early_ref, payload_ref, cold_module):
    mt, et, pt = trees['model'], trees['early'], trees['payload']
    need(model['prepared_only'] is True and early['prepared_only'] is True
         and model['software_cases'] == 255 and payload['software_cases'] == 26,
         'no bound model/early or reduced original255/payload26')
    for alias, manifest, names, root in [('model', model, model['files'], MODEL_ROOT),
                                         ('early', early, early['files'], EARLY_ROOT),
                                         ('payload', payload, payload['files'], PAYLOAD_ROOT)]:
        tree = trees[alias]
        need(manifest['root'] == root and manifest['files'] == source_refs(root, tree, names), 'complete new own-source closure ' + alias)
        need(test_case_counts(tree) == test_case_counts(old_trees[alias]), 'same actual test names/counts; no deletion or skip ' + alias)
    need(G.module_constant(mt['packet_contract.py'], 'ROOT') == MODEL_ROOT
         and G.module_constant(mt['packet_contract.py'], 'OUTPUT') == MODEL_OUT
         and G.module_constant(mt['packet_contract.py'], 'IDENTITY') == IDENTITY
         and G.module_constant(mt['packet_contract.py'], 'SOFTWARE_CASES') == 255,
         'one model packet identity/count')
    need(G.module_constant(et['owner.py'], 'ROOT') == EARLY_ROOT
         and G.module_constant(et['owner.py'], 'OUTROOT') == EARLY_OUT
         and G.module_constant(et['owner.py'], 'OWNER') == EARLY_OWNER
         and G.module_constant(et['recover.py'], 'MODEL_ROOT') == MODEL_ROOT,
         'actual early owner and actual child current model identity')
    need(mt['software_dependencies/early_scan_owner.py'] == et['owner.py']
         and mt['software_dependencies/early_scan_template.json'] == et['SOURCE_TEMPLATE.json'],
         'exact current early owner/template mirrors')
    need(model['early_software_policy']['prepared_owner_source'] == early_ref
         and model['early_software_policy']['required_payload_source'] == payload_ref
         and model['firstdecode_contract']['payload_source'] == payload_ref
         and model['prepared_identity_repair']['actual_child'] == early['files']['recover.py'],
         'same current early/model/payload relation')
    for name, body in pt.items():
        need(mt['software_dependencies/payload_contract_mirror/' + name] == body,
             'whole source-identical current payload mirror ' + name)
    need(mt['software_fixtures/owner_overlay.py.txt'] == mt['owner_overlay.py'], 'actual parser fixture uses current owner overlay')
    need(model['window'] == dict(start=START, cutoff=CUT) and model['authority'] == AUTHORITY
         and model['authority_sha256'] == AUTHORITY['sha256'] and model['cutoff_epoch'] == CUT,
         'one exact active authority/window')
    plugin = obj(mt['plugin/SOURCE_TEMPLATE.json'])
    need(plugin['window'] == model['window'], 'plugin current window joins model')
    index = obj(mt['COMMANDS.json'])
    need(index['output'] == MODEL_OUT and index['not_executable'] is True
         and index['execution_ticket'] == 'COMMANDS_FINAL.json', 'current command index, not a stale historical index')
    for key, entry in [('binding', 'bind_source.py'), ('sourceaudit', 'host_ticket.py'), ('execute', 'host_ticket.py')]:
        need(MODEL_ROOT + '/' + entry in index[key]['args'], 'actual current source command index ' + key)
    final = obj(mt['COMMANDS_FINAL.json'])
    need(final['template'] == model_ref and final['payload_source'] == payload_ref
         and final['postconsumer_input_ticket']['payload_source'] == payload_ref
         and final['phase_budget_registration'] == model['phase_budget_registration']
         and final['unchanged_cutoff_epoch'] == CUT
         and final['bind']['argv'][6] == final['cheap_prebind']['argv'][6] == model_ref['sha256'],
         'whole final template/ticket/current payload and original phase relation')
    cold_module.validate(obj(mt['payload_cold_readset_preflight.json']), payload_ref)
    need('SOURCE_MANIFEST.json' not in mt and 'plugin/SOURCE_MANIFEST.json' not in mt
         and 'SOURCE_MANIFEST.json' not in et, 'no fabricated bound model/early/plugin source')
    allowed = {('early', 'DONOR_OWNER.py'), ('model', 'test_stream_closed_tree.py')}
    findings, syntax = {}, {}
    for alias, tree in trees.items():
        syntax[alias] = 0
        for name, raw in tree.items():
            if not name.endswith('.py'):
                continue
            ast.parse(raw)
            syntax[alias] += 1
            stale = [token for token in OLD_TOKENS if token.encode('utf8') in raw]
            if stale:
                if (alias, name) in allowed:
                    need(raw == old_trees[alias][name], 'exact unchanged historical donor/mtime fixture')
                else:
                    findings[alias + '/' + name] = stale
            for token in (G.MODEL_NEW, G.EARLY_NEW, G.P_NEW, G.J_NEW, 'R38identity'):
                need(token.encode('utf8') not in raw, 'no old R38 active identity ' + alias + '/' + name)
    need(not findings, 'unreviewed old active authority/clock: ' + json.dumps(findings, sort_keys=True))
    return dict(python_syntax_and_authority_identity_counts=syntax, old_active_clock_findings=findings,
                historical_python_preserved=[a + '/' + n for a, n in sorted(allowed)],
                unchanged_test_method_counts=True, model_cases=255, early_cases=253, payload_cases=26,
                model_source_created=False, early_source_created=False, NPU=False, qualified=False)


def rebind_packet(G, raw, old_output, old_identity):
    """Whole defining identity assignment; prefix overlap in OUTPUT is harmless."""
    need(G.module_constant(raw, 'ROOT') == G.MODEL_NEW
         and G.module_constant(raw, 'OUTPUT') == old_output
         and G.module_constant(raw, 'IDENTITY') == old_identity,
         'exact complete original packet identity before rebinding')
    value = edit(raw, [(G.MODEL_NEW, MODEL_ROOT, 1), (old_output, MODEL_OUT, 1)], 'model/packet_contract.py')
    return assignment(value, 'IDENTITY', IDENTITY, 'model/packet_contract.py')


def prepare():
    authority_raw, reuse_raw = checked(AUTHORITY), checked(REUSE)
    authority_documents(obj(authority_raw), obj(reuse_raw))
    G = module(checked(GENERATOR), GENERATOR['path'], '_r39_exact_r38_preparer')
    bundle = G.prepare(PATCH, emit=True)
    old_mt = {n: s.encode('utf8') for n, s in bundle['trees'][G.MODEL_NEW].items()}
    old_et = {n: s.encode('utf8') for n, s in bundle['trees'][G.EARLY_NEW].items()}
    old_model, old_early = obj(old_mt['SOURCE_TEMPLATE.json']), obj(old_et['SOURCE_TEMPLATE.json'])
    need(old_model['software_cases'] == 255 and len(old_model['files']) == 280, 'complete R38 prepared closure')
    pt, payload, payload_ref, payload_old = prepare_payload(G, authority_raw, reuse_raw)
    old_pt = G.own_bytes(payload_old)
    old_pt['SOURCE_MANIFEST.json'] = checked(PAYLOAD_OLD)
    et, early, early_ref = prepare_early(G, old_et, old_early, authority_raw)
    mt = dict(old_mt)
    model = copy.deepcopy(old_model)

    old_identity = old_model['runtime_identity']
    pairs = [(G.MODEL_NEW, MODEL_ROOT), (G.EARLY_NEW, EARLY_ROOT),
             (G.EARLY_OUT_NEW, EARLY_OUT), (old_model['output_root'], MODEL_OUT),
             (old_model['postconsumer_output_root'], POST_OUT), (G.P_NEW, P_NAME), (G.J_NEW, J_NAME),
             ('ACTUAL_BOUND_FIRSTDECODE_R38_REF3', 'ACTUAL_BOUND_FIRSTDECODE_R39_REF3'),
             ('FINAL_R38_MODEL_TEMPLATE_REF3', 'FINAL_R39_MODEL_TEMPLATE_REF3')]
    mt['packet_contract.py'] = rebind_packet(G, mt['packet_contract.py'], old_model['output_root'], old_identity)
    mt['model_snapshot_budget.py'] = edit(mt['model_snapshot_budget.py'], [(G.P_NEW, P_NAME, 1), (G.J_NEW, J_NAME, 1)], 'model/model_snapshot_budget.py')
    mt['test_firstdecode_owner.py'] = edit(mt['test_firstdecode_owner.py'], [(G.P_NEW, P_NAME, 2)], 'model/test_firstdecode_owner.py')
    for name, sc, cc in [('owner_overlay.py', 1, 1), ('phase_budget_r21.py', 0, 1),
                         ('plugin/qwen36_deltalog_service/admission.py', 2, 2),
                         ('test_actual017_binding.py', 1, 1), ('test_parser_parent_r24.py', 1, 1),
                         ('test_window058.py', 0, 2)]:
        mt[name] = clock(mt[name], 'model/' + name, sc, cc)
    mt['renewed_closed_reader101r19.py'] = clock(mt['renewed_closed_reader101r19.py'], 'model/renewed_closed_reader101r19.py', authorities=True)
    mt['window_overlay.py'] = assignment(clock(mt['window_overlay.py'], 'model/window_overlay.py', iso=True), 'AUTHORITY', AUTHORITY, 'model/window_overlay.py')
    mt['renewal_authority_snapshot.json'], mt['renewal_reuse_scope_snapshot.json'] = authority_raw, reuse_raw
    need(old_mt['software_fixtures/owner_overlay.py.txt'] == old_mt['owner_overlay.py'], 'exact current parser owner fixture predecessor')
    mt['software_fixtures/owner_overlay.py.txt'] = mt['owner_overlay.py']
    mt['software_dependencies/early_scan_owner.py'] = et['owner.py']
    mt['software_dependencies/early_scan_template.json'] = et['SOURCE_TEMPLATE.json']
    for name, body in pt.items():
        key = 'software_dependencies/payload_contract_mirror/' + name
        need(key in old_mt and old_mt[key] == old_pt[name], 'exact full original payload mirror ' + name)
        mt[key] = body
    refresh_phase_inverse(mt, old_mt)
    phase_row = inverse_row(old_mt['phase_budget_r21.py'], mt['phase_budget_r21.py'],
                            obj(checked(G.M_OLD_REF))['files']['phase_budget_r21.py'],
                            MODEL_ROOT + '/phase_budget_r21.py')
    mt['CONTINUATION_PHASE_INVERSE.json'] = serial(dict(schema='deltalog.continuation-phase-inverse/v1', batch_id=BATCH, phase_budget_r21=phase_row, historical_R23_proof_unchanged=True))
    before = "   actual=(P/name).read_bytes()\n   if name=='run_owned.py':"
    after = "   actual=(P/name).read_bytes()\n   if name=='phase_budget_r21.py':\n    row=json.loads((P/'CONTINUATION_PHASE_INVERSE.json').read_bytes())['phase_budget_r21']\n    self.assertEqual(actual,row['after_utf8'].encode());self.assertIs(row['complete_inverse'],True)\n    actual=row['before_utf8'].encode()\n    self.assertEqual((len(actual),hashlib.sha256(actual).hexdigest()),(row['original_ref']['bytes'],row['original_ref']['sha256']))\n   if name=='run_owned.py':"
    mt['test_payload_contract_r23.py'] = edit(mt['test_payload_contract_r23.py'],
        [("self.assertEqual(m['software_cases'],243)", "self.assertEqual(m['software_cases'],255)", 1),
         (before, after, 1)], 'model/test_payload_contract_r23.py')

    cold_module = module(old_mt['payload_contract_plan.py'], G.MODEL_NEW + '/payload_contract_plan.py', '_r39_exact_original_cold_plan')
    cold, cold_inverse = cold_module.rebind(obj(old_mt['payload_cold_readset_preflight.json']), PAYLOAD_OLD, payload_ref)
    mt['payload_cold_readset_preflight.json'] = serial(cold)
    replacements = {PAYLOAD_OLD['path']: (PAYLOAD_OLD, payload_ref),
                    old_model['early_software_policy']['prepared_owner_source']['path']: (old_model['early_software_policy']['prepared_owner_source'], early_ref)}
    # COMMANDS.json is a current nonexecuting index consumed by a real test.
    index_pairs = pairs + [(G.MODEL_OLD, MODEL_ROOT),
                            (obj(checked(G.M_OLD_REF))['output_root'], MODEL_OUT),
                            ('ACTUAL_BOUND_FIRSTDECODE_R36_REF3', 'ACTUAL_BOUND_FIRSTDECODE_R39_REF3')]
    mt['COMMANDS.json'] = serial(command_strings(obj(old_mt['COMMANDS.json']), replacements, index_pairs))
    early_commands = command_strings(obj(old_et['COMMANDS.json']), replacements, pairs)
    early_commands['prepared_owner_source'] = early_ref
    et['COMMANDS.json'] = serial(early_commands)
    early_commands_ref = ref(EARLY_ROOT + '/COMMANDS.json', et['COMMANDS.json'])
    spec = command_strings(obj(old_mt['COMMANDS_SPEC.json']), replacements, pairs)
    skeleton = spec['skeleton']
    skeleton['renewal_authority'] = AUTHORITY
    skeleton['unchanged_cutoff_epoch'] = CUT
    skeleton['phase_budget_registration']['cutoff_epoch'] = CUT
    skeleton['early_software']['source_template'] = early_ref
    skeleton['early_software']['commands_ref'] = early_commands_ref
    mt['COMMANDS_SPEC.json'] = serial(spec)

    plugin = obj(old_mt['plugin/SOURCE_TEMPLATE.json'])
    current_refs = source_refs(MODEL_ROOT, mt, old_model['files'])
    plugin = rewrite_refs(plugin, map_refs(old_model['files'], current_refs))
    plugin['root'] = MODEL_ROOT + '/plugin'
    plugin['window'] = dict(start=START, cutoff=CUT)
    mt['plugin/SOURCE_TEMPLATE.json'] = serial(plugin)
    own_names = set(old_model['files']) | {'CONTINUATION_PHASE_INVERSE.json'}
    current_refs = source_refs(MODEL_ROOT, mt, own_names)
    own_map = map_refs(old_model['files'], current_refs)
    model = rewrite_refs(model, own_map)
    model['root'], model['output_root'], model['postconsumer_output_root'] = MODEL_ROOT, MODEL_OUT, POST_OUT
    model['runtime_identity'] = IDENTITY
    model['window'] = dict(start=START, cutoff=CUT)
    model['authority'], model['authority_sha256'], model['cutoff_epoch'] = AUTHORITY, AUTHORITY['sha256'], CUT
    model['phase_budget_registration']['cutoff_epoch'] = CUT
    model['files'] = current_refs
    model['early_software_policy']['prepared_owner_source'] = early_ref
    model['early_software_policy']['owner_output_root'] = early['output_root']
    model['early_software_policy']['required_payload_source'] = payload_ref
    model['prepared_identity_repair']['actual_child'] = early['files']['recover.py']
    model['firstdecode_contract']['payload_source'] = payload_ref
    model['diagnostic_geometry_observation']['payload_source'] = payload_ref
    # The old R23 payload repair record and old48h authority_ref are provenance.
    # Their exact old references are retained instead of rewritten as current.
    model['continuation_batch'] = dict(batch_id=BATCH, authority_ref=AUTHORITY, reuse_scope_ref=REUSE,
        start_epoch=START, cutoff_epoch=CUT, predecessor_preparer=GENERATOR, predecessor_patch_source=PATCH,
        predecessor_payload=PAYLOAD_OLD,
        r38_readonly_preparation_receipt_sha256=hashlib.sha256(serial(bundle['receipt'])).hexdigest(),
        r38_preparation_was_memory_only=True, cold_program_inverse=cold_inverse,
        new_payload=payload_ref, active_child=early['files']['recover.py'],
        old_sources_and_failure_evidence_unchanged=True, all_original_tests_retained=True,
        actual_sameimage_early_pass=None, bound_model_created=False, qualified=False)
    for value in (AUTHORITY, REUSE, GENERATOR, PATCH, PAYLOAD_OLD):
        if value not in model['dependencies']:
            model['dependencies'].append(value)
    mt['SOURCE_TEMPLATE.json'] = serial(model)
    model_ref = ref(MODEL_ROOT + '/SOURCE_TEMPLATE.json', mt['SOURCE_TEMPLATE.json'])
    final = copy.deepcopy(skeleton)
    need(final['template'] == {'$reviewed_template_ref': True}
         and final['bind']['argv'][6] == final['cheap_prebind']['argv'][6] == MARK, 'original noncircular ticket seams')
    final['template'] = model_ref
    final['bind']['argv'][6] = final['cheap_prebind']['argv'][6] = model_ref['sha256']
    mt['COMMANDS_FINAL.json'] = serial(final)
    trees = dict(model=mt, early=et, payload=pt)
    report = audit(G, dict(model=old_mt, early=old_et, payload=old_pt), trees, model, early, payload,
                   model_ref, early_ref, payload_ref, cold_module)
    for value in (AUTHORITY, REUSE, GENERATOR, PATCH, PAYLOAD_OLD):
        checked(value)
    receipt = dict(schema='deltalog.r39-continuation-prepared-package/v1', batch_id=BATCH,
        authority_ref=AUTHORITY, reuse_scope_ref=REUSE, predecessor_generator=GENERATOR, patch_ref=PATCH,
        model_template=model_ref, early_template=early_ref, payload_source=payload_ref,
        early_commands=early_commands_ref, cutoff_epoch=CUT, latest_full_model_entry_epoch=CUT - 3600,
        model_cases=255, early_cases=253, payload_cases=26, audit=report,
        consumer_preparation_pending=True, planned_consumer_root=CONSUMER_ROOT,
        planned_consumer_output=CONSUMER_OUT, old_model_postconsumer_output_must_remain_absent=POST_OUT,
        model_source_created=False, early_bound_source_created=False, NPU=False, qualified=False)
    roots = dict(model=MODEL_ROOT, early=EARLY_ROOT, payload=PAYLOAD_ROOT)
    original = dict(model=obj(checked(G.M_OLD_REF)), early=obj(checked(G.E_OLD_REF)), payload=payload_old)
    index = {}
    for alias, tree in trees.items():
        index[alias] = []
        for name, raw in sorted(tree.items()):
            previous = original[alias]['files'].get(name)
            if alias == 'payload' and name == 'SOURCE_MANIFEST.json':
                previous = PAYLOAD_OLD
            same = previous if previous is not None and all(ref('', raw)[k] == previous[k] for k in ('bytes', 'sha256')) else None
            index[alias].append(dict(relative_name=name, ref=ref(roots[alias] + '/' + name, raw), unchanged_original_ref=same))
    package_id = hashlib.sha256(serial(dict(receipt=receipt, index=index))).hexdigest()
    return dict(receipt=receipt, package_id=package_id, index=index,
                trees={roots[a]: {n: b.decode('utf8') for n, b in sorted(t.items())} for a, t in trees.items()})


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--emit-patch', action='store_true')
    parser.add_argument('--receipt', action='store_true')
    args = parser.parse_args()
    need(not (args.emit_patch and args.receipt), 'one preparation output mode')
    if not (args.emit_patch or args.receipt):
        print(json.dumps(dict(enabled=False, read_only=True, batch_id=BATCH, source_tree_created=False, NPU=False, qualified=False)))
        return 0
    result = prepare()
    if args.receipt:
        index = result['index']
        result = dict(receipt=result['receipt'], package_id=result['package_id'],
                      file_counts={a: len(rows) for a, rows in index.items()},
                      index_sha256=hashlib.sha256(serial(index)).hexdigest(),
                      structured_patch_entries={a: [row for row in rows if
                          row['unchanged_original_ref'] is None or
                          Path(row['relative_name']).name in {'SOURCE_TEMPLATE.json', 'SOURCE_MANIFEST.json', 'SOURCE_BOUND.json'} or
                          Path(row['relative_name']).name.startswith('COMMANDS')]
                          for a, rows in index.items()})
        need(len(serial(result)) <= 128 * 1024, 'bounded read-only receipt')
    sys.stdout.buffer.write(serial(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
