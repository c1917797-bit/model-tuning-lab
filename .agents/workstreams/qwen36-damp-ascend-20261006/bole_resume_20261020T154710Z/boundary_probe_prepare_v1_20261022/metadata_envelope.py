"""Pure JSON capacity calculation; fabricated bounds, never NPU evidence.

Uses exact observer schema with conservative 64-bit metadata values, maximum
encoded identifiers/paths, conv16 and eight draft-cache inventory entries.
No output tensor values or qualification receipts are synthesized.
"""
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('boundary_capacity_subject',
                                             Path(__file__).with_name('boundary_probe_v1.py'))
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
U = 2**64 - 1
SHA = 'f' * 64
SOURCE = dict(path='/' + 's' * 1023, bytes=U, sha256=SHA)
ROOT = '/' + 'r' * 199
REFS = []
META = []
RAW = []


def ref(name, size):
    value = dict(path=ROOT + '/BOUNDARY-R3/' + name, bytes=size, sha256=SHA)
    REFS.append(value)
    return value


def emit(gen, event, record):
    value = dict(schema=B.SCHEMA, source_sha256=SHA, rank=3, pid=U,
                 generation=gen, event=event, record=record,
                 numerical_qualified=False, formal_performance=False)
    data = B.canonical(value)
    META.append((event, len(data)))
    return ref('G%d-%s.json' % (gen, event), len(data))


def geometry(shape, dtype, logical):
    return dict(object=U, storage_ptr=U, storage_bytes=U, data_ptr=U,
                offset=U, shape=shape, stride=[U] * len(shape), dtype=dtype,
                device='npu:' + '9' * 12, logical_bytes=logical)


def digest():
    return dict(state=SHA, conv_full=SHA, conv_leading3=SHA,
                state_finite=True, conv_leading3_finite=True,
                conv_extra_numerical_gate=False)


def slot_geometry():
    return dict(state_arena=geometry([U, 12, 128, 128], 'torch.float32', U),
                conv_arena=geometry([U, 16, 2560], 'torch.bfloat16', U),
                selected_state=geometry([12, 128, 128], 'torch.float32', 786432),
                selected_conv=geometry([16, 2560], 'torch.bfloat16', 81920),
                selected_slot=U, conv_numerical_active_extent=[0, 3],
                conv_full_storage_extent=[0, 16])


def inventory():
    return dict(drafter_object=U, draft_model_object=U,
        cache_storage_inventory=[dict(module='m' * 128, module_object=U, item=U,
             geometry=geometry([U] * 5, 'd' * 24, U)) for _ in range(8)],
        draft_actual_write_footprint_known=False, alias_exclusion_proven=False,
        shared_allocation_alone_is_not_alias_bug_evidence=True,
        limitation='active draft slots/write extents not source-proved by this observer')


def main():
    emit(0, 'INSTALL', dict(source=SOURCE, worker=U, runner=U, model=U,
        hooks=4, hooks_return_none=True, native_math_replaced=False,
        blocking_D2H_observation=True, explicit_stream_or_event_manipulation=False))
    for gen in (1, 2):
        inputs = {}
        for name in ('mixed_qkv', 'b', 'a'):
            shape = B.RAW_SHAPES['layer1_' + name]
            size = 2
            for axis in shape:
                size *= axis
            inputs[name] = dict(sha256=SHA, bytes=size, shape=list(shape),
                dtype='torch.bfloat16', finite=True,
                geometry=geometry(list(shape), 'torch.bfloat16', size))
        emit(gen, 'NATIVE-INPUT-L00', dict(rows=inputs, layer=0,
            before_original_native_core=True, full_actual131_inputs=True, raw_values_preserved=False))
        for layer in B.GDN_LAYERS:
            row = digest()
            row['geometry'] = slot_geometry()
            emit(gen, 'NATIVE-L%02d' % layer, dict(layer=layer, prefix='p' * 128,
                request='q' * 128, request_object=U, metadata_object=U,
                core_return_observed_before_registration=True, slot=row))
        for name, shape in B.RAW_SHAPES.items():
            full = 2
            for axis in shape:
                full *= axis
            size = full // 131 * 8
            raw_ref = ref('G%d-%s.bin' % (gen, name), size)
            RAW.append(size)
            emit(gen, 'RAW-' + name, dict(name=name, logical_shape=list(shape),
                logical_sha256=SHA, logical_bytes=full, logical_finite=True,
                logical_geometry=geometry(list(shape), 'torch.bfloat16', full),
                actual_token_slice=[123, 131], raw=raw_ref, raw_slice_is_full_tensor=False,
                raw_slice_numerical_qualification=False,
                element_encoding='little-endian IEEE bfloat16; contiguous logical order'))
        for phase in B.PHASES:
            context = {}
            if phase == 'calibration_before':
                context = dict(generation=gen, created=False)
            elif phase == 'calibration_after':
                context = dict(generation=gen, created=False,
                    calibration_ref=dict(path=ROOT + '/' + 'c' * 80, bytes=U, sha256=SHA))
            elif phase.startswith('initial_mtp_'):
                context = dict(draft=inventory())
            rows = [dict(layer=layer, slot=U,
                digest={k: SHA for k in ('state', 'conv_full', 'conv_leading3')})
                for layer in B.GDN_LAYERS]
            emit(gen, phase, dict(rows=rows, context=context,
                state_finite=True, conv_leading3_finite=True,
                conv_extra_numerical_gate=False, storage_geometry_equal_native=True,
                numerical_equality_is_observed_not_required=True))
        emit(gen, 'RETIRE', dict(original_record_sha256=SHA, request='q' * 128,
            generation=gen, original_retirement_schema='bole.service-owner-native-retirement/v1',
            original_retirement_steps=7, output_token_ids=[U] * 8,
            actual_native_request_absent=True, device_read_bytes=B.DEVICE_READ_CAP,
            raw_bytes=B.RAW_CAP, metadata_bytes_before_record=B.META_CAP))
    emit(2, 'COMPLETE', dict(source=SOURCE, references=list(REFS),
        requests=['q' * 128, 'z' * 128], hooks_removed=True,
        device_read_bytes=B.DEVICE_READ_CAP, raw_bytes=B.RAW_CAP,
        metadata_bytes_before_index=B.META_CAP,
        observation_complete=True, draft_actual_write_footprint_known=False,
        alias_exclusion_proven=False, diagnostic_only=True))
    metadata = sum(size for _, size in META)
    maximum = max(META, key=lambda item: item[1])
    reads = 2 * 6 * 48 * (12 * 128 * 128 * 4 + 16 * 2560 * 2)
    full_raw_reads = sum(RAW) * 131 // 8
    native0_reads = 2 * (131 * 2560 * 2 + 2 * 131 * 12 * 2)
    result = dict(schema='bole.boundary-source-only-capacity-calculation/v1',
        fabricated_bounds_only=True, NPU=False, qualification=False,
        maximum_conv_width=16, maximum_draft_inventory_tensors=8,
        metadata_files=len(META), raw_files=len(RAW), all_files=len(REFS),
        metadata_upper_bound_bytes=metadata, metadata_cap=B.META_CAP,
        largest_metadata_file=dict(event=maximum[0], bytes=maximum[1]),
        per_metadata_file_cap=128 * 1024, exact_raw_bytes=sum(RAW), raw_cap=B.RAW_CAP,
        bounded_device_read_bytes=reads + full_raw_reads + native0_reads,
        device_read_cap=B.DEVICE_READ_CAP,
        original_other_actual_max=1668008, added_bytes=metadata + sum(RAW),
        retained_other_headroom=B.OTHER_HEADROOM,
        bounded_other_total_with_headroom=1668008 + metadata + sum(RAW) + B.OTHER_HEADROOM,
        original_other_cap=3 * 2**20,
        runtime_recounts_actual_original_buckets=True,
        statement='Capacity calculation only; no device run or numerical result.')
    print(json.dumps(result, sort_keys=True, indent=2))
    if not (metadata <= B.META_CAP and maximum[1] <= 128 * 1024 and
            sum(RAW) == B.RAW_CAP and len(REFS) == 148 and
            result['bounded_device_read_bytes'] <= B.DEVICE_READ_CAP and
            result['bounded_other_total_with_headroom'] <= 3 * 2**20):
        raise ValueError('capacity does not fit the unchanged original allocation')


if __name__ == '__main__':
    main()

