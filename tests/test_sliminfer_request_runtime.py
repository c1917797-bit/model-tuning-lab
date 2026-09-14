from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from sliminfer_ascend.request_runtime import (
    PersistentRequestState,
    capture_runner_forward_identity,
    clear_request_registry_for_test,
    current_runner_forward_identity,
    get_request_state,
    put_request_state,
    runner_forward_scope,
)


class FakeBlockTable:
    def __init__(self, rows, counts, block_size):
        self._rows = np.asarray(rows, dtype=np.int32)
        self.num_blocks_per_row = np.asarray(counts, dtype=np.int32)
        self.block_size = block_size

    def get_numpy_array(self):
        return self._rows


def _runner():
    request = SimpleNamespace(num_prompt_tokens=130)
    input_batch = SimpleNamespace(
        req_ids=["request-a"],
        num_computed_tokens_cpu=np.asarray([0], dtype=np.int32),
        block_table=SimpleNamespace(
            block_tables=[
                FakeBlockTable([[11, 12, 13, 0]], [3], 128),
                FakeBlockTable([[21, 22, 0, 0]], [2], 64),
            ]
        ),
    )
    return SimpleNamespace(
        input_batch=input_batch,
        requests={"request-a": request},
    )


def test_runner_identity_captures_request_and_each_kv_group_without_device_sync():
    identity = capture_runner_forward_identity(
        _runner(), SimpleNamespace(shape=(3, 130))
    )
    request = identity.requests[0]
    assert request.req_id == "request-a"
    assert request.prompt_tokens == 130
    assert request.num_computed_tokens == 0
    assert request.scheduled_tokens == 130
    assert request.block_tables == ((11, 12, 13), (21, 22))
    assert request.kv_block_sizes == (128, 64)


def test_runner_scope_is_transactional_and_rejects_multi_request_batch():
    runner = _runner()
    with runner_forward_scope(runner, SimpleNamespace(shape=(1,))) as identity:
        assert current_runner_forward_identity() is identity
        with pytest.raises(RuntimeError, match="nested"):
            with runner_forward_scope(runner, SimpleNamespace(shape=(1,))):
                pass
    with pytest.raises(RuntimeError, match="outside"):
        current_runner_forward_identity()

    runner.input_batch.req_ids.append("request-b")
    with pytest.raises(RuntimeError, match="one request"):
        capture_runner_forward_identity(runner, SimpleNamespace(shape=(2,)))


def test_persistent_registry_uses_request_id_and_can_be_replaced():
    clear_request_registry_for_test()
    first = PersistentRequestState(
        req_id="request-a",
        prompt_tokens=130,
        block_tables=((11, 12),),
        kv_block_sizes=(128,),
    )
    put_request_state(first)
    assert get_request_state("request-a") is first
    replacement = PersistentRequestState(
        req_id="request-a",
        prompt_tokens=64,
        block_tables=((31,),),
        kv_block_sizes=(128,),
    )
    put_request_state(replacement)
    assert get_request_state("request-a") is replacement
    with pytest.raises(RuntimeError, match="missing"):
        get_request_state("request-b")
