"""CPU-only full127 input builder; no requests or model weights loaded."""
import argparse,hashlib,json,os
from pathlib import Path
from independent_quality_ruler import load_ruler,EXPECTED
from independent_quality_inputs import context_segment,quality_generation,unique_public_segments
DATA_SHA="cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a"

def freeze(data_path,ruler_path,model_path,root):
    from transformers import AutoTokenizer
    raw=data_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=DATA_SHA:raise ValueError("dataset drift")
    samples=json.loads(raw)
    if len(samples)!=127:raise ValueError("full127 denominator required")
    ruler=load_ruler(ruler_path)
    tokenizer=AutoTokenizer.from_pretrained(str(model_path),local_files_only=True,trust_remote_code=False)
    rows=[];segments=[];seen=set()
    for i,sample in enumerate(samples):
        sid=sample["_id"]
        if sid in seen:raise ValueError("duplicate sample identity")
        seen.add(sid)
        prompt,reference=ruler["build_case"]("longbenchv2",sample)
        rendered=tokenizer.apply_chat_template([{"role":"user","content":prompt}],
            tokenize=False,add_generation_prompt=True,enable_thinking=False)
        # Locate the frozen template's exact context insertion, not an answer.
        marker="Please read the following text and answer the questions below.\n <text> \n "
        begin=rendered.find(marker)
        if begin<0:raise ValueError("chat template lost prompt")
        start=begin+len(marker);end=start+len(sample["context"])
        if rendered[start:end]!=sample["context"]:raise ValueError("context span drift")
        encoded=tokenizer(rendered,add_special_tokens=False,return_offsets_mapping=True)
        ids=encoded["input_ids"]
        if len(ids)+1024>41984:raise ValueError("full prompt exceeds frozen capacity")
        selected,segment=context_segment(ids,encoded["offset_mapping"],start,end)
        rows.append({"index":i,"sample_id":sid,"token_ids":ids,
            "prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),
            "rendered_sha256":hashlib.sha256(rendered.encode()).hexdigest(),
            "reference":reference,"segment":selected})
        segments.append(list(segment))
    payload={"schema":"hypic-quality-inputs/v1","dataset":"longbenchv2",
        "generation":quality_generation(),"repetitions":3,"requests":rows}
    catalog={"schema":"hypic-public-catalog/v1","public_segments":unique_public_segments(segments)}
    files={"inputs.json":payload,"catalog.json":catalog}
    receipt={"schema":"hypic-quality-input-freeze/v1","samples":127,
        "dataset_sha256":DATA_SHA,"ruler_sha256":EXPECTED,
        "tokenizer_sha256":hashlib.sha256((model_path/"tokenizer.json").read_bytes()).hexdigest(),
        "chat_template_sha256":hashlib.sha256(str(tokenizer.chat_template).encode()).hexdigest(),
        "builder_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "max_prompt_tokens":max(len(x["token_ids"]) for x in rows),"files":{},
        "scope":"CPU inputs only; independent replay/segment ambiguity audit and all NPU gates pending"}
    root.mkdir(parents=True,exist_ok=False)
    for name,obj in files.items():
        content=json.dumps(obj,separators=(",",":")).encode()
        with (root/name).open("xb") as stream:
            stream.write(content);stream.flush();os.fsync(stream.fileno())
        receipt["files"][name]=hashlib.sha256(content).hexdigest()
    with (root/"receipt.json").open("x") as stream:
        json.dump(receipt,stream);stream.flush();os.fsync(stream.fileno())
    print(json.dumps(receipt),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    for name in ("data","ruler","model","root"):parser.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args();freeze(args.data,args.ruler,args.model,args.root)
