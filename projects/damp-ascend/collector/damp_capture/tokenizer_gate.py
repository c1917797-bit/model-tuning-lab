"""Same-image, no-device CPU tokenizer gate; load no model weights."""
from __future__ import annotations
import argparse
import glob
import inspect
import json
import os
from pathlib import Path
from .contract import MODEL, MODEL_HASHES, file_digest, require, token_digest


def inspect_tokenizer(source):
    require(os.environ.get("DAMP_NO_DEVICE_TOKENIZER_GATE") == "1" and
            os.environ.get("ASCEND_RT_VISIBLE_DEVICES", "") == "" and
            not glob.glob("/dev/davinci[0-9]*"), "tokenizer diagnostic must have NO NPU devices")
    for name,sha in MODEL_HASHES.items():
        require(file_digest(Path(MODEL)/name) == sha, "model/tokenizer fingerprint changed")
    import transformers
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(MODEL,trust_remote_code=False,local_files_only=True)
    rows=[json.loads(line) for line in Path(source).read_text().splitlines() if line.strip()][:2]
    require(len(rows)==2, "need two actual smoke texts")
    output=[]
    for row in rows:
        messages=[{"role":"user","content":row["text"]}]
        default=tokenizer.apply_chat_template(messages,tokenize=True,
                                              add_generation_prompt=True,enable_thinking=False)
        ids=tokenizer.apply_chat_template(messages,tokenize=True,return_dict=False,
                                         add_generation_prompt=True,enable_thinking=False)
        require(isinstance(ids,list) and all(type(x) is int for x in ids),
                "explicit return_dict=False did not return actual list[int]")
        # Repeat CPU tokenization; no coercion from mapping/tensor and no handwritten IDs.
        again=tokenizer.apply_chat_template(messages,tokenize=True,return_dict=False,
                                           add_generation_prompt=True,enable_thinking=False)
        require(ids==again, "tokenizer not deterministic")
        output.append(dict(default_return_type=type(default).__name__,
                           explicit_return_type=type(ids).__name__,input_tokens=len(ids),
                           input_ids_sha256=token_digest(ids)))
    return dict(status="pass",scope="same-image-no-device-real-tokenizer-only",
                transformers_version=transformers.__version__,
                apply_chat_template_signature=str(inspect.signature(tokenizer.apply_chat_template)),
                source_sha256=file_digest(source),rows=output)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",required=True)
    a=p.parse_args()
    print(json.dumps(inspect_tokenizer(a.input),sort_keys=True))


if __name__=="__main__":
    main()
