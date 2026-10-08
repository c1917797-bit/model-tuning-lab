"""Read-only README audit; no device or service access."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
EXPECTED_SHA256 = "4dffc4b1ee436edb5c782162308ac384ab68b6c45f4d7e2bd995351f9891c880"
readme = ROOT / "README.md"
text = readme.read_text(encoding="utf-8")
digest = hashlib.sha256(readme.read_bytes()).hexdigest()
assert digest == EXPECTED_SHA256, (digest, EXPECTED_SHA256)

links = []
for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
    if re.match(r"^[a-zA-Z][\w+.-]*:", target) or target.startswith("#"):
        continue
    path = target.split("#", 1)[0]
    assert (ROOT / path).exists(), f"Missing README link: {target}"
    links.append(target)

registry = (ROOT / ".agents/skills.registry.yaml").read_text(encoding="utf-8")
registered = set(re.findall(r"^  - id: (\S+)\s*$", registry, flags=re.MULTILINE))
listed_section = text.split("<details>", 1)[1].split("</details>", 1)[0]
listed = re.findall(r"^- `([^`]+)`\s*$", listed_section, flags=re.MULTILINE)
physical = {p.parent.name for p in (ROOT / ".agents/skills").glob("*/SKILL.md")}
assert len(listed) == len(set(listed)) == 29
assert set(listed) == registered == physical, (set(listed) ^ registered, registered ^ physical)

in_fence = False
for index, line in enumerate(text.splitlines()):
    assert line == line.rstrip(), f"Trailing whitespace at line {index + 1}"
    if line.startswith(chr(96) * 3):
        in_fence = not in_fence
        continue
    if not in_fence and re.match(r"^#{1,6} ", line):
        assert text.splitlines()[index + 1] == "", f"Missing heading separation at line {index + 1}"
assert not in_fence, "Unclosed code fence"

task_dir = ROOT / ".agents/workstreams/readme-refresh-20261008"
for path in task_dir.glob("*.json"):
    json.loads(path.read_text(encoding="utf-8"))
task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
assert task["resource_leases"] == []
assert task["original_base"] == "f1f37a39bd86f7db5fd3ee3dea358ae6868275c6"
for path, expected in task["constraining_sha256"].items():
    frozen = subprocess.check_output(["git", "show", f'{task["original_base"]}:{path}'], cwd=ROOT)
    assert hashlib.sha256(frozen).hexdigest() == expected, path
changed = subprocess.check_output(
    ["git", "diff", "--name-only", task["original_base"]], cwd=ROOT, text=True
).splitlines()
untracked = subprocess.check_output(
    ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True
).splitlines()
for path in changed + untracked:
    assert path in {"README.md", ".agents/HANDOFF.md"} or path.startswith(
        ".agents/workstreams/readme-refresh-20261008/"
    ), f"Out-of-scope change: {path}"
print(json.dumps({"result": "PASS", "readme_sha256": digest, "relative_links": len(links),
                  "registered_skills": len(registered), "json_state": "PASS",
                  "formatting": "PASS", "original_base_and_frozen_hashes": "PASS",
                  "device_access": False, "change_scope": "PASS"}, sort_keys=True))
