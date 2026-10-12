"""Pinned-image CPU-only package registration and uninstall probe."""
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import tempfile

package = Path(__file__).resolve().parent/"state-observer-package-v2"
sys.path.insert(0, str(package))
with tempfile.TemporaryDirectory() as temp:
    cfg = Path(temp)/"config.json"
    cfg.write_text(json.dumps(dict(raw_root=str(Path(temp)/"capture"),
        request_id="probe", kv_layer="kv", gdn_layer="gdn")))
    os.environ["HYPIC_STATE_OBSERVER_ENABLE"] = "1"
    os.environ["HYPIC_STATE_CAPTURE_CONFIG"] = str(cfg)
    import hypic_diagnostic_patch as patch
    handle = patch.activate()
    ep = next(x for x in importlib.metadata.entry_points(group="vllm.general_plugins")
              if x.name == "hypic_vllm_ascend")
    func = ep.load()
    assert handle.adapter is not None and func is handle.adapter.replacement
    module = sys.modules["hypic_vllm_ascend"]
    original = handle.adapter.original
    func()
    assert handle.adapter.observer is not None
    patch.deactivate()
    assert module.register is original and handle not in sys.meta_path
    assert not (Path(temp)/"capture").exists()
    print(json.dumps(dict(package_registration=True, observer_installed=True,
        rollback=True, source=module.__file__, version=module.__version__,
        register_called=True, devices_used=False)),flush=True)
