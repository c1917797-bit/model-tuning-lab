"""Explicit read-only final host snapshot; stdout only, no resource admission.

Loads one exact previously reviewed helper. No model imports, NPU requests,
new owners, container mutation, stop/delete, bind/listen or filesystem writes.
Only newly spawned read-only CLI children can be stopped by that frozen helper
if their own inspection deadline expires. Arbitrary container env is not emitted.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import signal
import sys
import time

sys.dont_write_bytecode = True
REVIEWED_FROZEN = True
WS = Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
HELPER = dict(path=str(WS/'boundary_admission_v4_20261022/fresh_snapshot_v4.py'),
    bytes=19376, sha256='8c0b3105354708f3942f798d67a057ef16e11c5b10b538106166dafce61c1968')
CONFIG = WS/'boundary_admission_v4_20261022/CONFIG.json'
DIAGNOSTIC = dict(path='/opt/host/vnf/austinov/run-bole-boundary-reader-v2-20261022T080000Z/BOUNDARY_DIAGNOSTIC.json',
    bytes=5011374, sha256='c2260812c8bda323b4b0b363f770c6becb9a613ee1e1c850b456f6a9a852d9f2')
OLD_OUTPUT = Path('/opt/host/vnf/austinov/run-bole-boundary-ON-v1-20261022T080000Z')
NEW_OUTPUT = Path("/opt/host/vnf/austinov/run-bole-reduction-ON-v5_20261022T200000Z")
NEW_SOURCE = Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v5_20261022T200000Z")
CONTINUATION_OUTPUT = Path('/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z')
CONTINUATION_SOURCE = {'bytes': 1638841, 'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-boundary-ON-v3-continuation_20261022T120055Z/SOURCE_BOUND.json', 'sha256': 'd28e57b46ae913182ff8ebc0f35a1c631f12fce647376af495a4b59c4d8e10df'}
CONTINUATION_CIDS = {'cpu-preflight': '0a5ed053d4d08915b8748e0f6facbc6f3fad820ff1f46d1eefe0f4bc6626d955', 'dense': 'eb21e660585ed4e758476504bc0b409a02b777d875516e2925f00a9e8efaa8cf'}
CONTINUATION_OWNED_REFS = {'cpu-preflight': {'bytes': 1414912,
                   'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/cpu-preflight/OWNED.json',
                   'sha256': 'bd5297f2d8e8bfcea5d02b1fdb4612faf453db55bfdf3c5a1a4c87b7f4008316'},
 'dense': {'bytes': 1414866,
           'path': '/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z/dense/OWNED.json',
           'sha256': '45859b745214ec0f19d728d018d438a02dcff61104084726446baedf29e74ba8'}}

TEXTONLY_SOURCE = {"bytes": 1644617, "path": "/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-boundary-ON-v4-textonly_20261022T171000Z/SOURCE_BOUND.json", "sha256": "d25264b5eda1d2a45fb3bab7ce1ca331296a9640a2e42112f802d4db69a7f127"}
TEXTONLY_OUTPUT = Path('/opt/host/vnf/austinov/run-bole-boundary-ON-v4-textonly_20261022T171000Z')
TEXTONLY_CIDS = {"dense": "79c06ff95a70e957a5afd7e7ac1dc46932e7b45e4afde72fd56d0d4f996eab7c", "cpu-preflight": "4e17856a927a9bbccce9d145db5151c1c14e1688357124f9773fd878ac6003ec"}
TEXTONLY_OWNED_REFS = {"dense": {"path": "/opt/host/vnf/austinov/run-bole-boundary-ON-v4-textonly_20261022T171000Z/dense/OWNED.json", "bytes": 1418084, "sha256": "465163d220fa4122b17737d4f7aaa93fdcf192e6e3e5e286ddac6eaa90ebb206"}, "cpu-preflight": {"path": "/opt/host/vnf/austinov/run-bole-boundary-ON-v4-textonly_20261022T171000Z/cpu-preflight/OWNED.json", "bytes": 1418130, "sha256": "1b7f8ce52a4695c3da52ba5ca239983bea2e3c779d63213f90fef336ae2ea149"}}

OWNER = 'bole-root-r6-20261017-001'
HOST_SHA = '20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30'
IMAGE = 'sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
BOUNDARY_SOURCE_SHA = '702e3feba7de9e4365b472189c9bf0662fdc35f1e08e0e535c863b62e132dbdc'
FIRST_FOUR = {
    '40c6b48039182b29b47a4a4283ba17f414570f5a5465d6c2865a0b595866b45a',
    '54246001fc180995c8e021a27f8f5b14f237fe6e92dd62dcb4acadc3dfae0411',
    'c4a669cc4b20e5f013e92ce22ac89f6eccf7236286464bd2f7b7b8ac9bf3bdc9',
    '961b3501d0b739216264e2027115a3245d0e391709a408ed9ac2943bcd1f083d'}
LATEST = {
    'cpu-preflight': '6433f9740a1acc4be305d35456436dbccdaf0a91d6884e283259ea22dec99ef5',
    'dense': 'a25d55a819562ffbf2135ba1017bb52ae2e3ca9c3ee2998486540bbbaebd4cf0'}
UNITS = ('bole-short-on-v2-model-20261021t123841z.service',
         'bole-short-off-v2-model-20261021t123841z.service',
         'bole-boundary-on-v1-model-20261022t080000z.service',
         'bole-boundary-on-v3-continuation-20261022t120055z-u3.service',
         'bole-boundary-on-v4-textonly-20261022t171000z-u1.service')
START, CUTOFF, OLD_REPORT_CUTOFF = 1792689000, 1792710600, 1792672721
CAP = 16 * 2**20


def need(value, why):
    if not value:
        raise ValueError(why)


def read_ref(path, cap=8 * 2**20, expected=None):
    path = Path(path)
    need(path.is_absolute() and path.is_file() and
         not any(p.is_symlink() for p in (path, *path.parents)),
         'ordinary absolute read-only input')
    before = path.stat()
    need(0 <= before.st_size <= cap, 'whole input read cap')
    with path.open('rb') as stream:
        body = stream.read(cap + 1)
    identity = lambda value: (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
        value.st_uid, value.st_gid, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    need(len(body) <= cap and identity(path.stat()) == identity(before),
         'whole input identity unchanged during read; access-time changes excluded')
    actual = dict(path=str(path), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    need(expected is None or actual == expected, 'exact whole expected input Ref3')
    return actual, body


def latest_identities(H, manifest):
    """Use only saved inspect Ref3s inside the independently pinned readset.

    Missing historical join stays explicit. Current Docker inspect cannot be
    used to fabricate a historical name/label expectation.
    """
    references = manifest['inputs_before']
    need(type(references) is list and len(references) <= 16384,
         'bounded original independent input set')
    pins = {}
    for ref in references:
        need(type(ref) is dict and set(ref) == {'path', 'bytes', 'sha256'} and
             type(ref['path']) is str and type(ref['bytes']) is int and
             type(ref['sha256']) is str and re.fullmatch('[0-9a-f]{64}', ref['sha256']),
             'typed original input Ref3')
        need(ref['path'] not in pins or pins[ref['path']] == ref, 'unique original input identity')
        pins[ref['path']] = ref
    expected, evidence = [], []
    for arm, cid in LATEST.items():
        baseline = dict(id=cid, image=IMAGE)
        candidates = sorted((ref for ref in pins.values()
            if Path(ref['path']).parent == OLD_OUTPUT/arm and
            re.fullmatch('inspect-[0-9]+\\.json', Path(ref['path']).name)),
            key=lambda ref: ref['path'], reverse=True)
        row = dict(arm=arm, id=cid, historical_join_proven=False,
            candidate_count=len(candidates), inspected_refs=[],
            reason='no matching saved inspect in independently pinned readset')
        need(len(candidates) <= 32, 'bounded saved-inspect candidate closure')
        for candidate in candidates:
            H.bounded()
            try:
                pin, body = read_ref(candidate['path'], expected=candidate)
                envelope = json.loads(body)
                need(type(envelope) is dict and type(envelope.get('stdout')) is str,
                     'saved inspect command envelope with literal stdout')
                values = json.loads(envelope['stdout'])
                need(type(values) is list and len(values) == 1 and type(values[0]) is dict,
                     'one complete saved Docker inspect object')
                actual = values[0]
                row['inspected_refs'].append(pin)
                if actual.get('Id') != cid:
                    continue
                labels = {k:v for k,v in (actual['Config'].get('Labels') or {}).items()
                          if k.startswith('model-tuning-lab.')}
                need(actual['Image'] == IMAGE and type(actual['Name']) is str and
                     actual['Name'].startswith('/') and
                     labels.get('model-tuning-lab.source-manifest-sha256') == BOUNDARY_SOURCE_SHA and
                     labels.get('model-tuning-lab.arm') == arm and
                     labels.get('model-tuning-lab.run') == actual['Name'][1:],
                     'saved exact historical CID/image/source/name/arm join')
                baseline.update(name=actual['Name'], labels=labels)
                row.update(historical_join_proven=True, reason=None, saved_inspect=pin)
                break
            except Exception as exc:
                row['reason'] = type(exc).__name__ + ': ' + str(exc)
                H.fail('historical saved inspect read/join failed for exact arm ' + arm)
                break
        expected.append(baseline)
        evidence.append(row)
    return expected, evidence


def continuation_identities(H):
    """Add two independently pinned OWNED identities from the failed v3 run.

    Reading identities here grants no lifecycle/model qualification. MAIN still
    rereads create, complete inspect, stop/release and original failed RESULT.
    """
    need(type(CONTINUATION_OWNED_REFS) is dict and
         set(CONTINUATION_OWNED_REFS) == set(CONTINUATION_CIDS),
         'actual complete two-owner OWNED pins must be bound before observation')
    source_ref, source_raw = read_ref(CONTINUATION_SOURCE['path'], expected=CONTINUATION_SOURCE)
    source = json.loads(source_raw)
    need(source['root'] == str(Path(CONTINUATION_SOURCE['path']).parent) and
         source['output_root'] == str(CONTINUATION_OUTPUT),
         'exact immutable failed continuation source/output identity')
    identities, joins, refs = [], [], [source_ref]
    for arm, cid in CONTINUATION_CIDS.items():
        H.bounded()
        expected = CONTINUATION_OWNED_REFS[arm]
        need(type(expected) is dict and set(expected) == {'path', 'bytes', 'sha256'} and
             Path(expected['path']) == CONTINUATION_OUTPUT/arm/'OWNED.json',
             'complete original per-arm OWNED Ref3 at the exact historical output')
        ref, raw = read_ref(expected['path'], expected=expected)
        owned = json.loads(raw)
        need(owned['cid'] == cid and owned['arm'] == arm and owned['image'] == IMAGE and
             owned['source'] == CONTINUATION_SOURCE and owned['host_sha256'] == HOST_SHA and
             owned['sources']['safety_host.py'] == HOST_SHA and
             type(owned['name']) is str and owned['name'] and
             Path(owned['mounts']['/adakv-results'][0]) == CONTINUATION_OUTPUT/arm,
             'exact original CID/arm/image/source/controller/name/output join')
        labels = {'model-tuning-lab.arm': arm,
            'model-tuning-lab.controller-sha256': HOST_SHA,
            'model-tuning-lab.owner': OWNER, 'model-tuning-lab.run': owned['name'],
            'model-tuning-lab.source-manifest-sha256': CONTINUATION_SOURCE['sha256']}
        identities.append(dict(id=cid, image=IMAGE, name='/' + owned['name'], labels=labels))
        joins.append(dict(arm=arm, id=cid, source=source_ref, owned=ref,
            identity_from_original_OWNED=True, lifecycle_qualified=False, numerical_qualified=False))
        refs.append(ref)
    return identities, joins, refs


def textonly_identities(H):
    """Add two independently pinned OWNED identities from the completed V4 run.

    Reading identities here grants no lifecycle/model qualification. MAIN still
    rereads create, complete inspect, stop/release and original failed RESULT.
    """
    need(type(TEXTONLY_OWNED_REFS) is dict and
         set(TEXTONLY_OWNED_REFS) == set(TEXTONLY_CIDS),
         'actual complete two-owner OWNED pins must be bound before observation')
    source_ref, source_raw = read_ref(TEXTONLY_SOURCE['path'], expected=TEXTONLY_SOURCE)
    source = json.loads(source_raw)
    need(source['root'] == str(Path(TEXTONLY_SOURCE['path']).parent) and
         source['output_root'] == str(TEXTONLY_OUTPUT),
         'exact immutable completed text-only source/output identity')
    identities, joins, refs = [], [], [source_ref]
    for arm, cid in TEXTONLY_CIDS.items():
        H.bounded()
        expected = TEXTONLY_OWNED_REFS[arm]
        need(type(expected) is dict and set(expected) == {'path', 'bytes', 'sha256'} and
             Path(expected['path']) == TEXTONLY_OUTPUT/arm/'OWNED.json',
             'complete original per-arm OWNED Ref3 at the exact historical output')
        ref, raw = read_ref(expected['path'], expected=expected)
        owned = json.loads(raw)
        need(owned['cid'] == cid and owned['arm'] == arm and owned['image'] == IMAGE and
             owned['source'] == TEXTONLY_SOURCE and owned['host_sha256'] == HOST_SHA and
             owned['sources']['safety_host.py'] == HOST_SHA and
             type(owned['name']) is str and owned['name'] and
             Path(owned['mounts']['/adakv-results'][0]) == TEXTONLY_OUTPUT/arm,
             'exact original CID/arm/image/source/controller/name/output join')
        labels = {'model-tuning-lab.arm': arm,
            'model-tuning-lab.controller-sha256': HOST_SHA,
            'model-tuning-lab.owner': OWNER, 'model-tuning-lab.run': owned['name'],
            'model-tuning-lab.source-manifest-sha256': TEXTONLY_SOURCE['sha256']}
        identities.append(dict(id=cid, image=IMAGE, name='/' + owned['name'], labels=labels))
        joins.append(dict(arm=arm, id=cid, source=source_ref, owned=ref,
            identity_from_original_OWNED=True, lifecycle_qualified=False, numerical_qualified=False))
        refs.append(ref)
    return identities, joins, refs



def ids_from_inventory(H, result):
    need(result['exit_code'] == 0 and result['error'] is None, 'complete running container inventory')
    ids = result['stdout'].split()
    need(len(ids) <= 4096 and len(set(ids)) == len(ids) and
         all(re.fullmatch('[0-9a-f]{64}', cid) for cid in ids),
         'bounded exact running Docker CIDs')
    return ids


def share_complete_mount_members(H, result):
    """Lossless member interning; every original array keeps its exact order.

    Actual v3 was still oversized: the whole arrays did not share identical
    order/value content. No cause beyond unequal arrays is inferred. Store
    complete unique member values once plus every list's full integer index
    sequence, preserving repeats/order. Hash hits require full member equality;
    complete array value, bytes and SHA are rechecked before publishing refs.
    """
    members, arrays, bindings, pending = [], [], [], []
    member_index = {}
    original_bytes = 0
    unique_member_bytes = 0
    def canonical(value):
        return json.dumps(value, sort_keys=True, separators=(',', ':'),
                          allow_nan=False).encode()
    for section in ('inspect_before', 'inspect_old_after', 'newly_running_inspect'):
        if section not in result:
            continue
        rows = result[section]['containers']
        need(type(rows) is list, 'complete inspected container sequence')
        for ordinal, row in enumerate(rows):
            H.bounded()
            original = row['mounts']
            need(type(original) is list, 'original complete projected mount sequence')
            raw = canonical(original)
            array_digest = hashlib.sha256(raw).hexdigest()
            array_bytes = len(raw)
            original_bytes += array_bytes
            indices = []
            for offset, member in enumerate(original):
                if offset % 1024 == 0:
                    H.bounded()
                encoded_member = canonical(member)
                digest = hashlib.sha256(encoded_member).hexdigest()
                if digest in member_index:
                    index = member_index[digest]
                    need(members[index] == member and canonical(members[index]) == encoded_member,
                         'member digest reuse requires complete exact typed member/value equality')
                else:
                    index = len(members)
                    member_index[digest] = index
                    members.append(member)
                    unique_member_bytes += len(encoded_member)
                indices.append(index)
            array_index = len(arrays)
            arrays.append(dict(member_count=len(original),
                json_utf8_bytes=array_bytes, canonical_json_sha256=array_digest,
                ordered_member_indices=indices))
            bindings.append(dict(section=section, ordinal=ordinal,
                                 container_id=row['Id'], array_index=array_index))
            reference = dict(representation='complete_indexed_mount_members/v2',
                array_index=array_index, canonical_json_sha256=array_digest,
                json_utf8_bytes=array_bytes, member_count=len(original),
                full_order_and_duplicates_preserved=True)
            pending.append((row, reference, original))
    for row, reference, original in pending:
        H.bounded()
        array = arrays[reference['array_index']]
        restored = [members[index] for index in array['ordered_member_indices']]
        need(restored == original and len(restored) == array['member_count'],
             'complete original ordered mount array and duplicate multiplicity restored')
        encoded = canonical(restored)
        need(len(encoded) == array['json_utf8_bytes'] and
             hashlib.sha256(encoded).hexdigest() == array['canonical_json_sha256'],
             'restored whole mount array exact UTF8 bytes and SHA')
    member_raw = canonical(members)
    need(len(member_raw) == 2 + max(0, len(members)-1) + unique_member_bytes,
         'complete member table byte accounting')
    table = dict(schema='bole.complete-shared-projected-mount-members/v2',
        canonical_encoding='json.dumps(sort_keys=True,separators=(comma,colon),ensure_ascii=True,allow_nan=False).encode(utf8)',
        original_projected_member_fields=['Type','Source','Destination','RW'],
        raw_Docker_inspect_bytes_and_SHA_receipts_retained=True,
        all_projected_members_values_order_and_duplicates_preserved=True,
        full_member_equality_required_for_hash_reuse=True,
        every_original_array_fully_reconstructed_before_publication=True,
        reference_count=len(bindings), array_count=len(arrays),
        unique_member_count=len(members),
        original_repeated_list_json_utf8_bytes=original_bytes,
        unique_member_value_json_utf8_bytes=unique_member_bytes,
        complete_member_table_json_utf8_bytes=len(member_raw),
        complete_member_table_sha256=hashlib.sha256(member_raw).hexdigest(),
        bindings=bindings, arrays=arrays, members=members)
    # Publish only after every whole-array reconstruction succeeds. Failed
    # interning/collision cannot leave a partially replaced input snapshot.
    for row, reference, original in pending:
        row['mounts'] = reference
    return table


def oversize_diagnostic(result, encoded):
    """Bounded structural evidence only; never include observed string values.

    This is a failed observation, not a usable host/resource snapshot. Field
    sizes refer to this attempt's otherwise omitted complete compact JSON.
    """
    def bytecount(value):
        return len(json.dumps(value, sort_keys=True, separators=(',', ':'),
                              allow_nan=False).encode())

    def descriptor(value):
        row = dict(type=type(value).__name__, json_bytes=bytecount(value))
        if type(value) in (dict, list, str):
            row['items_or_characters'] = len(value)
        if type(value) is str:
            row['utf8_bytes'] = len(value.encode())
        return row

    def fields(value, allowed):
        return {name: descriptor(value[name]) for name in allowed if name in value}

    command_fields = ('argv', 'requested_argv', 'actual_argv', 'rss', 'observed_utc',
                      'exit_code', 'error', 'stdout', 'stderr', 'stdout_bytes', 'stdout_sha256')
    container_fields = ('Id', 'Name', 'Image', 'State', 'ExecIDs', 'labels',
                        'resources', 'mounts', 'visible_devices')
    holder_fields = ('pid', 'start_ticks', 'state', 'executable', 'cgroup', 'status',
                     'cpu_affinity', 'cmdline_sha256', 'cmdline_bytes',
                     'device_fds', 'lock_fds')

    def largest_rows(values, allowed):
        need(type(values) is list, 'structural list measurement')
        sizes = [(bytecount(value), index) for index, value in enumerate(values)]
        chosen = sorted(sizes, reverse=True)[:64]
        return dict(total_rows=len(values), detailed_rows=len(chosen),
            detailed_limit=64, detail_selection='largest_JSONbytes_then_ordinal',
            rows=[dict(ordinal=index, json_bytes=size,
                       fields=fields(values[index], allowed) if type(values[index]) is dict else {})
                  for size, index in chosen])

    top = {name: descriptor(value) for name, value in result.items()}
    measured = 2 + max(0, len(top)-1) + sum(
        bytecount(name) + 1 + row['json_bytes'] for name, row in top.items())
    need(measured == len(encoded.encode()), 'structural bytes reconstruct exact original JSON length')
    details = {}
    for name in ('inspect_before', 'inspect_old_after', 'newly_running_inspect'):
        value = result.get(name)
        if type(value) is dict:
            row = fields(value, ('commands', 'containers'))
            for child, allowed in (('commands', command_fields), ('containers', container_fields)):
                if type(value.get(child)) is list:
                    row[child + '_largest_rows'] = largest_rows(value[child], allowed)
            details[name] = row
    for name in ('docker_top_before', 'newly_running_top', 'old_units'):
        if type(result.get(name)) is list:
            details[name] = largest_rows(result[name], command_fields)
    for name in ('smi_before', 'smi_after', 'docker_unit', 'host_listeners_8230',
                 'running_inventory_before', 'running_inventory_after', 'engine_command'):
        if type(result.get(name)) is dict:
            details[name] = fields(result[name], command_fields)
    value = result.get('devices_and_actual_holders')
    if type(value) is dict:
        details['devices_and_actual_holders'] = fields(value, ('nodes', 'actual_holders',
            'actual_lock_fd_holders', 'disappeared_processes', 'process_count'))
        for name in ('actual_holders', 'actual_lock_fd_holders'):
            if type(value.get(name)) is list:
                details['devices_and_actual_holders'][name + '_largest_rows'] = largest_rows(value[name], holder_fields)
    diagnostic = dict(schema='bole.final-readonly-host-snapshot-oversize-diagnostic/v4',
        complete=False, observation_available=False, readonly=True,
        error='complete observation exceeds unchanged16MiB cap; only exact structural size counters retained',
        NPU=False, owner_created=False, container_started=False, container_modified=False,
        existing_process_signalled=False, resources_admitted=False, candidate_qualification=False,
        numerical_qualified=False, paired_gate_pass=False, performance_admitted=False,
        formal_performance=False, max_final_bytes=CAP,
        original_encoded_bytes=len(encoded.encode()),
        original_encoded_sha256=hashlib.sha256(encoded.encode()).hexdigest(),
        reconstructed_encoded_bytes=measured, field_measurements=top,
        limited_nonsecret_structure=details,
        raw_field_values_included=False,
        remaining_required='Size diagnosis only; no current resource or model conclusion is supported.')
    output = json.dumps(diagnostic, sort_keys=True, separators=(',', ':'), allow_nan=False)
    need(len(output.encode()) <= CAP, 'diagnostic remains under unchanged final16MiB cap')
    return output


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--execute-readonly', action='store_true')
    args = parser.parse_args()
    if not args.execute_readonly:
        print(json.dumps(dict(enabled=False, NPU=False, resources_admitted=False)))
        return 0
    started = time.monotonic()
    result = dict(schema='bole.final-readonly-host-snapshot/v4', readonly=True,
        NPU=False, owner_created=False, container_started=False, container_modified=False,
        existing_process_signalled=False, resources_admitted=False,
        candidate_qualification=False, numerical_qualified=False,
        paired_gate_pass=False, performance_admitted=False, formal_performance=False)
    H = None
    errors = []
    rereads = []
    def alarm(signum, frame):
        raise TimeoutError('final read-only snapshot whole180-second guard')
    signal.signal(signal.SIGALRM, alarm)
    signal.alarm(180)
    try:
        need(REVIEWED_FROZEN is True and CONTINUATION_OWNED_REFS is not None,
             'draft is not frozen/reviewed; no active observation permitted')
        os.sched_setaffinity(0, {166})
        need(os.sched_getaffinity(0) == {166}, 'host CPU166 inspection affinity')
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        need(hard == resource.RLIM_INFINITY, 'infinite hard AS required for frozen Go CLI wrapper')
        resource.setrlimit(resource.RLIMIT_AS, (512 * 2**20, hard))
        helper_ref, helper_body = read_ref(HELPER['path'], cap=2**20, expected=HELPER)
        spec = importlib.util.spec_from_file_location('_bole_frozen_final_snapshot_helper', HELPER['path'])
        H = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = H
        spec.loader.exec_module(H)
        H.START = started
        H.ERRORS = errors
        need(H.CUTOFF == OLD_REPORT_CUTOFF and H.MAX_INSPECTION_SECONDS == 180 and
             H.MAX_FINAL_BYTES == CAP and H.DOCKER == '/usr/bin/docker' and
             H.SMI == '/usr/local/sbin/npu-smi', 'unchanged reviewed helper constants')
        rereads.append(helper_ref)
        result['observed_start_utc'] = H.utc()
        epoch = time.time()
        result['clock'] = dict(epoch=epoch, start_epoch=START, cutoff_epoch=CUTOFF,
            historical_report_cutoff_epoch=OLD_REPORT_CUTOFF, old_window_extended=False,
            seconds_until_cutoff=CUTOFF-epoch, original_prepare3780_fits=epoch+3780<CUTOFF,
            original_source_whole3600_fits=epoch+3600<CUTOFF,
            time_observation_is_not_authority_extension=True)
        config_ref, config_body = read_ref(CONFIG)
        rereads.append(config_ref)
        config = json.loads(config_body)
        old = config['old_containers']
        need(type(old) is list and len(old) == 4 and {r['id'] for r in old} == FIRST_FOUR and
             all(r['image'] == IMAGE and type(r.get('name')) is str and
                 type(r.get('labels')) is dict for r in old),
             'exact first four configured historical owners')
        lock = Path(config.get('main_lock', config.get('MAIN_lock', '')))
        need(lock == WS/'MAIN_ADMISSION.lock' and config.get('fixed_cutoff') == OLD_REPORT_CUTOFF,
             'one original MAIN lock and unchanged hard deadline')
        diagnostic_ref, diagnostic_body = read_ref(DIAGNOSTIC['path'], expected=DIAGNOSTIC)
        rereads.append(diagnostic_ref)
        latest, joins = latest_identities(H, json.loads(diagnostic_body))
        continuation, continuation_joins, continuation_refs = continuation_identities(H)
        rereads.extend(continuation_refs)
        textonly, textonly_joins, textonly_refs = textonly_identities(H)
        rereads.extend(textonly_refs)
        old = list(old) + latest + continuation + textonly
        need(len(old) == 10 and len({r['id'] for r in old}) == 10,
             'all ten distinct exact historical CIDs')
        result['historical_identity_inputs'] = dict(helper=helper_ref, config=config_ref,
            first_four_from_config=True, first_four_OWNED_not_rederived_here=True,
            independent_diagnostic=diagnostic_ref, latest_two_saved_inspect_joins=joins,
            failed_continuation_two_OWNED_joins=continuation_joins,
            latest_textonly_two_OWNED_joins=textonly_joins)
        for row in joins:
            rereads.extend(row['inspected_refs'])
        result['self_process'] = H.proc(os.getpid())
        result['smi_before'] = H.run([H.SMI, 'info'])
        result['memory_before'] = H.read('/proc/meminfo').decode()
        result['main_lock'] = H.path_info(lock)
        result['kernel_locks_before'] = H.read('/proc/locks').decode()
        result['main_lock_kernel_matches_before'] = H.lock_matches(lock, result['kernel_locks_before'])
        result['devices_and_actual_holders'] = H.device_holders(lock)
        result['device_note'] = ('Physical0-7 inspected read-only; only physical4-7 are task targets. '
            'Declarations and visibility variables are not proof of actual allocation.')
        paths = [Path('/cache/efim/Qwen3.6-27B'), WS, OLD_OUTPUT,
                 WS/'bound-boundary-ON-v1-20261022T080000Z',
                 WS/'bound-boundary-ON-v2-20261022T100000Z', CONTINUATION_OUTPUT,
                 Path(CONTINUATION_SOURCE['path']).parent, NEW_SOURCE,
                 NEW_OUTPUT, Path(str(NEW_OUTPUT)+'-CPU')]
        result['paths_and_disks'] = [H.path_info(path) for path in paths]
        result['running_inventory_before'] = H.run([H.DOCKER, 'ps', '-q', '--no-trunc'])
        running = ids_from_inventory(H, result['running_inventory_before'])
        all_ids = sorted(set(running) | {r['id'] for r in old})
        need(len(all_ids) <= 4096, 'bounded full current/old Docker union')
        result['inspect_before'] = H.inspect(all_ids)
        result['old_before'] = H.old_identity(result['inspect_before']['containers'], old)
        result['docker_top_before'] = [H.run([H.DOCKER, 'top', cid, '-eo',
            'pid,ppid,uid,lstart,comm']) for cid in running]
        result['old_units'] = [H.run(['/usr/bin/systemctl', 'show', unit, '--no-pager',
            '--property=Id,LoadState,ActiveState,SubState,MainPID,ControlPID,Result,ExecMainStatus,ControlGroup'])
            for unit in UNITS]
        result['docker_unit'] = H.run(['/usr/bin/systemctl', 'show', 'docker.service', '--no-pager',
            '--property=MainPID,ControlGroup,ActiveState,SubState'])
        result['host_listeners_8230'] = H.run(['/usr/sbin/ss', '-lntp', 'sport = :8230'])
        result['host_listener_note'] = 'Host namespace observation only; network-none containers have their own loopback.'
        engine = H.run([H.DOCKER, 'info', '--format', '{{json .}}'])
        raw = engine.pop('stdout')
        engine.update(stdout_bytes=len(raw.encode()), stdout_sha256=hashlib.sha256(raw.encode()).hexdigest())
        result['engine_command'] = engine
        if not engine['error'] and engine['exit_code'] == 0:
            info = json.loads(raw)
            result['engine'] = {k:info.get(k) for k in ('NCPU','DockerRootDir','ServerVersion','CgroupDriver','CgroupVersion')}
            result['docker_disk'] = H.path_info(info['DockerRootDir'])
        result['memory_after'] = H.read('/proc/meminfo').decode()
        result['inspect_old_after'] = H.inspect([r['id'] for r in old])
        result['old_after'] = H.old_identity(result['inspect_old_after']['containers'], old)
        before = {r['Id']:r for r in result['inspect_before']['containers']}
        after = {r['Id']:r for r in result['inspect_old_after']['containers']}
        result['old_identity_state_stable_during_snapshot'] = all(
            cid in before and cid in after and all(before[cid][k] == after[cid][k]
                for k in ('Id','Name','Image','State','ExecIDs','labels')) for cid in (r['id'] for r in old))
        result['running_inventory_after'] = H.run([H.DOCKER, 'ps', '-q', '--no-trunc'])
        running_after = ids_from_inventory(H, result['running_inventory_after'])
        result['running_inventory_stable'] = set(running) == set(running_after)
        new_running = sorted(set(running_after) - set(running))
        result['newly_running_inspect'] = H.inspect(new_running)
        result['newly_running_top'] = [H.run([H.DOCKER, 'top', cid, '-eo',
            'pid,ppid,uid,lstart,comm']) for cid in new_running]
        result['smi_after'] = H.run([H.SMI, 'info'])
        result['kernel_locks_after'] = H.read('/proc/locks').decode()
        result['main_lock_kernel_matches_after'] = H.lock_matches(lock, result['kernel_locks_after'])
        for reference in rereads:
            read_ref(reference['path'], expected=reference)
        result['evidence_inputs_unchanged'] = True
        result['complete_mount_tables'] = share_complete_mount_members(H, result)
        result['aggregate_peak_rss'] = H.rss(['final_snapshot_textonly_v1.py'])
    except BaseException as exc:
        errors.append(type(exc).__name__ + ': ' + str(exc))
    finally:
        signal.alarm(0)
    result.update(observed_end_epoch=time.time(), elapsed_seconds=time.monotonic()-started,
        errors=errors, complete=not errors, input_refs=rereads,
        remaining_required='Observation only; no owner/resource/model-readiness or experimental admission is produced.')
    encoded = json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False)
    if len(encoded.encode()) > CAP:
        print(oversize_diagnostic(result, encoded))
        return 2
    print(encoded)
    return 0 if not errors else 2


if __name__ == '__main__':
    raise SystemExit(main())
