import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from dataclasses import make_dataclass, replace
import threading
import unittest
from unittest.mock import patch

import torch

from independent_c2_block_table_snapshot import c2_block_table_snapshot_scope
from independent_c2_cache_binding import BoundQueryWindow
from independent_c2_metadata import window_metadata

REQUESTS = (("request-a", 1, 7), ("request-b", 1, 7))


def metadata():
    values = dict(causal=True, num_decodes=0, num_decode_tokens=0, prefill=None,
        decode_meta=None, kvcomp_metadata=None, attn_state="native",
        num_actual_tokens_pcp_padded=12, num_actual_tokens=12, num_prefills=2,
        seq_lens=torch.tensor([6, 6], dtype=torch.int32),
        seq_lens_cpu=torch.tensor([6, 6], dtype=torch.int32),
        seq_lens_list=[6, 6], actual_seq_lengths_q=[6, 12],
        query_start_loc=torch.tensor([0, 6, 12], dtype=torch.int32),
        max_query_len=6,
        block_tables=torch.tensor([[4, 5], [9, 3]], dtype=torch.int32),
        slot_mapping=torch.arange(12, dtype=torch.int64), attn_mask=None)
    cls = make_dataclass("C2SnapshotMetadataFixture", [(k, object) for k in values])
    return cls(**values)


def window(block_ids=(9, 3)):
    return BoundQueryWindow(0, 2, (3, 4), (39, 12), 5, block_ids)


def candidate(native, snapshot, *, row=1, identity=REQUESTS[1], blocks=(9, 3)):
    return window_metadata(native, window(blocks), request_row=row,
        cache_hit_state="paged", block_table_reader=snapshot.read,
        request_identity=identity)


class SnapshotTests(unittest.TestCase):
    def scope(self, requests=REQUESTS, **kwargs):
        return c2_block_table_snapshot_scope(
            requests, enabled=True, source_verified_immutable=True, **kwargs)

    def assert_metadata_equal(self, left, right):
        self.assertEqual(set(vars(left)), set(vars(right)))
        for name, value in vars(left).items():
            other = getattr(right, name)
            if isinstance(value, torch.Tensor):
                self.assertTrue(torch.equal(value, other), name)
                self.assertEqual(value.dtype, other.dtype, name)
                self.assertEqual(value.device, other.device, name)
            else:
                self.assertEqual(value, other, name)

    def test_disabled_default_has_no_snapshot_or_cpu_copy(self):
        native = metadata()
        with patch.object(torch.Tensor, "cpu", side_effect=AssertionError("copy")):
            with c2_block_table_snapshot_scope(REQUESTS) as snapshot:
                self.assertIsNone(snapshot)
        self.assertEqual(native.block_tables.tolist(), [[4, 5], [9, 3]])

    def test_same_outputs_with_three_default_copies_vs_one_snapshot_copy(self):
        native = metadata()
        original = torch.Tensor.cpu
        copies = []
        def cpu(tensor, *args, **kwargs):
            copies.append(tensor.shape)
            return original(tensor, *args, **kwargs)
        with patch.object(torch.Tensor, "cpu", cpu):
            baseline = [window_metadata(native, window(), request_row=1,
                cache_hit_state="paged") for _ in range(3)]
        self.assertEqual(len(copies), 3)
        copies.clear()
        with patch.object(torch.Tensor, "cpu", cpu):
            with self.scope() as snapshot:
                observed = [candidate(native, snapshot) for _ in range(3)]
                self.assertEqual((snapshot.reads, snapshot.hits), (1, 2))
        self.assertEqual(len(copies), 1)
        for left, right in zip(baseline, observed):
            self.assert_metadata_equal(left, right)
            self.assertNotEqual(right.block_tables.data_ptr(),
                                native.block_tables.data_ptr())

    def test_full_table_snapshot_covers_later_longer_window(self):
        native = metadata()
        with self.scope() as snapshot:
            candidate(native, snapshot, blocks=(9,))
            candidate(native, snapshot, blocks=(9, 3))
            with self.assertRaises(ValueError):
                candidate(native, snapshot, blocks=(9, 4))
            self.assertEqual(snapshot.reads, 1)

    def test_native_device_table_is_still_cloned_not_replaced_by_cpu_snapshot(self):
        native = metadata()
        with self.scope() as snapshot:
            result = candidate(native, snapshot)
            self.assertEqual(result.block_tables.device, native.block_tables.device)
            result.block_tables[0, 0] = 100
            self.assertEqual(native.block_tables.tolist(), [[4, 5], [9, 3]])
            self.assertEqual(candidate(native, snapshot).block_tables.tolist(), [[9, 3]])

    def test_wrong_block_ids_rejected_in_default_and_candidate(self):
        native = metadata()
        with self.assertRaises(ValueError):
            window_metadata(native, window((9, 4)), request_row=1,
                            cache_hit_state="paged")
        with self.scope() as snapshot:
            with self.assertRaises(ValueError):
                candidate(native, snapshot, blocks=(9, 4))

    def test_missing_or_nonboolean_source_proof_rejected(self):
        for proof in (False, None, 1, "yes"):
            with self.subTest(proof=proof), self.assertRaises(ValueError):
                with c2_block_table_snapshot_scope(
                        REQUESTS, enabled=True, source_verified_immutable=proof):
                    pass

    def test_nonboolean_enable_rejected(self):
        with self.assertRaises(ValueError):
            with c2_block_table_snapshot_scope(REQUESTS, enabled=1):
                pass

    def test_request_rank_step_and_row_mismatch_rejected(self):
        native = metadata()
        invalid = [("request-a", 1, 7), ("request-b", 0, 7),
                   ("request-b", 1, 8), ("request-b", True, 7), None]
        with self.scope() as snapshot:
            for identity in invalid:
                with self.subTest(identity=identity), self.assertRaises(ValueError):
                    candidate(native, snapshot, identity=identity)
            with self.assertRaises(ValueError):
                candidate(native, snapshot, row=0)

    def test_bad_cohort_identities_and_row_maps_rejected(self):
        invalid = [(), (("request-a", 1, 7), ("request-a", 1, 7)),
            (("request-a", 1, 7), ("request-b", 1, 8)),
            (("request-a", True, 7),), (("request-a", 1, False),)]
        for requests in invalid:
            with self.subTest(requests=requests), self.assertRaises(ValueError):
                with self.scope(requests):
                    pass
        for rows in ((0,), (1, 1), (0, True), (-1, 1)):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                with self.scope(request_rows=rows):
                    pass

    def test_explicit_native_row_mapping(self):
        native = metadata()
        with self.scope(tuple(reversed(REQUESTS)), request_rows=(1, 0)) as snapshot:
            result = candidate(native, snapshot)
            self.assertEqual(result.block_tables.tolist(), [[9, 3]])

    def test_tensor_version_change_rejected(self):
        native = metadata()
        with self.scope() as snapshot:
            candidate(native, snapshot)
            native.block_tables[0, 0] += 1
            with self.assertRaises(ValueError):
                candidate(native, snapshot)

    def test_same_values_new_tensor_rejected(self):
        native = metadata()
        with self.scope() as snapshot:
            candidate(native, snapshot)
            native.block_tables = native.block_tables.clone()
            with self.assertRaises(ValueError):
                candidate(native, snapshot)

    def test_same_tensor_new_metadata_object_rejected(self):
        native = metadata()
        with self.scope() as snapshot:
            candidate(native, snapshot)
            other = replace(native)
            with self.assertRaises(ValueError):
                candidate(other, snapshot)

    def test_storage_replacement_without_version_change_rejected(self):
        native = metadata()
        with self.scope() as snapshot:
            candidate(native, snapshot)
            old_version = native.block_tables._version
            native.block_tables.data = native.block_tables.clone()
            self.assertEqual(native.block_tables._version, old_version)
            with self.assertRaises(ValueError):
                candidate(native, snapshot)

    def test_change_during_cpu_read_rejected(self):
        native = metadata()
        original = torch.Tensor.cpu
        def cpu(tensor, *args, **kwargs):
            result = original(tensor, *args, **kwargs)
            native.block_tables = native.block_tables.clone()
            return result
        with self.scope() as snapshot, patch.object(torch.Tensor, "cpu", cpu):
            with self.assertRaises(ValueError):
                candidate(native, snapshot)

    def test_inference_tensor_requires_same_proven_immutable_object(self):
        native = metadata()
        with torch.inference_mode():
            native.block_tables = native.block_tables.clone()
        with self.scope() as snapshot:
            candidate(native, snapshot)
            candidate(native, snapshot)
            self.assertEqual(snapshot.reads, 1)
            with torch.inference_mode():
                native.block_tables = native.block_tables.clone()
            with self.assertRaises(ValueError):
                candidate(native, snapshot)

    def test_closed_or_new_forward_cannot_reuse_old_snapshot(self):
        native = metadata()
        with self.scope() as old:
            candidate(native, old)
        with self.assertRaises(ValueError):
            candidate(native, old)
        with self.scope() as current:
            with self.assertRaises(ValueError):
                candidate(native, old)
            candidate(native, current)
            self.assertEqual((current.reads, current.hits), (1, 0))

    def test_scope_exception_restores_context_and_closes_reader(self):
        native = metadata()
        with self.assertRaisesRegex(RuntimeError, "sentinel"):
            with self.scope() as old:
                candidate(native, old)
                raise RuntimeError("sentinel")
        with self.assertRaises(ValueError):
            candidate(native, old)
        with self.scope() as current:
            candidate(native, current)
            self.assertEqual(current.reads, 1)

    def test_nested_enabled_scope_rejected_without_breaking_owner(self):
        native = metadata()
        with self.scope() as snapshot:
            with self.assertRaises(RuntimeError):
                with self.scope():
                    pass
            candidate(native, snapshot)
            self.assertEqual(snapshot.reads, 1)

    def test_cross_thread_even_copied_context_rejected(self):
        native = metadata()
        with self.scope() as snapshot:
            inherited = copy_context()
            def borrow():
                with self.assertRaises(ValueError):
                    inherited.run(candidate, native, snapshot)
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(borrow).result(timeout=5)
            candidate(native, snapshot)

    def test_concurrent_thread_scopes_are_independent(self):
        barrier = threading.Barrier(2)
        def run(second):
            native = metadata()
            native.block_tables[0, 0] += second
            with self.scope() as snapshot:
                barrier.wait(timeout=5)
                first = candidate(native, snapshot)
                second_result = candidate(native, snapshot)
                return snapshot.reads, snapshot.hits, first.block_tables.tolist(), second_result.block_tables.tolist()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, (0, 1)))
        self.assertEqual(results, [(1, 1, [[9, 3]], [[9, 3]])] * 2)

    def test_child_async_task_cannot_borrow_inherited_snapshot(self):
        async def run():
            native = metadata()
            with self.scope() as snapshot:
                async def borrow():
                    with self.assertRaises(ValueError):
                        candidate(native, snapshot)
                await asyncio.create_task(borrow())
                candidate(native, snapshot)
                self.assertEqual(snapshot.reads, 1)
        asyncio.run(run())

    def test_concurrent_async_scopes_are_independent(self):
        async def run_one():
            native = metadata()
            with self.scope() as snapshot:
                candidate(native, snapshot)
                await asyncio.sleep(0)
                candidate(native, snapshot)
                return snapshot.reads, snapshot.hits
        async def run():
            return await asyncio.gather(run_one(), run_one())
        self.assertEqual(asyncio.run(run()), [(1, 1), (1, 1)])

    def test_reader_coverage_validation_does_not_relax_native_guards(self):
        native = metadata()
        for reader in (False, lambda *args, **kwargs: (9,),
                       lambda *args, **kwargs: [9, 3],
                       lambda *args, **kwargs: (9, True)):
            with self.subTest(reader=reader), self.assertRaises(ValueError):
                window_metadata(native, window(), request_row=1,
                    cache_hit_state="paged", block_table_reader=reader,
                    request_identity=REQUESTS[1])
        with self.scope() as snapshot:
            native.causal = False
            with self.assertRaises(ValueError):
                candidate(native, snapshot)


if __name__ == "__main__":
    unittest.main()
