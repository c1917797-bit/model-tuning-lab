"""Small CPU-only reader controls; synthetic bytes are not model evidence."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location('boundary_reader_subject',
    Path(__file__).with_name('read_boundary_result_v2.py'))
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)


def bf16(words):
    return b''.join(struct.pack('<H', word) for word in words)


def reference(path, data):
    return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def ordered_refs():
    names = ['G0-INSTALL.json']
    for generation in (1, 2):
        p = 'G%d-' % generation
        names.append(p + 'NATIVE-INPUT-L00.json')
        names.extend(p + 'NATIVE-L%02d.json' % layer for layer in R.LAYERS)
        for name in R.RAW_SHAPES:
            names.extend([p + name + '.bin', p + 'RAW-' + name + '.json'])
        names.extend(p + phase + '.json' for phase in R.PHASES)
        names.append(p + 'RETIRE.json')
    return [dict(path='/synthetic/' + name, bytes=1, sha256='0' * 64) for name in names]


def geom(shape, dtype, unit, *, pointer=1024, offset=0):
    strides, step = [], 1
    for count in reversed(shape):
        strides.append(step)
        step *= count
    return dict(object=123, storage_ptr=pointer, storage_bytes=(step + offset) * unit,
        data_ptr=pointer + offset * unit, offset=offset, shape=list(shape),
        stride=list(reversed(strides)), dtype=dtype, device='npu:0', logical_bytes=step * unit)


class BoundaryReaderControls(unittest.TestCase):
    def test_bfloat16_values_magnitude_and_relative_norms(self):
        # BF16 exact [1,-2,3,0] versus [1,-1,5,0]: errors [0,1,2,0].
        value = R.bf16_compare(bf16([0x3f80, 0xc000, 0x4040, 0]),
                              bf16([0x3f80, 0xbf80, 0x40a0, 0]))
        self.assertEqual(value['elements'], 4)
        self.assertEqual(value['different_bits'], 2)
        self.assertEqual(value['different_numeric_values'], 2)
        self.assertEqual(value['max_abs'], 2)
        self.assertEqual(value['mean_abs'], .75)
        self.assertAlmostEqual(value['rms'], math.sqrt(5 / 4))
        self.assertAlmostEqual(value['generation_1_l2_norm'], math.sqrt(14))
        self.assertAlmostEqual(value['generation_2_l2_norm'], math.sqrt(27))
        self.assertAlmostEqual(value['norm_relative_to_generation_1'], math.sqrt(5 / 14))
        self.assertAlmostEqual(value['norm_relative_to_generation_2'], math.sqrt(5 / 27))
        self.assertIs(value['threshold_applied'], False)
        self.assertIs(value['numerical_qualification'], False)

    def test_signed_zero_bit_count_and_undefined_zero_denominator(self):
        value = R.bf16_compare(bf16([0, 0x8000]), bf16([0x8000, 0]))
        self.assertEqual(value['different_bits'], 2)
        self.assertEqual(value['different_numeric_values'], 0)
        self.assertEqual(value['rms'], 0)
        self.assertIsNone(value['norm_relative_to_generation_1'])
        self.assertIs(value['generation_1_zero_norm'], True)

    def test_nonfinite_is_counted_not_converted_to_numerical_pass(self):
        value = R.bf16_compare(bf16([0x7f80, 0xff80, 0x7fc1, 0x3f80]),
                              bf16([0x3f80, 0, 0, 0x3f80]))
        self.assertIs(value['all_finite'], False)
        self.assertEqual(value['generation_1_finite'], 1)
        self.assertEqual(value['generation_2_finite'], 4)
        self.assertEqual(value['finite_pairs'], 1)
        self.assertIs(value['numerical_qualification'], False)

    def test_truncated_odd_empty_and_oversized_binary_rejected(self):
        for first, second in ((b'', b''), (b'x', b'x'), (b'00', b'0000'),
                              (b'\0' * (96 * 1024 + 2), b'\0' * (96 * 1024 + 2))):
            with self.subTest(bytes=(len(first), len(second))):
                with self.assertRaises(ValueError):
                    R.bf16_compare(first, second)

    def test_whole_sha_not_prefix_and_changes_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'data.json'
            data = b'{"value":1}\n'
            path.write_bytes(data)
            reader = R.Readset()
            ref = reference(path, data)
            self.assertEqual(reader.obj(ref), {'value': 1})
            before, after = reader.finish()
            self.assertEqual(before, after)
            path.write_bytes(b'{"value":2}\n')
            with self.assertRaises(ValueError):
                reader.finish()
            with self.assertRaises(ValueError):
                R.Readset().read(dict(ref, bytes=len(data)-1))

    def test_symlinks_and_directory_inputs_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            file = root/'real'
            file.write_bytes(b'x')
            link = root/'link'
            link.symlink_to(file)
            with self.assertRaises(ValueError):
                R.Readset().read(reference(link, b'x'))
            directory = root/'dir'
            directory.mkdir()
            with self.assertRaises(ValueError):
                R.Readset().discover(directory)

    def test_refs_are_exact_typed_and_duplicates_conflict(self):
        value = dict(path='/synthetic/a', bytes=1, sha256='a' * 64)
        for bad in (dict(value, bytes=True), dict(value, extra=1),
                    dict(value, sha256='A' * 64), dict(value, path='/a/../b')):
            with self.assertRaises(ValueError):
                R.typed_ref(bad)
        self.assertEqual(len(R.ref_map([value, value])), 1)
        with self.assertRaises(ValueError):
            R.ref_map([value, dict(value, sha256='b' * 64)])

    def test_strict_json_duplicate_and_nonfinite_rejected(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.assertRaises(ValueError):
                R.strict_json(text)

    def test_complete_names_and_event_order_cannot_drop_a_frame(self):
        names = R.expected_names()
        self.assertEqual(len(names), 148)
        self.assertEqual(sum(name.endswith('.json') for name in names), 130)
        refs = ordered_refs()
        order = R.validate_order(refs)
        self.assertEqual(len(order), 64)
        self.assertEqual(order[0], 'NATIVE-INPUT-L00')
        self.assertEqual(order[-1], 'RETIRE')
        for bad in (refs[:-1], refs + [refs[-1]], [refs[1], refs[0], *refs[2:]]):
            with self.assertRaises(ValueError):
                R.validate_order(bad)

    def test_calibration_phase_order_is_required(self):
        refs = ordered_refs()
        a = next(i for i, ref in enumerate(refs) if ref['path'].endswith('G1-calibration_before.json'))
        b = next(i for i, ref in enumerate(refs) if ref['path'].endswith('G1-calibration_after.json'))
        refs[a], refs[b] = refs[b], refs[a]
        with self.assertRaises(ValueError):
            R.validate_order(refs)

    def test_geometry_logical_extent_and_storage_bounds(self):
        value = geom((131, 2560), 'torch.bfloat16', 2)
        R.geometry(value, expected_shape=(131, 2560), expected_dtype='torch.bfloat16')
        for bad in (dict(value, logical_bytes=2), dict(value, storage_bytes=value['storage_bytes']-2),
                    dict(value, offset=1), dict(value, shape=[131, True])):
            with self.assertRaises(ValueError):
                R.geometry(bad, expected_shape=(131, 2560), expected_dtype='torch.bfloat16')

    def test_full_conv_extra_is_not_mistaken_for_active_finite_gate(self):
        state = geom((2, 12, 128, 128), 'torch.float32', 4)
        conv = geom((2, 16, 2560), 'torch.bfloat16', 2)
        ss = dict(state, shape=state['shape'][1:], stride=state['stride'][1:], logical_bytes=786432)
        cs = dict(conv, shape=conv['shape'][1:], stride=conv['stride'][1:], logical_bytes=81920)
        slot = dict(state='a'*64, conv_full='b'*64, conv_leading3='c'*64,
            state_finite=True, conv_leading3_finite=True, conv_extra_numerical_gate=False,
            geometry=dict(state_arena=state, conv_arena=conv, selected_state=ss, selected_conv=cs,
                          selected_slot=0, conv_numerical_active_extent=[0,3], conv_full_storage_extent=[0,16]))
        R.slot_record(slot)
        bad = copy.deepcopy(slot)
        bad['conv_extra_numerical_gate'] = True
        with self.assertRaises(ValueError):
            R.slot_record(bad)
        bad = copy.deepcopy(slot)
        bad['geometry']['selected_slot'] = 1
        with self.assertRaises(ValueError):
            R.slot_record(bad)

    def test_same_requests_have_no_automatic_state_or_numerical_admission(self):
        request = dict(prompt=[1]*131, max_tokens=8, seed=0)
        rows = [dict(request=copy.deepcopy(request), id='cmpl-a', token_ids=[1]*8),
                dict(request=copy.deepcopy(request), id='cmpl-b', token_ids=[1]*7+[2])]
        value = R.compare_http(dict(rows=rows), dict(path='/synthetic/http'))
        self.assertIs(value['request_payload_equal'], True)
        self.assertIs(value['same_explicit_seed'], True)
        self.assertIs(value['identical_initial_state_assumed'], False)
        self.assertEqual(value['output_token_differences'], [dict(index=7, generation_1=1, generation_2=2)])


if __name__ == '__main__':
    unittest.main(verbosity=2)
