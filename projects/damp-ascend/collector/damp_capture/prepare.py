"""CPU-only manifest creation. No downloading or model execution."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from .contract import INPUT_ROOT, MODEL, base_manifest, canonical, file_digest, require, token_digest, validate_manifest


def write_exclusive(path, value):
    path = Path(path).resolve()
    require(path.is_relative_to(Path(INPUT_ROOT)), "inputs must remain outside Git in approved data root")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical(value) + b"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["smoke", "full"], required=True)
    parser.add_argument("--input", required=True, help="smoke text JSONL or full prepared 36-row JSON")
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=2)
    args = parser.parse_args()
    m = base_manifest(args.mode)
    m["prompt_builder_sha256"] = file_digest(__file__)
    if args.mode == "smoke":
        require(1 <= args.limit <= 12, "smoke limit 1..12")
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=False, local_files_only=True)
        source = Path(args.input)
        records = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
        require(len(records) >= args.limit, "not enough smoke text rows")
        m["rows"] = []
        for i, record in enumerate(records[:args.limit]):
            text = record["text"]
            ids = tokenizer.apply_chat_template([{"role": "user", "content": text}],
                                                tokenize=True, add_generation_prompt=True,
                                                enable_thinking=False)
            m["rows"].append(dict(id=f"smoke-{i:02d}", input_ids=ids,
                                  input_ids_sha256=token_digest(ids),
                                  prompt_text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                                  source=dict(path=str(source.resolve()), artifact_sha256=file_digest(source)),
                                  split="smoke", domain="project-smoke"))
        m["prompt_construction"] = "native chat template, enable_thinking=False; no padding/truncation"
    else:
        # Full rows must already contain audited source records and precisely 1024 IDs.
        # No synthetic extension or hidden substitution when official training data are absent.
        prepared = json.loads(Path(args.input).read_text())
        require(prepared.get("prompt_construction") and prepared.get("prompt_builder_sha256"),
                "full preprocessor provenance required")
        m["rows"] = prepared["rows"]
        m["prompt_builder_sha256"] = prepared["prompt_builder_sha256"]
        m["prompt_construction"] = prepared["prompt_construction"]
    validate_manifest(m)
    write_exclusive(args.output, m)
    print(json.dumps(dict(manifest=str(Path(args.output).resolve()), rows=len(m["rows"]),
                          mode=args.mode, source_scope=m["provenance"]), sort_keys=True))


if __name__ == "__main__":
    main()
