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

    module = FakeGdn()

    class FakeRunner:
        def __init__(self):
            self.model = SimpleNamespace(modules=lambda: (module,))
            self.input_batch = SimpleNamespace(req_ids=["req-a", "req-b"])
            self.requests = {
                "req-a": SimpleNamespace(num_computed_tokens=10),
                "req-b": SimpleNamespace(num_computed_tokens=20),
            }

        def _model_forward(self, *args, **kwargs):
            return module._forward_core(None, None, None, None)

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
        config, FakeGdn, FakeRunner, lambda: context
    )
    runner = FakeRunner()
    compact = module.get_kv_cache_spec(
        SimpleNamespace(scheduler_config=SimpleNamespace(max_num_seqs=3))
    )
    return module, runner, metadata, context, observed, compact, retained


def test_physical_patch_runs_dense_abi_and_commits_atomically(monkeypatch, tmp_path):
    module, runner, metadata, context, observed, compact, retained = _fixture(
        monkeypatch, tmp_path
    )
    persistent_cache = module.kv_cache
    persistent_ptrs = tuple(tensor.data_ptr() for tensor in persistent_cache)
    before_conv = persistent_cache[0].clone()
    before_temporal = persistent_cache[1].clone()

    assert compact.shapes == ((2, 3), (2, 2))
    result = runner._model_forward()

    assert result == "native-result"
    assert context.attn_metadata[module.prefix] is metadata
    bridge = module._mst_dasc_bound_bridge
    assert module.kv_cache is persistent_cache
    assert tuple(tensor.data_ptr() for tensor in persistent_cache) == persistent_ptrs
    assert observed["metadata"] is not metadata
    assert torch.equal(
        observed["metadata"].non_spec_state_indices_tensor,
        torch.tensor([0, 1], dtype=torch.int32),
    )
    dense_conv, dense_temporal = observed["cache"]
    assert dense_conv.shape == (3, 2, 3)
    assert dense_temporal.shape == (3, 4, 2)
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
        dense_temporal[:2].index_select(1, retained),
        persistent_cache[1].index_select(0, torch.tensor([6, 2])),
    )
    events = [
        json.loads(line)
        for line in (tmp_path / "evidence.jsonl").read_text().splitlines()
    ]
    bound = next(row for row in events if row["event"] == "physical_cache_bound")
    assert bound["allocation_matches_spec"] is True
    assert bound["actual_page_bytes"] == compact.page_size_bytes
    assert bound["persistent_bytes"] == (
        bound["num_blocks"] * compact.page_size_bytes
    )


def test_physical_patch_aborts_but_keeps_fixed_workspace_binding_on_native_error(
    monkeypatch, tmp_path
):
    module, runner, metadata, context, observed, _, _ = _fixture(
        monkeypatch, tmp_path, fail=True
    )
    persistent_cache = module.kv_cache
    before = tuple(tensor.clone() for tensor in persistent_cache)

    with pytest.raises(RuntimeError, match="native failure"):
        runner._model_forward()

    assert context.attn_metadata[module.prefix] is metadata
    bridge = module._mst_dasc_bound_bridge
    assert module.kv_cache is persistent_cache
    assert all(
        torch.equal(actual, expected)
        for actual, expected in zip(
            (bridge.conv_storage, bridge.temporal_storage), before
        )
    )
    assert bridge.active_owners == frozenset()
    assert observed["metadata"] is not metadata


def test_graph_boundary_reuses_buffers_with_changed_scheduler_blocks(
    monkeypatch, tmp_path
):
    module, runner, metadata, context, _, _, _ = _fixture(monkeypatch, tmp_path)

    runner._model_forward()
    bridge = module._mst_dasc_bound_bridge
    workspace_cache = bridge.workspace_cache
    workspace_ptrs = tuple(tensor.data_ptr() for tensor in workspace_cache)
    metadata_ptrs = module._mst_dasc_metadata_remapper.pointers
    active_conv_before = workspace_cache[0][:2].clone()
    active_temporal_before = workspace_cache[1][:2].clone()

    metadata.non_spec_state_indices_tensor = torch.tensor(
        [4, 7], dtype=torch.int32
    )
    before_conv = bridge.conv_storage.clone()
    before_temporal = bridge.temporal_storage.clone()
    runner._model_forward()

    assert context.attn_metadata[module.prefix] is metadata
    assert module.kv_cache is module._mst_dasc_persistent_cache
    assert tuple(tensor.data_ptr() for tensor in workspace_cache) == workspace_ptrs
    assert module._mst_dasc_metadata_remapper.pointers == metadata_ptrs
    ids = torch.tensor([4, 7])
    assert torch.equal(
        bridge.conv_storage.index_select(0, ids),
        active_conv_before + 11,
    )
    assert torch.equal(
        bridge.temporal_storage.index_select(0, ids),
        (active_temporal_before + 13).index_select(
            1, torch.tensor([0, 3])
        ),
    )
    assert torch.equal(
        workspace_cache[1][:2, [1, 2]],
        active_temporal_before[:, [1, 2]] + 13,
    )
    events = [
        json.loads(line)
        for line in (tmp_path / "evidence.jsonl").read_text().splitlines()
    ]
    assert sum(
        row["event"] == "request_active_state_initialized" for row in events
    ) == 1
    assert sum(
        row["event"] == "request_active_state_continued" for row in events
    ) == 1


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
