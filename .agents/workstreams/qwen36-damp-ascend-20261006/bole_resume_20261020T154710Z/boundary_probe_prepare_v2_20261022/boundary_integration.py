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
CHILD_ROOT = WORKSTREAM + '/bound-boundary-ON-v2-20261022T100000Z'
CHILD_OUTPUT = '/opt/host/vnf/austinov/run-bole-boundary-ON-v2-20261022T100000Z'
CHILD_BATCH = 'MAIN-BOLE-BOUNDARY-20261022T100000Z-ON-V2'
CHILD_AUTHORITY_SCOPE = 'ON only; two bounded eight-token requests; native-boundary and projection-callsite diagnosis; no performance admission'
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
    """Add exact helper pins and one child-lineage hook; keep every old gate."""
    text = pinned_text(old_text, OLD_VALIDATOR_REF)
    reviewed = normalize_reviewed_helpers(reviewed_helpers)
    line = "SCHEMA='bole.performance-successor-source-validation/v1'\n"
    text = once(text, line, line + 'BOUNDARY_REVIEWED_FILES = ' + repr(reviewed) + '\n')
    line = " m=C.obj(sr);parent=C.obj(P.PIN);audit=C.obj(AUDIT);root=Path(m['root'])\n"
    text = once(text, line, line + ' import boundary_validation as BV\n'
                + ' BV.validate(C,sr,m,reviewed=BOUNDARY_REVIEWED_FILES)\n')
    ast.parse(text)
    return text
