import copy

import pytest

from extract_formal_identity import MODEL_CONTAINER, MODEL_HOST, PLUGIN_HOST, RESULT_HOST, extract


def inspect_value(arm):
    candidate = arm == "candidate"
    env = [
        "ASCEND_RT_VISIBLE_DEVICES=0,1,2,3",
        f"VLLM_PLUGINS={'ascend,dasc_vllm_ascend' if candidate else 'ascend'}",
        f"MST_DASC_ENABLE={'1' if candidate else '0'}",
    ]
    if candidate:
        env += ["MST_DASC_MODE=physical-cache-eager", "MST_DASC_W_MAX=64"]
    return {
        "Name": f"/dasc_qwen36_formal_v13_{arm}_20260916",
        "Image": "sha256:" + "a" * 64,
        "Config": {
            "Env": env,
            "Labels": {
                "mst.owner": "c1917797-bit",
                "mst.experiment": "dasc-qwen36-formal-ab-v13",
                "mst.arm": arm,
            },
            "Cmd": [
                "vllm", "serve", MODEL_CONTAINER,
                "--served-model-name", "qwen36-dasc-formal-v13",
                "--tensor-parallel-size", "4",
                "--mamba-cache-mode", "align",
                "--enable-prefix-caching",
                "--max-model-len", "44032",
                "--max-num-seqs", "32",
                "--block-size", "128",
                "--kv-cache-memory", "9663676416",
                "--port", "8031",
            ],
        },
        "HostConfig": {
            "NetworkMode": "host",
            "Devices": [
                {"PathOnHost": f"/dev/davinci{x}", "PathInContainer": f"/dev/davinci{x - 4}"}
                for x in range(4, 8)
            ],
        },
        "Mounts": [
            {"Destination": MODEL_CONTAINER, "Source": MODEL_HOST, "RW": False},
            {"Destination": "/workspace/dasc", "Source": PLUGIN_HOST, "RW": False},
            {"Destination": "/dasc-results", "Source": RESULT_HOST, "RW": True},
        ],
    }


@pytest.mark.parametrize("arm", ["dense", "candidate"])
def test_extracts_exact_identity(arm):
    result = extract(inspect_value(arm), arm, "c" * 40, "model", "plugin")
    assert result["dasc_plugin"] is (arm == "candidate")
    assert result["physical_npus"] == [4, 5, 6, 7]


def test_rejects_protected_device_mapping():
    value = inspect_value("dense")
    value["HostConfig"]["Devices"].append(
        {"PathOnHost": "/dev/davinci0", "PathInContainer": "/dev/davinci4"}
    )
    with pytest.raises(ValueError, match="devices"):
        extract(value, "dense", "c" * 40, "model", "plugin")


def test_rejects_candidate_with_dense_plugin_switch():
    value = copy.deepcopy(inspect_value("candidate"))
    value["Config"]["Env"] = [
        x.replace("ascend,dasc_vllm_ascend", "ascend") for x in value["Config"]["Env"]
    ]
    with pytest.raises(ValueError, match="plugins"):
        extract(value, "candidate", "c" * 40, "model", "plugin")
