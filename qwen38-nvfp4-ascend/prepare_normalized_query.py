"""User-authorized supplement: remove only empty historical assistant turns."""
import argparse, hashlib, json
from pathlib import Path
from chat_benchmark import parse_chatml
from probe_empty_history import drop_empty_assistant

SOURCE_SHA = "a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e"


def transform(obj):
    original = parse_chatml(obj["question"])
    cleaned = drop_empty_assistant(original)
    rendered = "".join("<|im_start|>"+m["role"]+"\n"+m["content"]+"<|im_end|>\n" for m in cleaned)
    rendered += "<|im_start|>assistant\n"
    assert parse_chatml(rendered) == cleaned
    result = dict(obj)
    result["question"] = rendered
    assert {k:v for k,v in result.items() if k!="question"} == {k:v for k,v in obj.items() if k!="question"}
    return result, len(original)-len(cleaned)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    args = p.parse_args()
    raw = args.source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError("Original dataset changed")
    objects = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    if len(objects) != 357:
        raise ValueError("Expected full357 rows")
    rows = [transform(obj) for obj in objects]
    args.output_dir.mkdir(parents=True, exist_ok=False)
    path = args.output_dir/"query_rewrite.normalized.jsonl"
    path.write_text("".join(json.dumps(row,ensure_ascii=False)+"\n" for row,_ in rows))
    doc = dict(scope="authorized normalized supplement; never pool with original",
        source_sha256=SOURCE_SHA, normalized_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        rows=len(rows), changed_rows=sum(n>0 for _,n in rows),
        removed_assistant_messages=sum(n for _,n in rows),
        rule="remove assistant turns whose content.strip() is empty; preserve other semantic messages",
        ordering="same357 indices", requires_fresh_both_models=True)
    (args.output_dir/"manifest.json").write_text(json.dumps(doc,indent=2)+"\n")
    print(json.dumps(doc))


if __name__ == "__main__":
    main()
