import json
import struct
import tempfile
from pathlib import Path

from inspect_checkpoint import CheckpointContractError, inspect_checkpoint


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def _fixture(root: Path, group_size: int = 16) -> None:
    _write_json(
        root / "config.json",
        {"quantization_config": {"quant_method": "modelopt"}},
    )
    _write_json(
        root / "hf_quant_config.json",
        {
            "producer": {"name": "modelopt", "version": "test"},
            "quantization": {
                "quant_algo": "MIXED_PRECISION",
                "quantized_layers": {
                    "model.layers.0.mlp.gate_proj": {
                        "quant_algo": "NVFP4",
                        "group_size": group_size,
                    },
                    "model.layers.0.self_attn.q_proj": {"quant_algo": "FP8"},
                },
                "exclude_modules": ["mtp*"],
            },
        },
    )
    shard = "model-00001.safetensors"
    _write_json(
        root / "model.safetensors.index.json",
        {
            "weight_map": {
                "model.layers.0.mlp.gate_proj.weight": shard,
                "model.layers.0.mlp.gate_proj.weight_scale": shard,
                "model.layers.0.mlp.gate_proj.weight_scale_2": shard,
            }
        },
    )


def _write_test_shard(path: Path) -> None:
    header = {
        "model.layers.0.mlp.gate_proj.weight": {
            "dtype": "U8",
            "shape": [32, 8],
            "data_offsets": [0, 0],
        },
        "model.layers.0.mlp.gate_proj.weight_scale": {
            "dtype": "F8_E4M3",
            "shape": [32, 1],
            "data_offsets": [0, 0],
        },
        "model.layers.0.mlp.gate_proj.weight_scale_2": {
            "dtype": "F32",
            "shape": [],
            "data_offsets": [0, 0],
        },
    }
    raw = json.dumps(header).encode("utf-8")
    path.write_bytes(struct.pack("<Q", len(raw)) + raw)


def test_complete_checkpoint() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _fixture(root)
        _write_test_shard(root / "model-00001.safetensors")
        result = inspect_checkpoint(root)
        assert result["complete"]
        assert result["algorithms"] == {"FP8": 1, "NVFP4": 1}
        assert result["nvfp4_group_sizes"] == [16]
        assert result["validated_nvfp4_layers"] == 1
        assert result["nvfp4_tensor_contract_errors"] == []


def test_missing_shard_is_reported() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _fixture(root)
        result = inspect_checkpoint(root)
        assert not result["complete"]
        assert result["missing_shards"] == ["model-00001.safetensors"]


def test_group32_substitution_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _fixture(root, group_size=32)
        try:
            inspect_checkpoint(root)
        except CheckpointContractError as error:
            assert "group_size=16" in str(error)
        else:
            raise AssertionError("group32 checkpoint must fail the NVFP4 contract")


if __name__ == "__main__":
    test_complete_checkpoint()
    test_missing_shard_is_reported()
    test_group32_substitution_is_rejected()
    print("PASS: checkpoint contract inspector")
