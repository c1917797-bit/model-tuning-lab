#!/usr/bin/env python3
"""CPU-only native installation/disabled-entrypoint/uninstall probe.

Run only in the pinned disposable container with no device/network mappings.
This does not exercise enabled hooks, serving, numerical quality or NPU rollback.
"""
import glob
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

EXPECTED_TREE = "a5ebed77cc4ae0035e2634b81dc0606d8e37cc9d32f8894b984325bec1056692"
NAME = "hypic-vllm-ascend-plugin"
SOURCE = Path("/source-hypic")
TARGET = Path("/tmp/hypic")
VENV = Path("/tmp/hypic-venv")
devices = glob.glob("/dev/davinci*")
assert not devices, devices
assert not TARGET.exists() and not VENV.exists(), "nonempty probe paths"
try:
    metadata.distribution(NAME)
except metadata.PackageNotFoundError:
    pass
else:
    raise AssertionError("baseline image already installs HYPIC")

def tree(root):
    h = hashlib.sha256()
    files = sorted((root / "hypic_vllm_ascend").rglob("*.py"))
    assert len(files) == 32
    for path in files:
        assert not path.is_symlink()
        h.update(path.relative_to(root / "hypic_vllm_ascend").as_posix().encode() + b"\0")
        h.update(path.read_bytes() + b"\0")
    return h.hexdigest()

assert tree(SOURCE) == EXPECTED_TREE, "source tree mismatch"
shutil.copytree(SOURCE, TARGET, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
assert tree(TARGET) == EXPECTED_TREE, "copied tree mismatch"
env = dict(os.environ, PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1",
           PYTHONDONTWRITEBYTECODE="1", TMPDIR="/tmp")
env.pop("PYTHONPATH", None)
env.pop("VLLM_ASCEND_HYPIC_ENABLE", None)

def run(args, child_env=None):
    p = subprocess.run(args, cwd="/tmp", env=child_env or env, text=True,
                       capture_output=True, timeout=60)
    assert p.returncode == 0, (args, p.returncode, p.stdout[-2000:], p.stderr[-2000:])
    return p

run([sys.executable, "-B", "-m", "venv", "--system-site-packages", str(VENV)])
python = str(VENV / "bin/python")
installed = run([python, "-B", "-m", "pip", "install", "--no-deps",
                 "--no-build-isolation", "--no-index", "-e", str(TARGET)])
child = """
import importlib.metadata as m,json,sys
from pathlib import Path
d=m.distribution("hypic-vllm-ascend-plugin")
eps=[e for e in d.entry_points if e.group=="vllm.general_plugins" and e.name=="hypic_vllm_ascend"]
assert len(eps)==1 and eps[0].value=="hypic_vllm_ascend:register"
entry=eps[0].load()
entry()
import hypic_vllm_ascend as plugin
assert Path(plugin.__file__).resolve()==Path("/tmp/hypic/hypic_vllm_ascend/__init__.py")
assert "hypic_vllm_ascend.patches.bootstrap" not in sys.modules
assert "torch_npu" not in sys.modules and "vllm" not in sys.modules
print(json.dumps({"version":d.version,"entrypoint":eps[0].value,"module":plugin.__file__,
                  "bootstrap_imported":False,"device_framework_imported":False}))
"""
controls = []
for value in [None, "0"]:
    child_env = env.copy()
    if value is not None:
        child_env["VLLM_ASCEND_HYPIC_ENABLE"] = value
    p = run([python, "-B", "-c", child], child_env)
    assert "plugin_build_active" not in p.stdout + p.stderr
    controls.append({"switch": value, "result": json.loads(p.stdout)})
run([python, "-B", "-m", "pip", "uninstall", "-y", NAME])
removed = run([python, "-B", "-c", """
import importlib.metadata as m,importlib.util,json
try: m.distribution("hypic-vllm-ascend-plugin")
except m.PackageNotFoundError: pass
else: raise AssertionError("distribution remains")
assert importlib.util.find_spec("hypic_vllm_ascend") is None
assert not [e for e in m.entry_points(group="vllm.general_plugins") if e.name=="hypic_vllm_ascend"]
print(json.dumps({"distribution_absent":True,"import_absent":True,"entrypoint_absent":True}))
"""])
assert tree(SOURCE) == EXPECTED_TREE and tree(TARGET) == EXPECTED_TREE
print(json.dumps({"schema":"hypic-native-cpu-lifecycle/v1","python_tree_sha256":EXPECTED_TREE,
                  "source_files":32,"device_nodes":devices,"controls":controls,
                  "after_uninstall_new_interpreter":json.loads(removed.stdout),
                  "enabled_hook_tested":False,"serving_request_tested":False,
                  "npu_rollback_tested":False},sort_keys=True))
