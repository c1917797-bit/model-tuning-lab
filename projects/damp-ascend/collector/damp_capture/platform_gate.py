"""Fresh-process same-image NO-NPU platform/source/schema preflight."""
from __future__ import annotations
import argparse
import glob
import importlib.metadata
import json
import os
from .contract import GDN_SHA, RUNNER_SHA, file_digest, require


def inspect_platform():
    require(os.environ.get("DAMP_NO_DEVICE_TOKENIZER_GATE")=="1" and
            os.environ.get("ASCEND_RT_VISIBLE_DEVICES","")=="" and
            not glob.glob("/dev/davinci[0-9]*"), "platform preflight requires NO NPU devices")
    require(os.environ.get("VLLM_PLUGINS")=="ascend,ascend_kv_connector,ascend_model,ascend_model_loader,damp_capture",
            "platform plugin must not be filtered out")
    require(os.environ.get("DAMP_CAPTURE_ENABLE","0")=="0", "source preflight must not capture")
    points=importlib.metadata.entry_points()
    def group(name):
        selected=points.select(group=name) if hasattr(points,"select") else points.get(name,())
        return sorted(({"name":e.name,"value":e.value} for e in selected),key=lambda e:e["name"])
    inventory={name:group(name) for name in ("vllm.platform_plugins","vllm.general_plugins")}
    require(any(e["name"]=="ascend" for e in inventory["vllm.platform_plugins"]),
            "Ascend platform entrypoint absent")
    require(any(e["name"]=="damp_capture" for e in inventory["vllm.general_plugins"]),
            "DAMP general entrypoint absent")
    required_general={"ascend_kv_connector","ascend_model","ascend_model_loader","damp_capture"}
    require(required_general <= {e["name"] for e in inventory["vllm.general_plugins"]},
            "required Ascend general entrypoint absent")
    from vllm.platforms import current_platform
    require(current_platform.device_type=="npu" and
            type(current_platform).__module__.startswith("vllm_ascend."),
            "current_platform is not Ascend")
    from vllm.plugins import load_general_plugins
    load_general_plugins()
    import vllm_ascend
    require(vllm_ascend._GLOBAL_PATCH_APPLIED, "Ascend global runtime adaptation did not execute")
    # After activating NPUPlatform, importing FLA/gdn can query the actual SoC
    # via Triton. A NO-device check must read source, not pretend that import is
    # driver-free. Real dispatch is still a separate live-NPU smoke gate.
    from pathlib import Path
    package = Path(vllm_ascend.__file__).resolve().parent
    gdn_path = package / "ops/gdn.py"
    runner_path = package / "worker/model_runner_v1.py"
    gdnhash,runnerhash=file_digest(gdn_path),file_digest(runner_path)
    require(gdnhash==GDN_SHA and runnerhash==RUNNER_SHA, "frozen runtime hash mismatch")
    # enable_custom_op() itself needs SoC discovery on this frozen stack.
    # Do not load it without a device or replace the real schema with a mock.
    return dict(status="pass",scope="NO-NPU-platform-registration-source-only",
                inventory=inventory,allowed_plugins=os.environ["VLLM_PLUGINS"],
                current_platform=type(current_platform).__name__,device_type=current_platform.device_type,
                gdn_sha256=gdnhash,runner_sha256=runnerhash,
                recurrent_schema="deferred_to_mapped_live_import_and_canary",
                not_proven=["native_library_load", "operator_ABI", "NPU_dispatch"])


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(inspect_platform(),sort_keys=True))


if __name__=="__main__":
    main()
