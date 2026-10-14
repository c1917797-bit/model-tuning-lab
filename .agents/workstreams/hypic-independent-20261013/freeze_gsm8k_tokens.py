"""CPU-only fullGSM8K natural-task safety inputs, not PIC activation evidence."""
import argparse,hashlib,json,os
from pathlib import Path
from independent_quality_ruler import load_ruler,EXPECTED
from independent_quality_inputs import quality_generation
DATA_SHA="3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14"
def freeze(data,ruler,model,root):
    from transformers import AutoTokenizer
    raw=data.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=DATA_SHA:raise ValueError("GSM dataset drift")
    samples=[json.loads(line) for line in raw.splitlines() if line.strip()]
    if len(samples)!=1319:raise ValueError("full1319 denominator required")
    functions=load_ruler(ruler)
    tokenizer=AutoTokenizer.from_pretrained(str(model),local_files_only=True,trust_remote_code=False)
    rows=[]
    for i,sample in enumerate(samples):
        prompt,reference=functions["build_case"]("gsm8k",sample)
        rendered=tokenizer.apply_chat_template([{"role":"user","content":prompt}],tokenize=False,
            add_generation_prompt=True,enable_thinking=False)
        ids=tokenizer(rendered,add_special_tokens=False)["input_ids"]
        if len(ids)+1024>40960:raise ValueError("GSM service capacity exceeded")
        rows.append({"index":i,"sample_id":hashlib.sha256(json.dumps(sample,sort_keys=True).encode()).hexdigest(),
            "token_ids":ids,"reference":reference,"prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest()})
    payload={"schema":"hypic-gsm8k-safety-inputs/v1","dataset":"gsm8k","requests":rows,
        "repetitions":3,"generation":quality_generation(),"stop":["Question"],
        "scope":"native natural-task safety; no artificial PIC producer or HYPIC hot claim"}
    content=json.dumps(payload,separators=(",",":")).encode()
    receipt={"samples":1319,"scored_per_arm":3957,"dataset_sha256":DATA_SHA,
        "ruler_sha256":EXPECTED,"tokenizer_sha256":hashlib.sha256((model/"tokenizer.json").read_bytes()).hexdigest(),
        "inputs_sha256":hashlib.sha256(content).hexdigest(),"max_prompt_tokens":max(len(x["token_ids"]) for x in rows),
        "scope":payload["scope"]}
    root.mkdir(parents=True,exist_ok=False)
    with (root/"inputs.json").open("xb") as stream:
        stream.write(content);stream.flush();os.fsync(stream.fileno())
    with (root/"receipt.json").open("x") as stream:
        json.dump(receipt,stream);stream.flush();os.fsync(stream.fileno())
    print(json.dumps(receipt),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("data","ruler","model","root"):p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args();freeze(a.data,a.ruler,a.model,a.root)
