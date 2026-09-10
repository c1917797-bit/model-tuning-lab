"""Software-only checks for the independent sensitivity-capture auditor."""

import pytest
import torch

from tools import audit_gdn_sensitivity_capture as audit


def metadata(tensor):
    return {
        "shape": list(tensor.shape),
        "stride": list(tensor.stride()),
        "dtype": str(tensor.dtype),
        "device": "npu:0",
        "numel": tensor.numel(),
        "element_size": tensor.element_size(),
        "data_ptr": 11,
        "storage_ptr": 10,
        "storage_offset": 1,
        "storage_nbytes": tensor.numel() * tensor.element_size(),
        "contiguous": tensor.is_contiguous(),
    }


def base_record(step, state_initial, state_final):
    prefill = step == 0
    raw_q = torch.zeros(1, 1, 1, 128, dtype=torch.bfloat16)
    raw_k = raw_q.clone()
    raw_v = torch.zeros(1, 1, 12, 128, dtype=torch.bfloat16)
    operator_output = torch.zeros(1, 1, 12, 128, dtype=torch.bfloat16)
    common = {
        "raw_q": raw_q,
        "raw_k": raw_k,
        "raw_v": raw_v,
        "g": torch.zeros(1, 1, 12),
        "beta": torch.zeros(1, 1, 12, dtype=torch.bfloat16),
        "state_initial": state_initial,
        "operator_output": operator_output,
        "state_final": state_final,
        "norm_input": operator_output.reshape(-1, 128).clone(),
        "z": torch.zeros(12, 128, dtype=torch.bfloat16),
        "norm_output": torch.zeros(12, 128, dtype=torch.bfloat16),
        "norm_weight": torch.zeros(128, dtype=torch.bfloat16),
    }
    if prefill:
        common.update({
            "q": raw_q.clone(),
            "k": raw_k.clone(),
            "v": raw_v.clone(),
            "initial_state": state_initial.transpose(-1, -2).contiguous(),
            "cu_seqlens": torch.tensor([0, 128], dtype=torch.int32),
            "chunk_state_final": state_final.transpose(-1, -2).contiguous(),
        })
    else:
        common.update({
            "query": raw_q.squeeze(0),
            "key": raw_k.squeeze(0),
            "value": raw_v.squeeze(0),
            "actual_seq_lengths": torch.tensor([0, 1], dtype=torch.int64),
            "ssm_state_indices": torch.tensor([2], dtype=torch.int64),
        })
    state_meta = {
        "shape": [504, 12, 128, 128],
        "stride": [196608, 16384, 128, 1],
        "dtype": "torch.float32",
        "device": "npu:0",
        "numel": 99090432,
        "element_size": 4,
        "data_ptr": 101,
        "storage_ptr": 100,
        "storage_offset": 0,
        "storage_nbytes": 396361728,
        "contiguous": True,
    }
    record = {
        "schema": audit.SCHEMA,
        "manifest_sha256": audit.MANIFEST_SHA256,
        "sequence_id": "calibration-00",
        "nonce": "01234567-89ab-cdef-0123-456789abcdef",
        "rank": 0,
        "layer": 0,
        "step": step,
        "phase": "prefill" if prefill else "decode",
        "input_ids": list(range(128)) if prefill else [7],
        "positions": audit.expected_positions(step),
        "input_ids_source": "frozen_runner_input_ids_buffer_with_text_embeddings",
        "state_indices": [2],
        "state_metadata": state_meta,
        "norm": {"frozen": True},
        "scale": 128 ** -0.5,
        "operator_calls": 1,
        "tensors": common,
        "tensor_metadata": {"raw_q": metadata(raw_q)},
    }
    if prefill:
        record["has_initial_state"] = [False]
    return record, state_meta


def test_exact_is_byte_and_dtype_sensitive():
    value = torch.tensor([1, 2], dtype=torch.int32)
    assert audit.exact(value, value.clone())
    assert not audit.exact(value, value.to(torch.int64))
    assert not audit.exact(value, torch.tensor([1, 3], dtype=torch.int32))


def test_record_audit_checks_prefill_and_decode_state_continuity():
    sequence = {"id": "calibration-00", "input_ids": list(range(128))}
    ready = {"norm": {"frozen": True}}
    initial = torch.zeros(1, 12, 128, 128)
    first_final = torch.ones_like(initial)
    prefill, state_meta = base_record(0, initial, first_final)
    previous, observed_meta, slot, count = audit.verify_record(
        prefill,
        sequence=sequence,
        nonce=prefill["nonce"],
        output_ids=[7] * 9,
        rank=0,
        layer=0,
        step=0,
        ready_layer=ready,
        previous_state=None,
        stable_state_metadata=None,
    )
    assert observed_meta == state_meta
    assert slot == 2
    assert count == 18

    second_final = torch.full_like(initial, 2)
    decode, _ = base_record(1, first_final.clone(), second_final)
    next_state, _, _, count = audit.verify_record(
        decode,
        sequence=sequence,
        nonce=decode["nonce"],
        output_ids=[7] * 9,
        rank=0,
        layer=0,
        step=1,
        ready_layer=ready,
        previous_state=previous,
        stable_state_metadata=state_meta,
    )
    assert audit.exact(next_state, second_final)
    assert count == 17

    decode["tensors"]["state_initial"][0, 0, 0, 0] = 9
    with pytest.raises(ValueError, match="state continuity"):
        audit.verify_record(
            decode,
            sequence=sequence,
            nonce=decode["nonce"],
            output_ids=[7] * 9,
            rank=0,
            layer=0,
            step=1,
            ready_layer=ready,
            previous_state=previous,
            stable_state_metadata=state_meta,
        )


def test_library_identity_is_path_independent_but_requires_native_roles():
    libraries = [
        {"path": "/a/libopapi.so", "sha256": "a" * 64},
        {"path": "/b/libcust_opapi.so", "sha256": "b" * 64},
        {"path": "/c/libvllm_ascend_kernels.so", "sha256": "c" * 64},
        {"path": "/d/libcust_opsproto.so", "sha256": "d" * 64},
        {"path": "/e/libcust_opmaster.so", "sha256": "e" * 64},
    ]
    assert len(audit.verify_libraries(libraries)) == 5
    with pytest.raises(ValueError, match="library"):
        audit.verify_libraries(libraries[1:])
