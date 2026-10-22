"""Exact additional source gate for one bounded ON boundary-observer child.

This runs before the unchanged short validator's D.runtime comparisons and all
its numerical, clock, dependency, software and original-command gates. It does
not execute controls, launch a service, or grant numerical/performance admission.
"""
import importlib
import sys
from pathlib import Path
import boundary_integration as I


def ref_identity(reference):
    return reference['bytes'], reference['sha256']


def validate(C, source_ref, manifest, *, reviewed):
    m = manifest
    pins = I.normalize_reviewed_helpers(reviewed)
    C.need(I.canonical(m.get('boundary_reviewed_helpers')) == I.canonical(pins),
           'manifest and actual validator carry identical MAIN-reviewed helper pins')
    C.need(m.get('boundary_parent_source') == I.PARENT_REF,
           'one exact completed old ON short parent; no alternate lineage')
    parent = C.obj(I.PARENT_REF)
    C.need(parent['files']['short_binding_delta.py'] == I.OLD_SHORT_DELTA_REF
           and parent['files']['performance_validate.py'] == I.OLD_VALIDATOR_REF,
           'fixed old ON source owns the exact original delta and validator')
    old_delta = C.checked(I.OLD_SHORT_DELTA_REF).read_text()
    old_validator = C.checked(I.OLD_VALIDATOR_REF).read_text()
    root = Path(m['root'])
    C.need(str(root) == I.CHILD_ROOT and m['output_root'] == I.CHILD_OUTPUT
           and root == Path(source_ref['path']).parent and root != Path(parent['root'])
           and m['output_root'] != parent['output_root'],
           'fresh exact child source and output identities')
    C.need(set(m['files']) == set(parent['files']) | set(I.REVIEWED_HELPERS),
           'only four explicitly reviewed modules added to copied ON source closure')
    for name in I.REVIEWED_HELPERS:
        reference = m['files'][name]
        C.need(reference == dict(path=str(root/name), **pins[name]),
               'exact source-owned MAIN-reviewed helper: ' + name)
        C.checked(reference)
    C.need(C.ref(__file__) == m['files']['boundary_validation.py']
           and C.ref(I.__file__) == m['files']['boundary_integration.py'],
           'actual child validator and renderer loaded from this source')
    C.need(C.checked(m['files']['short_binding_delta.py']).read_text() == I.render_short_delta(old_delta),
           'child D is exactly the original short runtime plus the declared boundary composition')
    C.need(C.checked(m['files']['performance_validate.py']).read_text() == I.render_validator(old_validator, pins),
           'child V retains the entire original validator body plus this one lineage hook')
    D = sys.modules.get('short_binding_delta')
    C.need(D is not None and C.ref(D.__file__) == m['files']['short_binding_delta.py']
           and tuple(D.RUNTIME) == I.RUNTIME,
           'actual exact child D and full expanded runtime declaration')
    delta = importlib.import_module('boundary_delta')
    probe = importlib.import_module('boundary_probe_v1')
    C.need(C.ref(delta.__file__) == m['files']['boundary_delta.py']
           and C.ref(probe.__file__) == m['files']['boundary_probe_v1.py']
           and tuple(delta.EXTRA_RUNTIME) == I.EXTRA_RUNTIME,
           'actual reviewed observer/delta and exact three added runtime operands')
    C.need(probe.FLAG == I.FLAG and probe.select({}, None) is None
           and probe.select({I.FLAG: '0'}, None) is None
           and probe.create(None, None, None, {}, {}, None, None, None) is None,
           'stateless explicit default-OFF selection/factory does no source or tensor work')
    C.need(I.canonical(m.get('boundary_probe_profile')) == I.canonical(probe.DECLARATION)
           and probe.select({I.FLAG: '1'}, m['boundary_probe_profile']) == m['boundary_probe_profile'],
           'exact reviewed ON diagnostic declaration and its explicit opt-in')
    C.need(m['short_state_digest_profile'] == parent['short_state_digest_profile']
           and m['short_state_digest_profile']['observation'] == 'ON'
           and 'observation_only_profile' not in m
           and m['default_enabled'] is False and m['prepared_only'] is False,
           'original bounded ON short profile and default-disabled model entry')

    # Root/alias/source bindings may move; all other old manifest semantics stay exact.
    mutable = {'root', 'output_root', 'model_receipt_root', 'stream_channel_root',
               'stream_channel_contract_path', 'authority_ref', 'prepared_template', 'files',
               'performance_parent_preparation', 'performance_timing_donor',
               'performance_streaming_client', 'service_runtime_source_snapshots',
               'dependencies', 'short_delta_ref'}
    C.need(set(m) == set(parent) | set(I.MANIFEST_FIELDS),
           'closed child manifest delta; no undeclared configuration fields')
    for field in set(parent) - mutable:
        C.need(I.canonical(m[field]) == I.canonical(parent[field]),
               'unchanged original ON semantic manifest field: ' + field)
    C.need(m['model_receipt_root'] == str(Path(I.CHILD_OUTPUT)/'dense/receipts')
           and m['stream_channel_root'] == str(Path(I.CHILD_OUTPUT)/'dense/receipts/STREAM')
           and m['stream_channel_contract_path'] == str(Path(I.CHILD_OUTPUT)/'dense/receipts/STREAM/CHANNEL.json')
           and Path(m['prepared_template']['path']) == root/'SOURCE_TEMPLATE.json',
           'exact derived child receipt/stream/template aliases')

    def rebound(reference):
        name = str(Path(reference['path']).relative_to(Path(parent['root'])))
        C.need(parent['files'].get(name) == reference and name in m['files'],
               'original alias was a source-owned parent file')
        return m['files'][name]

    for field in ('performance_parent_preparation', 'performance_timing_donor', 'performance_streaming_client'):
        C.need(m[field] == rebound(parent[field]), 'exact copied child operand alias: ' + field)
    C.need(m['service_runtime_source_snapshots'] ==
           {key: rebound(reference) for key, reference in parent['service_runtime_source_snapshots'].items()},
           'only copied snapshot identities rebound; installed runtime paths stay fixed')

    authority = C.obj(m['authority_ref'])
    old_authority = C.obj(parent['authority_ref'])
    expected_authority = dict(old_authority, batch_id=I.CHILD_BATCH, scope=I.CHILD_AUTHORITY_SCOPE)
    C.need(I.canonical(authority) == I.canonical(expected_authority),
           'authority changes only exact child batch and narrower diagnostic scope')
    C.need(Path(m['authority_ref']['path']) == root/'SHORT_AUTHORITY.json'
           and authority['schema'] == old_authority['schema'] == 'bole.short-state-authority/v1'
           and authority['user_authorization_ref'] == old_authority['user_authorization_ref']
           and authority['start_epoch'] == old_authority['start_epoch'] == 1792586321
           and authority['cutoff_epoch'] == old_authority['cutoff_epoch'] == 1792672721
           and authority['cutoff_iso'] == old_authority['cutoff_iso'] == '2026-10-22T12:38:41+00:00'
           and authority['phase_seconds'] == old_authority['phase_seconds'] == 3600
           and authority['cleanup_seconds'] == old_authority['cleanup_seconds'] == 180
           and authority['batch_id'] == I.CHILD_BATCH,
           'same actual user window/phase/cleanup; one new source identity, no renewed authority')
    C.checked(authority['user_authorization_ref'])

    # The unchanged V checks all transformed runtime text against D.runtime and
    # all original clock/text deltas. This additionally closes every other parent
    # file against any new change, including mathematical/component/cleanup code.
    permitted_existing_changes = set(I.RUNTIME) | {
        'bind_model.py', 'contract090.py', 'g2_cold_clock.py', 'g2_software_stages.py',
        'owned_substrate.py', 'worker_bootstrap.py',
        'short_binding_delta.py', 'performance_validate.py', 'SHORT_AUTHORITY.json', 'SHORT_DELTA.json'}
    for name, reference in parent['files'].items():
        C.checked(reference)
        if name not in permitted_existing_changes:
            C.need(ref_identity(m['files'][name]) == ref_identity(reference),
                   'all other original ON whole-file bytes unchanged: ' + name)

    dependencies = {}
    for reference in m['dependencies']:
        C.need(reference['path'] not in dependencies or dependencies[reference['path']] == reference,
               'unique child dependency Ref')
        dependencies[reference['path']] = reference
    required_parent_refs = [I.PARENT_REF, parent['prepared_template'], parent['authority_ref'],
                            *parent['files'].values(), *parent['dependencies']]
    for reference in required_parent_refs:
        C.need(dependencies.get(reference['path']) == reference,
               'complete original ON lineage retained in host before/after readset')
        C.checked(reference)
    controls = m['boundary_control_refs']
    C.need(type(controls) is list and 0 < len(controls) <= 16
           and len({reference['path'] for reference in controls}) == len(controls),
           'explicit separately reviewed boundary control source/evidence refs')
    for reference in controls:
        C.need(dependencies.get(reference['path']) == reference,
               'separate boundary control remains a pinned dependency, not a replacement for original20')
        C.checked(reference)
    C.need(m['service_required_sameimage_software_cases'] == parent['service_required_sameimage_software_cases'] == 20
           and m['performance_software_scope'] == parent['performance_software_scope']
           and m['service_software_scope'] == parent['service_software_scope'],
           'original exact20 and original300-second aggregate software budget unchanged')
    return dict(schema='bole.boundary-child-source-lineage/v1', source=source_ref,
        parent=I.PARENT_REF, source_validated=True, original_short_runtime_comparison_bypassed=False,
        controls_executed=False, original_twenty_controls_changed=False,
        numerical_qualified=False, model_ready=False, formal_performance=False, NPU=False)
