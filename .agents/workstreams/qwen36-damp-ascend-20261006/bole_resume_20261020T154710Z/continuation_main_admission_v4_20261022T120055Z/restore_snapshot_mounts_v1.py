"""Independently restore every v4 mount member/order before old-owner checks.

Pure data validation; no host operations, source imports, model or device use.
A successful restoration is not resource admission or evidence of idleness.
"""
import hashlib
import json


def need(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode()


def uint(value):
    return type(value) is int and value >= 0


def restore(snapshot):
    need(type(snapshot) is dict and snapshot.get('schema') ==
         'bole.final-readonly-host-snapshot/v4' and
         snapshot.get('complete') is True and snapshot.get('errors') == [],
         'one complete successful live v4 observation; diagnostics cannot be restored')
    for field in ('NPU', 'resources_admitted', 'candidate_qualification',
                  'numerical_qualified', 'paired_gate_pass', 'performance_admitted',
                  'formal_performance'):
        need(snapshot.get(field) is False, 'observation has no experimental admission')
    table = snapshot['complete_mount_tables']
    need(table['schema'] == 'bole.complete-shared-projected-mount-members/v2' and
         table['original_projected_member_fields'] == ['Type', 'Source', 'Destination', 'RW'] and
         table['raw_Docker_inspect_bytes_and_SHA_receipts_retained'] is True and
         table['all_projected_members_values_order_and_duplicates_preserved'] is True and
         table['full_member_equality_required_for_hash_reuse'] is True and
         table['every_original_array_fully_reconstructed_before_publication'] is True,
         'exact v4 complete member schema, not a truncated mount projection')
    need(table['canonical_encoding'] ==
         'json.dumps(sort_keys=True,separators=(comma,colon),ensure_ascii=True,allow_nan=False).encode(utf8)',
         'one exact canonical JSON encoding')
    members, arrays, bindings = table['members'], table['arrays'], table['bindings']
    need(all(type(value) is list for value in (members, arrays, bindings)) and
         uint(table['unique_member_count']) and table['unique_member_count'] == len(members) and
         uint(table['array_count']) and uint(table['reference_count']) and
         table['array_count'] == table['reference_count'] == len(arrays) == len(bindings),
         'all member, array and reference counts agree')
    encoded_members = canonical(members)
    need(len(encoded_members) == table['complete_member_table_json_utf8_bytes'] and
         hashlib.sha256(encoded_members).hexdigest() == table['complete_member_table_sha256'],
         'whole complete member table bytes/SHA')
    seen, member_bytes = {}, 0
    for member in members:
        need(type(member) is dict and set(member) == {'Type', 'Source', 'Destination', 'RW'} and
             all(type(member[key]) is str for key in ('Type', 'Source', 'Destination')) and
             type(member['RW']) is bool, 'every full typed original mount member')
        raw = canonical(member)
        digest = hashlib.sha256(raw).hexdigest()
        need(digest not in seen, 'unique member table; no duplicate or colliding member key')
        seen[digest] = raw
        member_bytes += len(raw)
    need(member_bytes == table['unique_member_value_json_utf8_bytes'] and
         len(encoded_members) == 2 + max(0, len(members)-1) + member_bytes,
         'complete member byte accounting')
    pending, total, index = [], 0, 0
    for section in ('inspect_before', 'inspect_old_after', 'newly_running_inspect'):
        rows = snapshot[section]['containers']
        need(type(rows) is list and len({row['Id'] for row in rows}) == len(rows),
             'all exact distinct inspected containers in this pass')
        for ordinal, row in enumerate(rows):
            reference = row['mounts']
            need(type(reference) is dict and set(reference) == {
                'representation', 'array_index', 'canonical_json_sha256',
                'json_utf8_bytes', 'member_count', 'full_order_and_duplicates_preserved'} and
                reference['representation'] == 'complete_indexed_mount_members/v2' and
                reference['full_order_and_duplicates_preserved'] is True and
                uint(reference['array_index']) and reference['array_index'] == index < len(arrays),
                'one complete ordered array reference for each original inspected row')
            binding = bindings[index]
            need(binding == dict(section=section, ordinal=ordinal,
                                 container_id=row['Id'], array_index=index),
                 'complete binding to original pass, row, CID and array ordinal')
            array = arrays[index]
            need(type(array) is dict and set(array) == {
                'member_count', 'json_utf8_bytes', 'canonical_json_sha256', 'ordered_member_indices'},
                'exact complete original-array schema')
            indices = array['ordered_member_indices']
            need(type(indices) is list and uint(array['member_count']) and
                 len(indices) == array['member_count'] == reference['member_count'] and
                 all(uint(position) and position < len(members) for position in indices),
                 'all original integer indices present; ordering/repeats retained')
            restored = [members[position] for position in indices]
            encoded = canonical(restored)
            need(len(encoded) == array['json_utf8_bytes'] == reference['json_utf8_bytes'] and
                 hashlib.sha256(encoded).hexdigest() ==
                 array['canonical_json_sha256'] == reference['canonical_json_sha256'],
                 'independently reconstructed whole original ordered-array bytes/SHA')
            pending.append((row, restored))
            total += len(encoded)
            index += 1
    need(index == len(arrays) == len(bindings) and
         total == table['original_repeated_list_json_utf8_bytes'],
         'no missing, extra or unused array bindings')
    for row, restored in pending:
        row['mounts'] = restored
    return dict(schema='bole.independent-v4-mount-restoration/v1',
        array_count=index, member_count=len(members),
        original_repeated_list_json_utf8_bytes=total,
        all_members_values_order_and_duplicates_restored=True,
        resources_admitted=False, NPU=False)
