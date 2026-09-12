"""Read-only raw ChatML audit; no template application or model import."""
import argparse
import hashlib
import json
import re
from pathlib import Path

MARKER = re.compile(r"<\|im_start\|>|<\|im_end\|>")
ROLE = re.compile(r"^(system|user|assistant|tool)")


def inspect_prompt(prompt):
    if not isinstance(prompt, str):
        raise ValueError("question must be a string")
    markers = list(MARKER.finditer(prompt))
    counts = dict(messages=0, missing_role_newline=0, unknown_role=0,
                  unclosed_message=0, orphan_end=0, empty_closed_assistant=0,
                  generation_stub=0, generation_stub_without_newline=0)
    pending = None
    for marker in markers:
        if marker.group() == "<|im_start|>":
            if pending is not None:
                counts["unclosed_message"] += 1
            pending = marker.end()
            continue
        if pending is None:
            counts["orphan_end"] += 1
            continue
        body = prompt[pending:marker.start()]
        counts["messages"] += 1
        role = ROLE.match(body)
        if role is None:
            counts["unknown_role"] += 1
        else:
            content = body[role.end():]
            counts["missing_role_newline"] += not content.startswith("\n")
            counts["empty_closed_assistant"] += (
                role.group() == "assistant" and not content.strip())
        pending = None
    if pending is not None:
        suffix = prompt[pending:]
        if suffix in ("assistant", "assistant\n"):
            counts["generation_stub"] = 1
            counts["generation_stub_without_newline"] = suffix == "assistant"
        else:
            counts["unclosed_message"] += 1
    return counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args()
    data = args.dataset.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != args.expected_sha256:
        raise ValueError("dataset identity mismatch")
    rows = []
    for index, line in enumerate(data.decode("utf-8").splitlines()):
        record = json.loads(line)
        prompt = record["question"]
        rows.append(dict(index=index,
                         prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                         **inspect_prompt(prompt)))
    if not rows:
        raise ValueError("empty dataset")
    keys = inspect_prompt("").keys()
    print(json.dumps(dict(
        schema="raw-chatml-format-audit-v1", dataset_sha256=digest,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        count=len(rows),
        totals={key: sum(row[key] for row in rows) for key in keys},
        affected_rows={key: sum(bool(row[key]) for row in rows) for key in keys},
        boundary="Format observations only; not causal diagnosis or task accuracy. "
                 "No input modification, template application, or NPU inference.",
        rows=rows), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
