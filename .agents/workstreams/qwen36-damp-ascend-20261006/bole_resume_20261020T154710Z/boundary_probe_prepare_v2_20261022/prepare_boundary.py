"""Fresh source-only ON boundary diagnostic; no owners, containers, or devices.

This assembler keeps the original short numerical/runtime/clock gates and uses
the reviewed exact observer delta.  A successfully frozen source is not NPU
qualification and is not permission for performance or task accuracy runs.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
PARENT = dict(path=str(WS / 'bole_performance_profile_prepare_20261021/successor_layer/bound-short-ON-v2/SOURCE_BOUND.json'),
              bytes=1503149, sha256='a285ac43d953cf257255ec4848d8719b613010bf339491e2a39d20d2f3b73b8f')
ROOT = WS / 'bound-boundary-ON-v2-20261022T100000Z'
OUT = Path('/opt/host/vnf/austinov/run-bole-boundary-ON-v2-20261022T100000Z')
BATCH = 'MAIN-BOLE-BOUNDARY-20261022T100000Z-ON-V2'
HELPERS = ('boundary_probe_v1.py', 'boundary_delta.py',
           'boundary_integration.py', 'boundary_validation.py', 'projection_probe_v1.py')
CLOCK_FILES = ('bind_model.py', 'contract090.py', 'g2_cold_clock.py',
               'g2_software_stages.py', 'owned_substrate.py', 'worker_bootstrap.py')


def need(value, message):
    if not value:
        raise ValueError(message)


def ref(path):
    path = Path(path)
    need(path.is_absolute() and path.is_file() and
         not any(p.is_symlink() for p in (path, *path.parents)),
         'ordinary absolute source input')
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def checked(reference):
    need(type(reference) is dict and set(reference) == {'path', 'bytes', 'sha256'} and
         ref(reference['path']) == reference, 'exact complete immutable source Ref')
    return Path(reference['path'])


def obj(reference):
    return json.loads(checked(reference).read_bytes())


def exclusive(path, value):
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()
    with Path(path).open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return ref(path)


def clock(text, authority):
    return (text.replace('1792511230', str(authority['start_epoch']))
            .replace('1792597630', str(authority['cutoff_epoch']))
            .replace('2026-10-21T15:47:10+00:00', authority['cutoff_iso'])
            .replace('MAIN-BOLE-CONTINUE-20261020T154710Z', authority['batch_id']))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def freeze(review_ref):
    need(HERE == WS / 'boundary_probe_prepare_v2_20261022', 'assigned preparation directory')
    need(not ROOT.exists() and not OUT.exists() and not Path(str(OUT) + '-CPU').exists(),
         'fresh diagnostic source and both output identities; no overwrite or failed rerun')
    need(time.time() + 3780 < 1792672721, 'whole original phase and cleanup inside hard cutoff')
    review = obj(review_ref)
    need(review['schema'] == 'bole.boundary-probe-main-source-review/v1' and
         review['source_only'] is True and review['NPU_executed'] is False and
         review['paired_gate_pass'] is False and review['performance_admitted'] is False and
         review['parent'] == PARENT and set(review['helpers']) == set(HELPERS),
         'explicit exact reviewed source-only diagnostic scope')
    old = obj(PARENT)
    parent = obj(old['short_parent_source'])
    audit = obj(old['short_parent_audit'])
    need(old['short_state_digest_profile']['observation'] == 'ON' and
         'observation_only_profile' not in old and old['default_enabled'] is False,
         'actual retained ON parent and default-disabled plugin')
    readset = {}
    def include(reference):
        checked(reference)
        need(reference['path'] not in readset or readset[reference['path']] == reference,
             'unique exact source path identity')
        readset[reference['path']] = reference
    historical_boundary_auditor = dict(path=str(WS / 'boundary_probe_prepare_v1_20261022/audit_boundary_source.py'),
        bytes=4631, sha256='318abb0246fce440ba877c8428cbcc1dd90caea7846be76a884c5e26cb4b5533')
    for reference in [PARENT, old['prepared_template'], review_ref, ref(__file__), historical_boundary_auditor,
                      ref(HERE / 'audit_boundary_source.py'),
                      *old['files'].values(), *old['dependencies'],
                      *audit['readset'], *review['control_refs']]:
        include(reference)
    pins = {}
    for name in HELPERS:
        source = review['helpers'][name]
        need(Path(source['path']) == HERE / name, 'reviewed helper belongs to this preparation')
        include(source)
        pins[name] = {key: source[key] for key in ('bytes', 'sha256')}
    # The preparation imports pure source renderers only; no runtime entrypoint.
    sys.path.insert(0, str(HERE))
    sys.path.insert(1, old['root'])
    import boundary_integration as BI
    import boundary_delta as BD
    import boundary_probe_v1 as BP
    import projection_probe_v1 as PP
    import performance_binding_delta as B
    import prepare_short_gate as P
    need(P.PIN == old['short_parent_source'], 'original qualified numerical lineage')
    authority = copy.deepcopy(obj(old['authority_ref']))
    authority.update(batch_id=BATCH,
        scope='ON only; two bounded eight-token requests; native-boundary and projection-callsite diagnosis; no performance admission')
    need(authority['start_epoch'] == 1792586321 and authority['cutoff_epoch'] == 1792672721 and
         authority['phase_seconds'] == 3600 and authority['cleanup_seconds'] == 180,
         'unaltered original authority, phase and cleanup')
    checked(authority['user_authorization_ref'])
    names = set(old['files'])
    ROOT.mkdir(mode=0o700)
    for name in sorted(names):
        target = ROOT / name
        need(ROOT in target.parents, 'confined copied source')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(checked(old['files'][name]), target)
    for name in HELPERS:
        shutil.copyfile(checked(review['helpers'][name]), ROOT / name)
        names.add(name)
    (ROOT / 'short_binding_delta.py').write_text(BI.render_short_delta(
        checked(old['files']['short_binding_delta.py']).read_text()))
    (ROOT / 'performance_validate.py').write_text(BI.render_validator(
        checked(old['files']['performance_validate.py']).read_text(), pins))
    D = module('_boundary_assembled_short_delta', ROOT / 'short_binding_delta.py')
    originals = {name: checked(parent['files'][name]).read_text() for name in D.RUNTIME}
    changed = D.runtime(originals)
    need(set(changed) == set(D.RUNTIME), 'complete exact expanded runtime delta')
    changed['contract090.py'] = B.bind_outputs(
        checked(parent['files']['contract090.py']).read_text(), str(OUT))
    for name in CLOCK_FILES:
        changed[name] = clock(changed.get(name,
            checked(parent['files'][name]).read_text()), authority)
    for name, text in changed.items():
        (ROOT / name).write_text(text)
    # This coordinator is copied from the already-current ON source, retaining
    # all twenty current controls, the original finite Budget and metadata gate.
    for path in ROOT.rglob('*.py'):
        compile(path.read_bytes(), str(path), 'exec')
    # These files are new unfrozen copies, not writes to the retained parent.
    (ROOT / 'SHORT_AUTHORITY.json').write_text(json.dumps(authority, sort_keys=True) + '\n')
    authority_ref = ref(ROOT / 'SHORT_AUTHORITY.json')
    m = copy.deepcopy(old)
    m.pop('prepared_template', None)
    m.update(root=str(ROOT), output_root=str(OUT),
        model_receipt_root=str(OUT / 'dense/receipts'),
        stream_channel_root=str(OUT / 'dense/receipts/STREAM'),
        stream_channel_contract_path=str(OUT / 'dense/receipts/STREAM/CHANNEL.json'),
        authority_ref=authority_ref, prepared_only=True,
        boundary_parent_source=PARENT,
        boundary_probe_profile=copy.deepcopy(BP.DECLARATION),
        projection_probe_profile=copy.deepcopy(PP.DECLARATION),
        boundary_reviewed_helpers=pins,
        boundary_control_refs=copy.deepcopy(review['control_refs']))
    m['files'] = {name: ref(ROOT / name) for name in sorted(names)}
    m['performance_parent_preparation'] = m['files']['PARENT381_PREPARATION.json']
    m['performance_timing_donor'] = m['files']['benchmark_shared_prefix.py']
    m['performance_streaming_client'] = m['files']['performance_service_client.py']
    m['service_runtime_source_snapshots'] = B.rebind_snapshots(old, m['files'])
    different = {name for name in parent['files'] if name != 'PERFORMANCE_WHOLE_DELTA.json'
                 and checked(parent['files'][name]).read_bytes() != (ROOT / name).read_bytes()}
    ledger = dict(schema='bole.short-state-exact-delta/v1', parent=P.PIN,
        files={name: dict(before=parent['files'][name], after=m['files'][name])
               for name in sorted(different)})
    (ROOT / 'SHORT_DELTA.json').write_text(json.dumps(ledger, sort_keys=True) + '\n')
    m['short_delta_ref'] = ref(ROOT / 'SHORT_DELTA.json')
    m['files']['SHORT_DELTA.json'] = m['short_delta_ref']
    dependencies = dict(readset)
    for reference in [m['performance_streaming_client'], m['performance_timing_donor']]:
        checked(reference)
        need(reference['path'] not in dependencies or dependencies[reference['path']] == reference,
             'same complete actual runtime dependency')
        dependencies[reference['path']] = reference
    m['dependencies'] = list(dependencies.values())
    template = exclusive(ROOT / 'SOURCE_TEMPLATE.json', m)
    m.update(prepared_only=False, prepared_template=template)
    source = exclusive(ROOT / 'SOURCE_BOUND.json', m)
    command_module = module('_boundary_commands', ROOT / 'command_contract.py')
    commands = dict(schema='bole.performance-actual-bound-commands/v1', source=template,
        bound_source=source, required_sameimage_software_cases=20,
        historical_required_sameimage_software_cases=154, G3_stream_protocol=False,
        actual_G3_execution_claimed=False, actual_G1_execution_claimed=False,
        legacy_entrypoints_retained_for_inverse_tests_only=True,
        short_state_gate=True, boundary_diagnostic_only=True,
        NPU_executed=False, formal_performance=False,
        **command_module.expected(ROOT, str(OUT), source, template, m['component_refs']))
    command_ref = exclusive(ROOT / 'COMMANDS.json', commands)
    exclusive(ROOT / m['command_scope']['compatibility_file'], dict(
        source=source, template=template, commands=command_ref,
        model=commands['model'], CPU=commands['CPU'], required_sameimage_software_cases=20))
    for reference in readset.values():
        checked(reference)
    result = dict(schema='bole.boundary-probe-source-freeze/v1', source=source,
        commands=command_ref, source_only=True, owner_created=False, NPU=False,
        paired_gate_pass=False, performance_admitted=False, formal_performance=False,
        parent=PARENT, review=review_ref, original_inputs_unchanged=True,
        original_readset=list(readset.values()), fixed_cutoff=1792672721,
        phase_seconds=3600, cleanup_seconds=180)
    receipt = exclusive(HERE / 'BUILD_RECORD.json', result)
    print(json.dumps(dict(receipt=receipt, source=source, commands=command_ref,
                         source_only=True, NPU=False, performance_admitted=False), sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--review-ref', required=True, type=json.loads)
    freeze(parser.parse_args().review_ref)
