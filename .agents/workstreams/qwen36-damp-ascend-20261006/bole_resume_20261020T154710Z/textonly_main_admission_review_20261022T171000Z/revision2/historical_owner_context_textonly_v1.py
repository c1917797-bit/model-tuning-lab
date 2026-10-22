"""Pure historical create/inspect contexts; never installs an old controller.

Every input is read through the caller's exact whole-file readset. Private
namespaces use the original full function ASTs and original cap32 provider.
The active new S/c/external module is fingerprinted, never rebound or restored.
Only the eight registered cpu-preflight/dense historical owners are in scope.
"""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import types


BASE = '/cache/cch/qwen36-paper-preparation-20261007/sparse/adakv-tp4-model-once-v1-025'
ORIGINAL = {
    'model_contract': dict(path=BASE+'/model_contract.py', bytes=13660,
        sha256='82243c277890aef7c24ea5eb5fbfa0658b314a39c01d7b2a7ddf34b2bf363e9f'),
    'safety_host': dict(path=BASE+'/safety_host.py', bytes=22338,
        sha256='20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30'),
    'host_once': dict(path=BASE+'/host_once.py', bytes=18170,
        sha256='36844e41895b95e810b54ecae32994a96b21258ae8ad8d88fccaac19f035cf8c')}
SHARED = {
    'external025.py': (5198, '8b65bbd0518a81b194459e087dd6a6003dcfbb07151940c031aaec31d29e3c62'),
    'g2_host_adapter.py': (4399, '3df2119e322ea800efb1100d3c4dcfbea4760cafaea5689a7ff066c3f2f815b6'),
    'cap48_provider.py': (2056, '51ec78ed1c1d9b9aab60f749988b799c8ec39ebe077eb5638aab86704440ad2a'),
    # Full actual installers were independently reopened and statically read.
    # Observer changes only Controller.observe; scanner changes only resources.
    'observer_race_repair.py': (1959, 'f7d8fa2ea99cedb7373273a625dce39802a45d24fa291371a925d145cd28a609'),
    'output_scan131r8.py': (6239, 'db7f8d9301ef7225aebdc1cd12c07adaa3edcb125b2c173d03154aa0c47e5daa')}
OLD_OWNED = (3579, '4ff2d6f19d87897ded40a860ee37f1225ca428594720d4ba8c8c238256f77bb7')
CONTINUATION_OWNED = (3579, 'fa39a66478b766260cee0709d20fe69c30303cb1ba65ca0a7dfaf99ab162ee89')
NEW_OWNED = None  # Bind whole actual text-only owned_substrate bytes after source review.
CONTINUATION_SOURCE = {'bytes': 1638841, 'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-boundary-ON-v3-continuation_20261022T120055Z/SOURCE_BOUND.json', 'sha256': 'd28e57b46ae913182ff8ebc0f35a1c631f12fce647376af495a4b59c4d8e10df'}
CONTINUATION_CIDS = {'0a5ed053d4d08915b8748e0f6facbc6f3fad820ff1f46d1eefe0f4bc6626d955', 'eb21e660585ed4e758476504bc0b409a02b777d875516e2925f00a9e8efaa8cf'}


def need(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def functions(body, names, parent=None):
    tree = ast.parse(body)
    nodes = tree.body
    if parent is not None:
        parents = [n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == parent]
        need(len(parents) == 1, 'one original exact parent function')
        nodes = parents[0].body
    selected = [n for n in nodes if isinstance(n, ast.FunctionDef) and n.name in names]
    need(len(selected) == len(names) and {n.name for n in selected} == set(names),
         'all full original function ASTs found exactly once')
    return selected


def assignments(body, names):
    selected = []
    for node in ast.parse(body).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in names:
                selected.append(node)
    need(len(selected) == len(names), 'all original constant assignments exactly once')
    return selected


def evaluate(nodes, namespace, filename):
    exec(compile(ast.Module(body=nodes, type_ignores=[]), filename, 'exec', dont_inherit=True), namespace)


def module(body, name, filename):
    value = types.ModuleType(name)
    value.__file__ = filename
    exec(compile(body, filename, 'exec', dont_inherit=True), value.__dict__)
    return value


def active_fingerprint(S):
    external = sys.modules.get('external025')
    need(external is not None and getattr(S, '_EXTERNAL', None) is not None,
         'genuine active current external/adapter context already installed')
    return dict(
        external_id=id(external), external_globals=id(vars(external)),
        external_OUT=str(external.OUT), external_environment=id(external.environment),
        external_environment_globals=id(external.environment.__globals__),
        external_LOG=canonical(external.LOG).hex(), S_globals=id(vars(S)),
        S_external=id(S._EXTERNAL), S_external_environment=id(S._EXTERNAL.environment),
        functions={name: (id(getattr(S, name)), id(getattr(S, name).__globals__))
                   for name in ('create_argv', 'validate_inspect', 'labels', 'device_map', 'environment')},
        resources=(S.MEM, S.RESERVE, S.HOST_MEM, S.WORKSPACE, S.PHASE, S.CLEANUP,
                   S.OWNER, tuple(S.PHYSICAL)),
        contract=(id(S.c), str(S.c.ROOT), S.c.IMAGE, S.c.GIB, id(S.c.require),
                  S.c.CUTOFF, S.c.CUT))


def build(readset, historical, owned, current, active_S):
    before = active_fingerprint(active_S)
    need(owned['arm'] in ('cpu-preflight', 'dense'), 'only original eight nonconsumer historical roles')
    output, root = Path(historical['output_root']), Path(historical['root'])
    leaf = Path(owned['mounts']['/adakv-results'][0])
    need(output.is_absolute() and root.is_absolute() and leaf.parent == output and
         leaf.name == owned['arm'] and
         Path(owned['source']['path']) == root/'SOURCE_BOUND.json' and
         output != Path(current['output_root']), 'exact old source/output/owned-leaf binding')
    need(historical['resources'] == current['resources'] and
         historical['stream_resource_profile'] == current['stream_resource_profile'],
         'unchanged actual historical and current resource/profile values')
    bodies, refs = {}, []
    for name, (size, digest) in SHARED.items():
        old_ref, new_ref = historical['files'][name], current['files'][name]
        need(Path(old_ref['path']) == root/name and
             Path(new_ref['path']) == Path(current['root'])/name and
             old_ref['sha256'] == new_ref['sha256'] == digest and
             (size is None or old_ref['bytes'] == new_ref['bytes'] == size),
             'exact separately reviewed whole shared helper and source-owned paths')
        old_body, new_body = readset.read(old_ref), readset.read(new_ref)
        need(old_body == new_body, 'whole original/current helper bodies identical')
        bodies[name] = old_body
        refs += [old_ref, new_ref]
    historical_owned_pin = OLD_OWNED
    if owned['cid'] in CONTINUATION_CIDS:
        need(owned['source'] == CONTINUATION_SOURCE and
             historical['root'] == str(Path(CONTINUATION_SOURCE['path']).parent),
             'exact two later continuation owners bind their genuine historical substrate')
        historical_owned_pin = CONTINUATION_OWNED
    else:
        need(owned['source'] != CONTINUATION_SOURCE,
             'later historical substrate is never accepted for another owner')
    need(NEW_OWNED is not None, 'current whole text-only substrate pin is not frozen')
    for source, expected, key in ((historical, historical_owned_pin, 'old_owned'), (current, NEW_OWNED, 'new_owned')):
        reference = source['files']['owned_substrate.py']
        need(Path(reference['path']) == Path(source['root'])/'owned_substrate.py' and
             (reference['bytes'], reference['sha256']) == expected, 'exact whole old/new owned substrate')
        bodies[key] = readset.read(reference)
        refs.append(reference)
    old_env = functions(bodies['old_owned'], {'environment'}, parent='load')
    new_env = functions(bodies['new_owned'], {'environment'}, parent='load')
    need(ast.dump(old_env[0], include_attributes=False) == ast.dump(new_env[0], include_attributes=False),
         'whole original nested base-environment function unchanged by continuation')
    for name in ('old_owned', 'new_owned'):
        namespace = {}
        evaluate(assignments(bodies[name], {'BASE', 'REFS'}), namespace, name)
        need(namespace['REFS'] == ORIGINAL, 'both substrates bind the same complete genuine025 foundation')
    raw_c, raw_s = readset.read(ORIGINAL['model_contract']), readset.read(ORIGINAL['safety_host'])
    readset.read(ORIGINAL['host_once'], keep=False)
    # Construct original constants and require in a private object, without
    # executing model_contract imports/gates or mutating active c.
    c = types.ModuleType('_historical_original_contract')
    c.__dict__['Path'] = Path
    evaluate(assignments(raw_c, {'ROOT', 'GIB', 'IMAGE'}) + functions(raw_c, {'require'}),
             c.__dict__, ORIGINAL['model_contract']['path'])
    need((c.ROOT, c.GIB, c.IMAGE) == (active_S.c.ROOT, active_S.c.GIB, active_S.c.IMAGE),
         'original exact contract values, independent of active clock')
    S = types.ModuleType('_historical_original_safety')
    S.__file__ = ORIGINAL['safety_host']['path']
    S.__dict__.update(c=c, Path=Path, re=re)
    constants = {'DOCKER', 'SMI', 'PRLIMIT', 'MEM', 'HOST_MEM', 'RESERVE', 'WORKSPACE',
                 'PHASE', 'CLEANUP', 'OWNER', 'PHYSICAL'}
    pure = {'environment', 'labels', 'device_map', 'create_argv', 'validate_inspect'}
    evaluate(assignments(raw_s, constants) + functions(raw_s, pure), S.__dict__, S.__file__)
    # The genuine provider first checks its original64/8.5/.5 constants and
    # whole safety source, then changes only private MEM32/RESERVE8. No host
    # memory admission is made by constructing these historical validators.
    cap = module(bodies['cap48_provider.py'], '_historical_cap32', historical['files']['cap48_provider.py']['path'])
    cap_proof = cap.prepare(S, c)
    need((S.MEM, S.RESERVE, S.HOST_MEM, S.WORKSPACE, S.PHYSICAL) ==
         (active_S.MEM, active_S.RESERVE, active_S.HOST_MEM, active_S.WORKSPACE, active_S.PHYSICAL),
         'same actual private/current cap32 globals, not a new host73GiB threshold')
    load = functions(bodies['old_owned'], {'load'})[0]
    scoped = [node for node in load.body if isinstance(node, ast.Assign) and len(node.targets) == 1
              and isinstance(node.targets[0], ast.Attribute) and isinstance(node.targets[0].value, ast.Name)
              and node.targets[0].value.id == 'S' and node.targets[0].attr in ('PHASE', 'CLEANUP', 'OWNER')]
    need(len(scoped) == 3, 'original three owner scope assignments')
    evaluate(scoped, dict(S=S), historical['files']['owned_substrate.py']['path'])
    need((S.PHASE, S.CLEANUP, S.OWNER) == (active_S.PHASE, active_S.CLEANUP, active_S.OWNER),
         'original identical owner and phase scope')
    S.original_env = S.environment
    evaluate(old_env, S.__dict__, historical['files']['owned_substrate.py']['path'])
    external = module(bodies['external025.py'], '_historical_private_external', historical['files']['external025.py']['path'])
    external.OUT = output  # This private module is never placed in sys.modules.
    adapter = dict()
    evaluate(assignments(bodies['g2_host_adapter.py'], {'CPU_PROFILE'}) +
             functions(bodies['g2_host_adapter.py'], {'derive'}), adapter,
             historical['files']['g2_host_adapter.py']['path'])
    need(adapter['CPU_PROFILE'] == historical['stream_resource_profile'], 'whole original CPU profile')
    text, pairs = adapter['derive'](raw_s, external)
    nested = functions(bodies['g2_host_adapter.py'], {'environment'}, parent='install')
    first = nested[0].body[0]
    expected = ast.parse("if e['arm'] != 'stream-consumer':\n return external.environment(e)\n").body[0]
    need(ast.dump(first, include_attributes=False) == ast.dump(expected, include_attributes=False),
         'exact original nonconsumer branch for the only accepted historical roles')
    # Compile the full original adapter environment function; the strict role
    # binding below ensures its unchanged nonconsumer branch is taken.
    env_scope = dict(external=external, C=types.SimpleNamespace(need=need), m=historical,
                     channel=Path(historical['stream_channel_root']),
                     receipt=Path(historical['model_receipt_root']))
    evaluate(nested, env_scope, historical['files']['g2_host_adapter.py']['path'])
    S._EXTERNAL = types.SimpleNamespace(environment=env_scope['environment'], LOG=external.LOG)
    evaluate(functions(text, {'create_argv', 'validate_inspect'}), S.__dict__, S.__file__+'#historical-original-G2')
    need(all(getattr(S, name).__globals__ is vars(S) for name in pure) and
         external.environment.__globals__ is vars(external) and external is not sys.modules['external025'] and
         vars(S) is not vars(active_S) and c is not active_S.c,
         'all historical function globals/output/contract isolated from active new controller')
    need(active_fingerprint(active_S) == before, 'active new controller untouched during historical construction')
    fixed = {key: owned[key] for key in ('cid', 'name', 'image', 'arm', 'source', 'host_sha256', 'guest_cpus')}

    def invoke(name, *args):
        expected_owner = args[-1]
        need(all(expected_owner[key] == value for key, value in fixed.items()),
             'context bound to one exact historical owner; no stream/foreign role reuse')
        need(active_fingerprint(active_S) == before, 'active context unchanged before historical validation')
        try:
            return getattr(S, name)(*args)
        finally:
            need(active_fingerprint(active_S) == before, 'active context unchanged after historical validation')

    proof = dict(schema='bole.exact-private-historical-owner-context/v1', cid=owned['cid'],
        source=owned['source'], historical_output_root=str(output), active_output_root=str(current['output_root']),
        helper_refs=refs, original_refs=list(ORIGINAL.values()), cap32=cap_proof,
        original_adapter_delta=pairs, all_function_bodies_original=True,
        active_globals_never_rebound=True, NPU=False, resources_admitted=False)
    return types.SimpleNamespace(create_argv=lambda e: invoke('create_argv', e),
        validate_inspect=lambda x, e: invoke('validate_inspect', x, e), proof=proof)
