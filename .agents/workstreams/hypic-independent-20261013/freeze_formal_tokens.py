"""CPU-only tokenizer artifact builder for the independent matched workload."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from independent_formal_layout import formal_layout, assemble_formal_prompts

def digest(data):
    return hashlib.sha256(json.dumps(data,separators=(",",":")).encode()).hexdigest()

def stream(tokenizer,label,length):
    base=tokenizer.encode(label+". Independently generated deterministic benchmark text.\n",
                          add_special_tokens=False).ids
    if not base:raise ValueError("empty tokenizer stream")
    return (base*((length+len(base)-1)//len(base)))[:length]

def freeze(tokenizer_path,root):
    from tokenizers import Tokenizer
    tokenizer=Tokenizer.from_file(str(tokenizer_path))
    native=stream(tokenizer,"Shared native prefix A",8192)
    public=stream(tokenizer,"Shared position independent segment B",16384)
    parts=[]
    for i in range(40):
        x=formal_layout(i)
        parts.append((stream(tokenizer,"Private bridge "+str(i),x.bridge),
                      stream(tokenizer,"Private tail "+str(i),x.tail)))
    prompts=assemble_formal_prompts(native,public,parts)
    payload={"native_prefix":native,"public_segment":public,
             "requests":[dict(p,token_ids=list(p["token_ids"])) for p in prompts]}
    receipt={"schema":"independent-formal-tokens/v1","requests":40,
             "input_tokens":32768,"native_prefix_tokens":8192,"pic_tokens":16384,
             "tokenizer_sha256":hashlib.sha256(tokenizer_path.read_bytes()).hexdigest(),
             "builder_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             "payload_digest":digest(payload),"output_tokens":1024,
             "concurrency":16,"same_input_all_groups":True,
             "scope":"CPU token artifact only; warmup/service/quality not executed"}
    root.mkdir(parents=True,exist_ok=False)
    for name,data in (("tokens.json",payload),("receipt.json",receipt)):
        with (root/name).open("x") as f:
            json.dump(data,f,separators=(",",":"));f.flush();os.fsync(f.fileno())
    print(json.dumps(receipt),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--tokenizer",type=Path,required=True)
    p.add_argument("--root",type=Path,required=True);a=p.parse_args()
    freeze(a.tokenizer,a.root)
