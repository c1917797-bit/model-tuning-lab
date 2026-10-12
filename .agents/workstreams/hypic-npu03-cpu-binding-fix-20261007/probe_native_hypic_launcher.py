#!/usr/bin/env python3
"""Exercise the prospective native launcher, CPU only, in a disposable image."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import glob

assert not glob.glob("/dev/davinci*")
source = Path("/source-hypic")
target = Path("/tmp/hypic")
venv = Path("/tmp/venv")
assert not target.exists() and not venv.exists()
shutil.copytree(source, target)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PIP_NO_INDEX="1",
           PIP_DISABLE_PIP_VERSION_CHECK="1", TMPDIR="/tmp")
env.pop("PYTHONPATH", None)
env.pop("VLLM_ASCEND_HYPIC_ENABLE", None)
def command(args, run_env=None):
    return subprocess.run(args, cwd="/tmp", env=run_env or env, text=True,
                          capture_output=True, timeout=60)
def checked(args):
    p = command(args)
    assert p.returncode == 0, (p.stdout[-2000:], p.stderr[-2000:])
checked([sys.executable, "-B", "-m", "venv", "--system-site-packages", str(venv)])
python = str(venv / "bin/python")
env["PATH"] = str(venv / "bin") + os.pathsep + env["PATH"]
checked([python, "-B", "-m", "pip", "install", "--no-deps",
         "--no-build-isolation", "--no-index", "-e", str(target)])
launcher = ["bash", str(target / "run_with_native_plugin.sh")]
probe = [python, "-B", "-c",
         "import os;print('DISPATCHED='+os.environ['VLLM_ASCEND_HYPIC_ENABLE'])"]
controls = []
for value in [None, "0", "1"]:
    child_env = env.copy()
    if value is not None:
        child_env["VLLM_ASCEND_HYPIC_ENABLE"] = value
    p = command(launcher + probe, child_env)
    assert p.returncode == 0 and p.stdout.strip() == "DISPATCHED=" + (value or "0"), p.stderr
    controls.append({"switch":value, "forwarded":value or "0"})
invalid_env = dict(env, VLLM_ASCEND_HYPIC_ENABLE="invalid")
invalid = command(launcher + probe, invalid_env)
assert invalid.returncode == 78 and "DISPATCHED=" not in invalid.stdout
no_args = command(launcher)
assert no_args.returncode == 64
manifest_path = target / "MANIFEST.json"
original = manifest_path.read_bytes()
manifest = json.loads(original)
manifest["source_files"][0]["sha256"] = "0" * 64
manifest_path.write_text(json.dumps(manifest))
drift = command(launcher + probe)
assert drift.returncode != 0 and "DISPATCHED=" not in drift.stdout
assert "source inventory/hash mismatch" in drift.stderr
manifest_path.write_bytes(original)
checked([python, "-B", "-m", "pip", "uninstall", "-y", "hypic-vllm-ascend-plugin"])
removed = command(launcher + probe)
assert removed.returncode != 0 and "DISPATCHED=" not in removed.stdout
print(json.dumps({"schema":"hypic-native-launcher-cpu/v1",
                  "manifest_sha256":hashlib.sha256(original).hexdigest(),
                  "controls":controls,"invalid_switch_exit":invalid.returncode,
                  "no_command_exit":no_args.returncode,
                  "source_drift_rejected_before_dispatch":True,
                  "uninstalled_package_rejected_before_dispatch":True,
                  "enabled_value_only_forwarded_to_harmless_command":True,
                  "enabled_hook_tested":False,"real_request_tested":False,
                  "npu_rollback_tested":False,"device_nodes":[]},sort_keys=True))
