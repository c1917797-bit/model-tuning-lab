#!/usr/bin/env python3
"""Lossless documentation relocation check; not host/NPU behavioral acceptance."""
import json
import subprocess
from pathlib import Path

BASE = "924857d39f7b06ca197322acc460ae2afb01ad86"
SKILL = ".agents/skills/chicaihong01-host-maintenance/SKILL.md"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MOVES = [
    ("Start-of-turn remote orientation", "Host-side Python test environment", "session-orientation.md"),
    ("Host-side Python test environment", "Machine and experiment safety", "host-python-tests.md"),
    ("Machine and experiment safety", "Editing and checkpoints", "machine-experiment-safety.md"),
]
ROUTES = {"session-orientation.md":"## Start-of-turn remote orientation\n\nRead [references/session-orientation.md](references/session-orientation.md)\nat the start of every remote session, before touching claimed files or resources.\n\n","host-python-tests.md":"## Host-side Python test environment\n\nBefore host-side Python tests, read\n[references/host-python-tests.md](references/host-python-tests.md).\nDo not install device packages into the host-test environment.\n\n","machine-experiment-safety.md":"## Machine and experiment safety\n\nBefore inspecting or changing machine/runtime resources, read\n[references/machine-experiment-safety.md](references/machine-experiment-safety.md).\nThis includes container, port, process, NPU, HugeTLB and long-controller work.\nRead its Qwen runtime lesson when that stated runtime condition applies.\n\n"}

def section(text, heading, following):
    start = text.index("## " + heading + "\n")
    end = text.index("## " + following + "\n", start)
    return text[start:end]

def validate(base, core, references, qwen_target_exists=True):
    if len(core.splitlines()) > 120:
        raise ValueError("entrypoint exceeds 120 lines")
    rebuilt = core
    for heading, following, name in MOVES:
        routed = section(core, heading, following)
        if routed != ROUTES[name]:
            raise ValueError("required read routing changed: " + name)
        if name not in references:
            raise ValueError("required reference missing: " + name)
        original = section(base, heading, following)
        expected = original.rstrip() + "\n"
        if name == "machine-experiment-safety.md":
            expected = expected.replace("references/qwen35-v023-runtime-lessons.md",
                                        "qwen35-v023-runtime-lessons.md")
        if references[name] != expected:
            raise ValueError("moved instructions changed: " + name)
        rebuilt = rebuilt.replace(routed, original, 1)
    if rebuilt != base:
        raise ValueError("unmoved instructions changed")
    if not qwen_target_exists:
        raise ValueError("nested Qwen reference missing")
    return {"source_lines": len(base.splitlines()), "entrypoint_lines": len(core.splitlines()),
            "moved_sections_preserved": 3, "device_validation": False,
            "main_integrated": False}

def inputs():
    base = subprocess.check_output(["git", "show", BASE + ":" + SKILL], cwd=REPO, text=True)
    path = REPO / SKILL
    refs = {name: (path.parent / "references" / name).read_text()
            for _, _, name in MOVES if (path.parent / "references" / name).is_file()}
    return base, path.read_text(), refs

if __name__ == "__main__":
    print(json.dumps(validate(*inputs(),
        qwen_target_exists=(REPO / Path(SKILL).parent / "references/qwen35-v023-runtime-lessons.md").is_file()),
        sort_keys=True))
