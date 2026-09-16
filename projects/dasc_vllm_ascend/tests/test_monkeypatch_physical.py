from dataclasses import dataclass
import json
from types import SimpleNamespace

import pytest
import torch

import dasc_vllm_ascend.monkeypatch as physical_patch
from vllm.v1.attention.backends.registry import MambaAttentionBackendEnum
from vllm.v1.kv_cache_interface import MambaSpec


@dataclass
class Metadata:
    non_spec_state_indices_tensor: torch.Tensor


def _dense_spec():
    return MambaSpec(
        block_size=1536,
        shapes=((2, 3), (4, 2)),
        dtypes=(torch.float32, torch.float32),
        page_size_padded=None,
        mamba_type=MambaAttentionBackendEnum.GDN_ATTN,
        mamba_cache_mode="align",
    )


def _fixture(monkeypatch, tmp_path, *, fail=False):
    metadata = Metadata(torch.tensor([6, 2], dtype=torch.int32))
    context = SimpleNamespace(attn_metadata={"layers.0": metadata})
    observed = {}

    class FakeGdn:
        def __init__(self):
            self.prefix = "layers.0"
            self.A_log = torch.zeros(4)
            self.dt_bias = torch.zeros(4)
            self.kv_cache = (
                torch.arange(8 * 2 * 3, dtype=torch.float32).view(8, 2, 3),
                torch.arange(8 * 2 * 2, dtype=torch.float32).view(8, 2, 2),
            )

        def get_kv_cache_spec(self, vllm_config):
            return _dense_spec()

        def _forward_core(self, mixed_qkv, b, a, core_attn_out):
            observed["metadata"] = context.attn_metadata[self.prefix]
            observed["cache"] = self.kv_cache
            observed["cache_before"] = tuple(tensor.clone() for tensor in self.kv_cache)
            if fail:
                raise RuntimeError("native failure")
            self.kv_cache[0].add_(11)
            self.kv_cache[1].add_(13)
            return "native-result"

    config = SimpleNamespace(
        representative_a=-0.3,
        epsilon=0.001,
        w_max=64,
        evidence_path=tmp_path / "evidence.jsonl",
        mode="physical-cache-eager",
    )
    retained = torch.tensor([0, 3], dtype=torch.long)
    monkeypatch.setattr(
        physical_patch, "retained_head_indices", lambda module, cfg: retained
    )
    physical_patch._install_physical_cache_patch(
        config, FakeGdn, lambda: context
    )
    module = FakeGdn()
    compact = module.get_kv_cache_spec(
        SimpleNamespace(scheduler_config=SimpleNamespace(max_num_seqs=3))
    )
    return module, metadata, context, observed, compact, retained


def test_physical_patch_runs_dense_abi_and_commits_atomically(monkeypatch, tmp_path):
    module, metadata, context, observed, compact, retained = _fixture(
        monkeypatch, tmp_path
    )
    persistent_cache = module.kv_cache
    persistent_ptrs = tuple(tensor.data_ptr() for tensor in persistent_cache)
    before_conv = persistent_cache[0].clone()
    before_temporal = persistent_cache[1].clone()

    assert compact.shapes == ((2, 3), (2, 2))
    result = module._forward_core(None, None, None, None)

    assert result == "native-result"
    assert context.attn_metadata[module.prefix] is metadata
    assert module.kv_cache is persistent_cache
    assert tuple(tensor.data_ptr() for tensor in module.kv_cache) == persistent_ptrs
    assert observed["metadata"] is not metadata
    assert torch.equal(
        observed["metadata"].non_spec_state_indices_tensor,
        torch.tensor([1, 0], dtype=torch.int32),
    )
    dense_conv, dense_temporal = observed["cache"]
    assert dense_conv.shape == (2, 2, 3)
    assert dense_temporal.shape == (2, 4, 2)
    assert torch.equal(
        persistent_cache[0].index_select(0, torch.tensor([6, 2])),
        before_conv.index_select(0, torch.tensor([6, 2])) + 11,
    )
    assert torch.equal(
        persistent_cache[1].index_select(0, torch.tensor([6, 2])),
        before_temporal.index_select(0, torch.tensor([6, 2])) + 13,
    )
    assert torch.count_nonzero(observed["cache_before"][1][:, [1, 2]]).item() == 0
    assert torch.equal(
        dense_temporal.index_select(1, retained),
        persistent_cache[1].index_select(0, torch.tensor([2, 6])),
    )


def test_physical_patch_aborts_and_restores_bindings_on_native_error(
    monkeypatch, tmp_path
):
    module, metadata, context, observed, _, _ = _fixture(
        monkeypatch, tmp_path, fail=True
    )
    persistent_cache = module.kv_cache
    before = tuple(tensor.clone() for tensor in persistent_cache)

    with pytest.raises(RuntimeError, match="native failure"):
        module._forward_core(None, None, None, None)

    assert context.attn_metadata[module.prefix] is metadata
    assert module.kv_cache is persistent_cache
    assert all(torch.equal(actual, expected) for actual, expected in zip(module.kv_cache, before))
    assert module._mst_dasc_bound_bridge._active_ids is None
    assert observed["metadata"] is not metadata


def test_aligned_hybrid_grouping_preserves_exact_inner_page_sizes(tmp_path):
    from vllm.v1.kv_cache_interface import FullAttentionSpec, UniformTypeKVCacheSpecs

    attention = FullAttentionSpec(
        block_size=1536,
        num_kv_heads=1,
        head_size=128,
        dtype=torch.bfloat16,
    )
    mamba6 = MambaSpec(
        block_size=1536,
        shapes=((3, 16), (6, 128, 128)),
        dtypes=(torch.bfloat16, torch.float32),
        mamba_type=MambaAttentionBackendEnum.GDN_ATTN,
        mamba_cache_mode="align",
    )
    mamba12 = MambaSpec(
        block_size=1536,
        shapes=((3, 16), (12, 128, 128)),
        dtypes=(torch.bfloat16, torch.float32),
        mamba_type=MambaAttentionBackendEnum.GDN_ATTN,
        mamba_cache_mode="align",
    )
    namespace = SimpleNamespace(
        get_kv_cache_groups=lambda *_: (_ for _ in ()).throw(
            AssertionError("fallback must not run")
        )
    )
    config = SimpleNamespace(
        mode="physical-cache-eager", evidence_path=tmp_path / "events.jsonl"
    )
    physical_patch._install_aligned_hybrid_grouping_patch(config, namespace)
    groups = namespace.get_kv_cache_groups(
        SimpleNamespace(),
        {"mamba6": mamba6, "attn": attention, "mamba12": mamba12},
    )
    assert len(groups) == 1
    assert isinstance(groups[0].kv_cache_spec, UniformTypeKVCacheSpecs)
    inner = groups[0].kv_cache_spec.kv_cache_specs
    assert list(inner) == ["mamba6", "attn", "mamba12"]
    assert inner["mamba6"].page_size_bytes < inner["mamba12"].page_size_bytes


def test_aligned_hybrid_grouping_rejects_hidden_cache(tmp_path):
    from vllm.v1.kv_cache_interface import FullAttentionSpec, HiddenStateCacheSpec

    specs = {
        "attn": FullAttentionSpec(
            block_size=1536,
            num_kv_heads=1,
            head_size=128,
            dtype=torch.bfloat16,
        ),
        "mamba1": MambaSpec(
            block_size=1536,
            shapes=((3, 16), (1, 128, 128)),
            dtypes=(torch.bfloat16, torch.float32),
            mamba_type=MambaAttentionBackendEnum.GDN_ATTN,
            mamba_cache_mode="align",
        ),
        "mamba2": MambaSpec(
            block_size=1536,
            shapes=((3, 16), (2, 128, 128)),
            dtypes=(torch.bfloat16, torch.float32),
            mamba_type=MambaAttentionBackendEnum.GDN_ATTN,
            mamba_cache_mode="align",
        ),
        "hidden": HiddenStateCacheSpec(
            block_size=1536,
            num_kv_heads=1,
            head_size=128,
            dtype=torch.bfloat16,
        ),
    }
    namespace = SimpleNamespace(get_kv_cache_groups=lambda *_: [])
    config = SimpleNamespace(
        mode="physical-cache-eager", evidence_path=tmp_path / "events.jsonl"
    )
    physical_patch._install_aligned_hybrid_grouping_patch(config, namespace)
    with pytest.raises(physical_patch.DascRuntimeUnsupported, match="hidden-state"):
        namespace.get_kv_cache_groups(SimpleNamespace(), specs)


def test_heterogeneous_input_batch_dispatch_preserves_storage_order(tmp_path):
    from vllm.v1.kv_cache_interface import (
        FullAttentionSpec,
        KVCacheConfig,
        KVCacheGroupSpec,
        UniformTypeKVCacheSpecs,
    )

    attention = FullAttentionSpec(
        block_size=1536,
        num_kv_heads=1,
        head_size=128,
        dtype=torch.bfloat16,
    )
    mamba6 = MambaSpec(
        block_size=1536,
        shapes=((3, 16), (6, 128, 128)),
        dtypes=(torch.bfloat16, torch.float32),
        mamba_type=MambaAttentionBackendEnum.GDN_ATTN,
        mamba_cache_mode="align",
    )
    mamba12 = MambaSpec(
        block_size=1536,
        shapes=((3, 16), (12, 128, 128)),
        dtypes=(torch.bfloat16, torch.float32),
        mamba_type=MambaAttentionBackendEnum.GDN_ATTN,
        mamba_cache_mode="align",
    )
    storage_inner = {
        "mamba6": mamba6,
        "attn": attention,
        "mamba12": mamba12,
    }
    aggregate = UniformTypeKVCacheSpecs(
        block_size=1536,
        kv_cache_specs=storage_inner,
    )
    group = KVCacheGroupSpec(
        layer_names=["mamba6", "attn", "mamba12"],
        kv_cache_spec=aggregate,
    )
    cache_config = KVCacheConfig(
        num_blocks=8,
        kv_cache_tensors=[],
        kv_cache_groups=[group],
    )
    observed = {}

    class FakeRunner:
        def may_reinitialize_input_batch(self, received):
            received_group = received.kv_cache_groups[0]
            observed["config"] = received
            observed["layer_names"] = list(received_group.layer_names)
            observed["dispatch_order"] = list(
                received_group.kv_cache_spec.kv_cache_specs
            )
            return "reinitialized"

    evidence_path = tmp_path / "events.jsonl"
    config = SimpleNamespace(
        mode="physical-cache-eager", evidence_path=evidence_path
    )
    physical_patch._install_heterogeneous_input_batch_dispatch_patch(
        config, FakeRunner
    )

    assert FakeRunner().may_reinitialize_input_batch(cache_config) == "reinitialized"
    assert observed["config"] is not cache_config
    assert observed["dispatch_order"] == ["attn", "mamba6", "mamba12"]
    assert observed["layer_names"] == ["mamba6", "attn", "mamba12"]
    assert list(cache_config.kv_cache_groups[0].kv_cache_spec.kv_cache_specs) == [
        "mamba6",
        "attn",
        "mamba12",
    ]
    events = [json.loads(line) for line in evidence_path.read_text().splitlines()]
    adapted = [
        event
        for event in events
        if event["event"] == "heterogeneous_input_batch_dispatch_adapted"
    ]
    assert len(adapted) == 1
    assert adapted[0]["groups"] == [
        {
            "group_id": 0,
            "storage_first": "mamba6",
            "dispatch_first": "attn",
            "attention_layers": 1,
            "mamba_layers": 2,
        }
    ]


def test_heterogeneous_input_batch_dispatch_leaves_plain_group_unchanged(tmp_path):
    from vllm.v1.kv_cache_interface import (
        FullAttentionSpec,
        KVCacheConfig,
        KVCacheGroupSpec,
    )

    attention = FullAttentionSpec(
        block_size=1536,
        num_kv_heads=1,
        head_size=128,
        dtype=torch.bfloat16,
    )
    cache_config = KVCacheConfig(
        num_blocks=8,
        kv_cache_tensors=[],
        kv_cache_groups=[
            KVCacheGroupSpec(layer_names=["attn"], kv_cache_spec=attention)
        ],
    )
    observed = {}

    class FakeRunner:
        def may_reinitialize_input_batch(self, received):
            observed["config"] = received

    config = SimpleNamespace(
        mode="physical-cache-eager", evidence_path=tmp_path / "events.jsonl"
    )
    physical_patch._install_heterogeneous_input_batch_dispatch_patch(
        config, FakeRunner
    )
    FakeRunner().may_reinitialize_input_batch(cache_config)
    assert observed["config"] is cache_config
    assert not config.evidence_path.exists()


def test_heterogeneous_cascade_guard_disables_only_uniform_group(tmp_path):
    from vllm.v1.kv_cache_interface import (
        FullAttentionSpec,
        KVCacheGroupSpec,
        UniformTypeKVCacheSpecs,
    )

    attention = FullAttentionSpec(
        block_size=1536,
        num_kv_heads=1,
        head_size=128,
        dtype=torch.bfloat16,
    )
    aggregate = UniformTypeKVCacheSpecs(
        block_size=1536,
        kv_cache_specs={"attn": attention},
    )

    class FakeRunner:
        def _compute_cascade_attn_prefix_lens(self, *args, **kwargs):
            return [["original"]]

    config = SimpleNamespace(
        mode="physical-cache-eager", evidence_path=tmp_path / "events.jsonl"
    )
    physical_patch._install_heterogeneous_cascade_guard(config, FakeRunner)

    runner = FakeRunner()
    runner.kv_cache_config = SimpleNamespace(
        kv_cache_groups=[KVCacheGroupSpec(["attn"], aggregate)]
    )
    assert runner._compute_cascade_attn_prefix_lens(None, None, None) is None
    assert runner._mst_dasc_cascade_guard_emitted

    runner.kv_cache_config = SimpleNamespace(
        kv_cache_groups=[KVCacheGroupSpec(["attn"], attention)]
    )
    assert runner._compute_cascade_attn_prefix_lens(None, None, None) == [
        ["original"]
    ]


def test_heterogeneous_mamba_lifecycle_filters_attention_layers(tmp_path):
    from vllm.v1.kv_cache_interface import (
        FullAttentionSpec,
        KVCacheGroupSpec,
        UniformTypeKVCacheSpecs,
    )

    attention = FullAttentionSpec(
        block_size=1536,
        num_kv_heads=1,
        head_size=128,
        dtype=torch.bfloat16,
    )
    mamba6 = MambaSpec(
        block_size=1536,
        shapes=((3, 16), (6, 128, 128)),
        dtypes=(torch.bfloat16, torch.float32),
        mamba_type=MambaAttentionBackendEnum.GDN_ATTN,
        mamba_cache_mode="align",
    )
    mamba12 = MambaSpec(
        block_size=1536,
        shapes=((3, 16), (12, 128, 128)),
        dtypes=(torch.bfloat16, torch.float32),
        mamba_type=MambaAttentionBackendEnum.GDN_ATTN,
        mamba_cache_mode="align",
    )
    aggregate = UniformTypeKVCacheSpecs(
        block_size=1536,
        kv_cache_specs={
            "attn": attention,
            "mamba6": mamba6,
            "mamba12": mamba12,
        },
    )
    cache_config = SimpleNamespace(
        kv_cache_groups=[
            KVCacheGroupSpec(["attn", "mamba6", "mamba12"], aggregate)
        ]
    )
    observed = {}

    class FakeBuffers:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

        @classmethod
        def create(cls, *_args, **_kwargs):
            raise AssertionError("aggregate must use DASC creation")

    def original_collect(_bufs, proxied, *_args):
        observed["layer_names"] = proxied.kv_cache_groups[0].layer_names

    namespace = SimpleNamespace(
        get_mamba_groups=lambda *_: (_ for _ in ()).throw(
            AssertionError("aggregate must use DASC group discovery")
        ),
        MambaCopyBuffers=FakeBuffers,
        collect_mamba_copy_meta=original_collect,
    )
    config = SimpleNamespace(
        mode="physical-cache-eager", evidence_path=tmp_path / "events.jsonl"
    )
    physical_patch._install_heterogeneous_mamba_lifecycle_patch(config, namespace)

    allocations = []

    def make_buffer(count, dtype):
        allocations.append((count, dtype))
        return SimpleNamespace(count=count, dtype=dtype)

    buffers = FakeBuffers.create(3, cache_config, (object(), object()), make_buffer)
    assert buffers.mamba_group_ids == [0]
    assert buffers.mamba_spec is mamba6
    assert allocations == [
        (12, torch.int64),
        (12, torch.int64),
        (12, torch.int32),
    ]

    namespace.collect_mamba_copy_meta(
        buffers,
        cache_config,
        (object(), object()),
        [0],
        0,
        1,
        0,
        SimpleNamespace(),
        {},
    )
    assert observed["layer_names"] == ["mamba6", "mamba12"]
