from __future__ import annotations

import hashlib
import unittest
from pathlib import Path
from types import SimpleNamespace

import sparse_prefix_ascend.coexistence as coexistence
from sparse_prefix_ascend.coexistence import (
    _CachingGuardBypass,
    _NativePrefixGate,
    install_native_kv_worker_validation,
)


class _FakeManager:
    def __init__(self, native_tokens: int = 3072):
        self.enable_caching = True
        self.empty_kv_cache_blocks = object()
        self.coordinator = SimpleNamespace(hash_block_size=128)
        self.native_tokens = native_tokens
        self.seen_hash_count = None

    def get_computed_blocks(self, request):
        self.seen_hash_count = len(request.block_hashes)
        return "blocks", self.native_tokens


class _FakeHypicScheduler:
    @staticmethod
    def extract_request_id(request):
        return request.request_id


class NativePrefixGateTests(unittest.TestCase):
    def test_guard_is_false_once_then_true(self):
        guard = _CachingGuardBypass()
        self.assertFalse(bool(guard))
        self.assertTrue(bool(guard))
        self.assertTrue(bool(guard))
        self.assertEqual(guard.reads, 3)

    def test_unready_checkpoint_hides_native_cache(self):
        manager = _FakeManager()
        state = SimpleNamespace(scheduler_advanced_prefixes={})
        request = SimpleNamespace(
            request_id="r0",
            block_hashes=list(range(80)),
            skip_reading_prefix_cache=False,
        )
        gate = _NativePrefixGate(manager, state, _FakeHypicScheduler)
        gate.install()
        try:
            blocks, tokens = manager.get_computed_blocks(request)
        finally:
            gate.restore()
        self.assertIs(blocks, manager.empty_kv_cache_blocks)
        self.assertEqual(tokens, 0)
        self.assertIsNone(manager.seen_hash_count)

    def test_ready_checkpoint_bounds_native_hashes(self):
        manager = _FakeManager(native_tokens=3072)
        state = SimpleNamespace(
            scheduler_advanced_prefixes={"r0": (b"hash", 3072)}
        )
        original_hashes = list(range(80))
        request = SimpleNamespace(
            request_id="r0",
            block_hashes=original_hashes,
            skip_reading_prefix_cache=False,
        )
        gate = _NativePrefixGate(manager, state, _FakeHypicScheduler)
        gate.install()
        try:
            blocks, tokens = manager.get_computed_blocks(request)
        finally:
            gate.restore()
        self.assertEqual((blocks, tokens), ("blocks", 3072))
        self.assertEqual(manager.seen_hash_count, 24)
        self.assertIs(request.block_hashes, original_hashes)

    def test_native_kv_must_match_recurrent_checkpoint(self):
        manager = _FakeManager(native_tokens=2944)
        state = SimpleNamespace(
            scheduler_advanced_prefixes={"r0": (b"hash", 3072)}
        )
        request = SimpleNamespace(
            request_id="r0",
            block_hashes=list(range(80)),
            skip_reading_prefix_cache=False,
        )
        gate = _NativePrefixGate(manager, state, _FakeHypicScheduler)
        gate.install()
        try:
            with self.assertRaisesRegex(
                RuntimeError,
                "atomic cache transaction is incomplete",
            ):
                manager.get_computed_blocks(request)
        finally:
            gate.restore()

    def test_gate_restores_preexisting_instance_override(self):
        manager = _FakeManager()
        previous = manager.get_computed_blocks
        manager.get_computed_blocks = previous
        state = SimpleNamespace(scheduler_advanced_prefixes={})
        gate = _NativePrefixGate(manager, state, _FakeHypicScheduler)
        gate.install()
        gate.restore()
        self.assertIs(manager.get_computed_blocks, previous)

    def test_worker_validator_delegates_full_attention_to_native_kv(self):
        calls = []

        def original(report, **kwargs):
            calls.append((report, kwargs))
            return "validated"

        runner = SimpleNamespace(
            __file__=__file__,
            _validate_hot_path_report=original,
        )
        expected_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        old_digest = coexistence._HYPIC_RUNNER_SHA256
        coexistence._HYPIC_RUNNER_SHA256 = expected_digest
        try:
            self.assertTrue(install_native_kv_worker_validation(runner))
            result = runner._validate_hot_path_report(
                object(),
                verified_hot_requests=2,
                expected_full_layers={"full.0", "full.1"},
                expected_gdn_layers={"gdn.0"},
                require_rope_relocation=False,
                expected_transition_composes=2,
            )
            self.assertEqual(result, "validated")
            self.assertEqual(calls[0][1]["expected_full_layers"], set())
            self.assertEqual(
                calls[0][1]["expected_gdn_layers"],
                {"gdn.0"},
            )
            self.assertEqual(
                calls[0][1]["expected_transition_composes"],
                2,
            )
            self.assertFalse(install_native_kv_worker_validation(runner))
        finally:
            coexistence._HYPIC_RUNNER_SHA256 = old_digest


if __name__ == "__main__":
    unittest.main()
