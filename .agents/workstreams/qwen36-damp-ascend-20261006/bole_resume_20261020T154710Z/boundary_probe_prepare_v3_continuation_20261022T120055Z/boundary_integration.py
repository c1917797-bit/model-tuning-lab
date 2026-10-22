"""Pure exact-source renderers for one reviewed ON boundary diagnostic child.

No file write, import of model code, owner creation, or device operation.
The caller supplies helper hashes only after independent MAIN review.
"""
import ast
import hashlib
import json

WORKSTREAM = '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z'
PARENT_ROOT = WORKSTREAM + '/bole_performance_profile_prepare_20261021/successor_layer/bound-short-ON-v2'
PARENT_REF = dict(path=PARENT_ROOT + '/SOURCE_BOUND.json', bytes=1503149,
    sha256='a285ac43d953cf257255ec4848d8719b613010bf339491e2a39d20d2f3b73b8f')
OLD_SHORT_DELTA_REF = dict(path=PARENT_ROOT + '/short_binding_delta.py', bytes=1851,
    sha256='4406fdeaff1965c2c3ce2adf859b1969bd29c102344c1f51204da037b81470d9')
OLD_VALIDATOR_REF = dict(path=PARENT_ROOT + '/performance_validate.py', bytes=6933,
    sha256='c45e114ab03fd35a47c85c8dd6f70bb71bbc406fa08be151222d082d8d57d824')
OLD_SOFTWARE_COORDINATOR_REF = dict(path=PARENT_ROOT + '/performance_software_stages.py',
    bytes=5440, sha256='b862faa3ac7763c34af4055e48fef2c3d1140eea023e10de71d73770d13f05cd')
CHILD_ROOT = WORKSTREAM + '/bound-boundary-ON-v3-continuation_20261022T120055Z'
CHILD_OUTPUT = '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z'
CHILD_BATCH = 'MAIN-BOLE-BOUNDARY-CONTINUATION-20261022T120055Z-ON-V3'
CHILD_AUTHORITY_SCOPE = 'ON only; two bounded eight-token requests; native-boundary and projection-callsite diagnosis; no performance admission'
PREPARATION_ROOT = WORKSTREAM + '/boundary_probe_prepare_v3_continuation_20261022T120055Z'
AUTHORIZATION_REF = dict(path=PREPARATION_ROOT + '/AUTHORIZATION_CONTINUATION.json',
    bytes=1886, sha256='e0808a184326bfcf70e5ce158c7a00dac03b5f7aeab2aabc99b7c99618e40fac')
AUTHORIZATION_DOCUMENT_REF = dict(path=PREPARATION_ROOT + '/AUTHORIZATION_CONTINUATION.md',
    bytes=3956, sha256='3bd808a5012bbe447b2a48bbc611116771f9f65a0b40f8c99e02c702000de0ba')
START_EPOCH = 1792670455
CUTOFF_EPOCH = 1792692055
CUTOFF_ISO = '2026-10-22T18:00:55+00:00'
OLD_REPORT_CUTOFF = 1792672721
PHASE_SECONDS = 3600
CLEANUP_SECONDS = 180
ORIGINAL_VALIDATOR_AUTHORITY_GATE = " C.need(authority['schema']=='bole.short-state-authority/v1' and authority['start_epoch']==1792586321 and authority['cutoff_epoch']==1792672721 and authority['phase_seconds']==3600 and authority['cleanup_seconds']==180,'explicit new user24h authority; fixed phase cleanup')\n"
CONTINUATION_VALIDATOR_AUTHORITY_GATE = " C.need(authority['schema']=='bole.short-state-authority/v1' and authority['start_epoch']==1792670455 and authority['cutoff_epoch']==1792692055 and authority['phase_seconds']==3600 and authority['cleanup_seconds']==180,'explicit user continuation; finite new batch with fixed phase cleanup')\n"
OLD_RUNTIME = ('service_runner.py', 'live_owner.py', 'bole_performance_profile.py',
    'performance_service_client.py', 'host_service.py', 'performance_host.py', 'command_contract.py')
EXTRA_RUNTIME = ('prefill_tail.py', 'model_process_calibration.py', 'g3_budget.py')
RUNTIME = OLD_RUNTIME + EXTRA_RUNTIME
REVIEWED_HELPERS = ('boundary_probe_v1.py', 'boundary_delta.py',
                    'boundary_integration.py', 'boundary_validation.py', 'projection_probe_v1.py')
FLAG = 'BOLE_NATIVE_BOUNDARY_PROBE_ENABLE'
MANIFEST_FIELDS = ('boundary_parent_source', 'boundary_probe_profile',
                   'boundary_reviewed_helpers', 'boundary_control_refs', 'projection_probe_profile')


def need(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('utf-8')


def pinned_text(text, reference):
    need(type(text) is str, 'source text must be an exact decoded string')
    data = text.encode('utf-8')
    need(len(data) == reference['bytes'] and hashlib.sha256(data).hexdigest() == reference['sha256'],
         'exact actual old ON source bytes: ' + reference['path'])
    return text


def once(text, before, after):
    need(text.count(before) == 1, 'one exact source fragment: ' + before[:72])
    return text.replace(before, after, 1)


def check_continuation_payload(value):
    """Check the fixed recorded authority; callers also check both whole Refs."""
    expected = dict(schema='bole.explicit-continuation-authorization/v1',
        authority_kind='explicit_user_continuation', user_statement='可以继续穿刺一直到成功',
        document=AUTHORIZATION_DOCUMENT_REF, old_window_extended=False,
        old_hard_report_deadline_utc='2026-10-22T12:38:41+00:00',
        internal_batch_start_epoch=START_EPOCH, internal_batch_cutoff_epoch=CUTOFF_EPOCH,
        internal_batch_cutoff_utc=CUTOFF_ISO, internal_batch_limit_seconds=21600,
        internal_limit_is_not_user_promised_result_window=True,
        phase_seconds=PHASE_SECONDS, cleanup_seconds=CLEANUP_SECONDS,
        whole_prepare_admission_seconds=3780, batch_id=CHILD_BATCH,
        model_path='/cache/efim/Qwen3.6-27B', physical_npus=[4, 5, 6, 7],
        protected_physical_npus=[0, 1, 2, 3], tensor_parallel_size=4,
        scope=CHILD_AUTHORITY_SCOPE, source_root=CHILD_ROOT, output_root=CHILD_OUTPUT,
        numerical_thresholds_unchanged=True, formal_performance_admitted=False,
        resource_owner_created=False, source_frozen=False)
    need(type(value) is dict and all(type(value.get(k)) is type(v) and value[k] == v
                                   for k, v in expected.items()),
         'exact explicit continuation, independent finite batch, unchanged limits and protected devices')
    return value


def continuation_authority(old_authority, old_authority_ref):
    """New ticket only; the exact original ticket remains an immutable input."""
    need(type(old_authority) is dict and old_authority['schema'] == 'bole.short-state-authority/v1'
         and old_authority['start_epoch'] == 1792586321
         and old_authority['cutoff_epoch'] == OLD_REPORT_CUTOFF
         and old_authority['cutoff_iso'] == '2026-10-22T12:38:41+00:00'
         and old_authority['phase_seconds'] == PHASE_SECONDS
         and old_authority['cleanup_seconds'] == CLEANUP_SECONDS,
         'fixed original completed short authority and unchanged owner budgets')
    return dict(old_authority, batch_id=CHILD_BATCH, scope=CHILD_AUTHORITY_SCOPE,
        user_authorization_ref=AUTHORIZATION_REF, historical_authority_ref=old_authority_ref,
        start_epoch=START_EPOCH, cutoff_epoch=CUTOFF_EPOCH, cutoff_iso=CUTOFF_ISO)


def render_current_software_coordinator(old_text):
    """Only three literal cutoffs change in the whole pinned current coordinator."""
    text = pinned_text(old_text, OLD_SOFTWARE_COORDINATOR_REF)
    need(text.count('1792672721') == 3 and str(CUTOFF_EPOCH) not in text,
         'exact three original software cutoff operands')
    text = text.replace('1792672721', str(CUTOFF_EPOCH))
    need(text.replace(str(CUTOFF_EPOCH), '1792672721') == old_text,
         'exact inverse coordinator authority rebind; every other byte unchanged')
    ast.parse(text)
    return text


def normalize_reviewed_helpers(reviewed_helpers):
    need(type(reviewed_helpers) is dict and set(reviewed_helpers) == set(REVIEWED_HELPERS),
         'exact five independently reviewed diagnostic helper pins')
    result = {}
    for name in sorted(reviewed_helpers):
        pin = reviewed_helpers[name]
        need(type(pin) is dict and set(pin) == {'bytes', 'sha256'}
             and type(pin['bytes']) is int and 0 < pin['bytes'] <= 2**22
             and type(pin['sha256']) is str and len(pin['sha256']) == 64
             and all(char in '0123456789abcdef' for char in pin['sha256']),
             'typed complete reviewed helper pin: ' + name)
        result[name] = dict(bytes=pin['bytes'], sha256=pin['sha256'])
    return result


def render_short_delta(old_text):
    """Retain old runtime logic and compose exactly one reviewed boundary delta."""
    text = pinned_text(old_text, OLD_SHORT_DELTA_REF)
    text = once(text, 'import prepare_short_gate as P\n',
                'import prepare_short_gate as P\nimport boundary_delta\n')
    nodes = [node for node in ast.parse(text).body if isinstance(node, ast.Assign)
             and any(isinstance(target, ast.Name) and target.id == 'RUNTIME' for target in node.targets)]
    need(len(nodes) == 1 and ast.literal_eval(nodes[0].value) == OLD_RUNTIME,
         'exact original seven-file runtime declaration')
    text = once(text, ast.get_source_segment(text, nodes[0]), 'RUNTIME = ' + repr(RUNTIME))
    text = once(text, 'def runtime(old):\n',
                "def runtime(old):\n P.need(type(old) is dict and set(old)==set(RUNTIME),'complete boundary runtime input set')\n")
    text = once(text, ' return out\n',
                " out=boundary_delta.runtime(old,out)\n"
                " P.need(type(out) is dict and set(out)==set(RUNTIME),'complete boundary runtime output set')\n"
                ' return out\n')
    ast.parse(text)
    return text


def render_validator(old_text, reviewed_helpers):
    """Add exact helper pins/lineage and rebind one explicit authority predicate."""
    text = pinned_text(old_text, OLD_VALIDATOR_REF)
    reviewed = normalize_reviewed_helpers(reviewed_helpers)
    line = "SCHEMA='bole.performance-successor-source-validation/v1'\n"
    text = once(text, line, line + 'BOUNDARY_REVIEWED_FILES = ' + repr(reviewed) + '\n')
    line = " m=C.obj(sr);parent=C.obj(P.PIN);audit=C.obj(AUDIT);root=Path(m['root'])\n"
    text = once(text, line, line + ' import boundary_validation as BV\n'
                + ' BV.validate(C,sr,m,reviewed=BOUNDARY_REVIEWED_FILES)\n')
    text = once(text, ORIGINAL_VALIDATOR_AUTHORITY_GATE, CONTINUATION_VALIDATOR_AUTHORITY_GATE)
    ast.parse(text)
    return text
