#!/usr/bin/env bash
# Native HYPIC delivery launcher; registration remains owned by vLLM.
set -euo pipefail
if [ "$#" -eq 0 ]; then
    printf '%s\n' 'A service command is required.' >&2
    exit 64
fi
export VLLM_ASCEND_HYPIC_ENABLE="${VLLM_ASCEND_HYPIC_ENABLE:-0}"
case "$VLLM_ASCEND_HYPIC_ENABLE" in
    0|1) ;;
    *) printf '%s\n' 'HYPIC enable switch must be 0 or 1.' >&2; exit 78 ;;
esac
package_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 -B - "$package_root" <<'PY'
import hashlib
import importlib.metadata as metadata
import importlib.util
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
manifest = json.loads((root / "MANIFEST.json").read_text())
distribution = metadata.distribution("hypic-vllm-ascend-plugin")
entries = [e for e in distribution.entry_points
           if e.group == "vllm.general_plugins" and e.name == "hypic_vllm_ascend"]
if len(entries) != 1 or entries[0].value != "hypic_vllm_ascend:register":
    raise SystemExit("Native HYPIC entrypoint mismatch")
spec = importlib.util.find_spec("hypic_vllm_ascend")
if not spec or not spec.origin or Path(spec.origin).resolve() != root / "hypic_vllm_ascend/__init__.py":
    raise SystemExit("Installed HYPIC does not resolve to this package")
expected = {item["path"]: item["sha256"] for item in manifest["source_files"]}
files = sorted((root / "hypic_vllm_ascend").rglob("*.py"))
actual = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in files if not p.is_symlink()}
if len(expected) != len(manifest["source_files"]) or actual != expected:
    raise SystemExit("Installed HYPIC source inventory/hash mismatch")
if any(p.is_symlink() for p in (root / "hypic_vllm_ascend").rglob("*")):
    raise SystemExit("HYPIC source symlink is not allowed")
if distribution.version != "0.8.5":
    raise SystemExit("HYPIC distribution version mismatch")
PY
exec "$@"
