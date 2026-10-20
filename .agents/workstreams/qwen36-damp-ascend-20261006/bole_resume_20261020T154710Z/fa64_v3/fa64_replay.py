"""BOLE repair12 all-rank FA replay. Original pointwise gate stays unchanged."""
import argparse, hashlib, json, os, time, traceback
from pathlib import Path

def ref(p):
    p=Path(p); h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(8*1024*1024),b""): h.update(block)
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())

def checked(r):
    p=Path(r["path"])
    if ref(p)!=r: raise ValueError("input identity mismatch "+str(p))
    return p

def write(p,v):
    p=Path(p)
    with p.open("x") as f: json.dump(v,f,sort_keys=True,allow_nan=False); f.write("\n")
    return ref(p)

def bits(t,a,b):
    return a.shape==b.shape and a.dtype==b.dtype and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8))

def gate(t,output,truth):
    error=(output.double()-truth.double()).abs()
    bound=.001+.01*truth.double().abs()
    return dict(pointwise_pass=bool(t.isfinite(output).all() and (error<=bound).all()),
                failed_elements=int((error>bound).sum()),peak_abs=float(error.max()),
                worst_bound_ratio=float((error/bound).max()))

def reference(t,inputs,dtype):
    q=inputs["query"].squeeze(0).permute(1,0,2).to(dtype)
    k=inputs["key"].permute(0,2,1,3).reshape(-1,256).to(dtype)
    v=inputs["value"].permute(0,2,1,3).reshape(-1,256).to(dtype)
    mask=inputs["atten_mask"][0,0]
    rows=[]
    for node in range(3):
        logits=q[node]@k[~mask[node]].T*(256**-.5)
        weights=(logits-logits.max(-1,keepdim=True).values).exp()
        weights=weights/weights.sum(-1,keepdim=True)
        rows.append(weights@v[~mask[node]])
    return t.stack(rows)

def extract(a,t):
    assert not list(Path("/dev").glob("davinci[0-9]*"))
    inputs=json.loads(checked(json.loads(a.inputs_ref)).read_text())
    frames=[]
    for rank,pair in enumerate(inputs["raw_ranks"]):
        receipt=json.loads(checked(pair["receipt"]).read_text())
        assert receipt["raw"]==pair["raw"] and receipt["rank"]==rank and receipt["primary"] is None
        exported=t.load(checked(pair["raw"]),map_location="cpu",weights_only=False)
        raw=exported["payload"]
        assert raw["rank"]==rank and raw["scheduler_committed"] is False
        captures=raw["tree_context"]["captures"]
        for layer in range(3,64,4):
            row=captures[layer]
            saved={k:v.clone() for k,v in row["trial"]["native_before"].items()}
            assert row["kind"]=="fa" and saved["query"].shape==(1,6,3,256)
            assert saved["key"].shape==saved["value"].shape==(2,1,128,256)
            assert saved["block_table"].tolist()==[[0,1]]
            assert saved["atten_mask"].shape==(1,1,3,256)
            q=saved["query"].squeeze(0).permute(1,0,2)
            assert bits(t,q,row["query"].reshape(3,6,256))
            expected=t.ones((3,256),dtype=t.bool)
            expected[:,:132]=False; expected[1,132]=False; expected[2,133]=False
            assert bits(t,expected,saved["atten_mask"][0,0])
            cast_rows={}
            for key in ("query","key","value"):
                assert saved[key].dtype==t.bfloat16 and bool(t.isfinite(saved[key]).all())
                converted=saved[key].to(t.float16)
                assert bool(t.isfinite(converted).all()), "nonfinite FP16 input conversion"
                delta=(converted.double()-saved[key].double()).abs()
                cast_rows[key]=dict(changed=int((delta!=0).sum()),elements=delta.numel(),peak_abs=float(delta.max()),
                    nonzero_to_zero=int(((saved[key]!=0)&(converted==0)).sum()),lossless=bool((delta==0).all()))
            truth64=reference(t,saved,t.float64);truth32=reference(t,saved,t.float32)
            original=row["output"].clone()
            frames.append(dict(rank=rank,layer=layer,inputs=saved,cast_rows=cast_rows,original_output=original,
                               truth64=truth64,truth32=truth32,
                               original_gate64=gate(t,original,truth64),
                               original_gate32=gate(t,original,truth32)))
        del exported,raw,captures
    assert len(frames)==64 and {(x["rank"],x["layer"]) for x in frames}=={(r,l) for r in range(4) for l in range(3,64,4)}
    out=Path(a.output);out.mkdir(exist_ok=False)
    with (out/"FRAMES.pt").open("xb") as f:t.save(frames,f)
    report=dict(schema="bole.fa64.extract/v1",inputs=json.loads(a.inputs_ref),frames=ref(out/"FRAMES.pt"),
                source=ref(__file__),frame_count=64,all_cast_values_lossless=all(v["lossless"] for x in frames for v in x["cast_rows"].values()),
                changed_input_values=sum(v["changed"] for x in frames for v in x["cast_rows"].values()),
                peak_cast_abs=max(v["peak_abs"] for x in frames for v in x["cast_rows"].values()),
                cast_ledger=[dict(rank=x["rank"],layer=x["layer"],values=x["cast_rows"]) for x in frames],
                original_failed_frames=sum(not x["original_gate64"]["pointwise_pass"] for x in frames),
                NPU=False,model_qualified=False)
    assert report["original_failed_frames"]==23, "original failed-frame set/count must reproduce"
    write(out/"EXTRACT.json",report); print(json.dumps({k:v for k,v in report.items() if k!="cast_ledger"}))

def replay(a,t):
    import torch_npu
    t.npu.set_device("npu:0")
    frames_ref=json.loads(a.frames_ref)
    frames=t.load(checked(frames_ref),map_location="cpu",weights_only=False)
    out=Path(a.output);out.mkdir(exist_ok=False)
    rows=[];start=time.monotonic()
    for frame in frames:
        if time.monotonic()-start>780: raise TimeoutError("bounded FA64 phase")
        record=dict(rank=frame["rank"],layer=frame["layer"],arms={})
        for variant in ("BF16-original","FP16-input-BF16-output"):
            use_half=variant.startswith("FP16")
            cpu={k:(v.to(t.float16) if use_half and k in ("query","key","value") else v.clone()) for k,v in frame["inputs"].items()}
            device={k:v.to("npu:0") for k,v in cpu.items()}
            assert all(bits(t,device[k].cpu(),v) for k,v in cpu.items())
            result=torch_npu.npu_fused_infer_attention_score(**device,input_layout="BNSD",block_size=128,
                actual_seq_lengths=[3],actual_seq_lengths_kv=[134],num_key_value_heads=1,num_heads=6,
                scale=256**-.5,sparse_mode=1,pre_tokens=2147483647,next_tokens=2147483647,inner_precise=2)
            t.npu.synchronize()
            kernel=result[0].cpu()
            assert kernel.shape==(1,6,3,256) and kernel.dtype==(t.float16 if use_half else t.bfloat16)
            actual=kernel.to(t.bfloat16).squeeze(0).permute(1,0,2).contiguous()
            assert all(bits(t,device[k].cpu(),v) for k,v in cpu.items())
            raw=out/("rank%d-layer%d-%s.pt"%(frame["rank"],frame["layer"],variant))
            with raw.open("xb") as f:t.save(dict(output=actual,kernel_output=kernel,frame_ref=frames_ref),f)
            record["arms"][variant]=dict(double=gate(t,actual,frame["truth64"]),
                float=gate(t,actual,frame["truth32"]),raw=ref(raw),
                original_output_bitwise=bits(t,actual,frame["original_output"]))
            del device,result,kernel,actual
        rows.append(record);write(out/("rank%d-layer%d.json"%(frame["rank"],frame["layer"])),record)
    report=dict(schema="bole.fa64.replay/v1",source=ref(__file__),frames=frames_ref,NPU=True,
                rows=rows,frame_count=len(rows),elapsed=time.monotonic()-start,
                original_bitwise_frames=sum(x["arms"]["BF16-original"]["original_output_bitwise"] for x in rows),
                original_failed_frames=sum(not all(x["arms"]["BF16-original"][k]["pointwise_pass"] for k in ("double","float")) for x in rows),
                candidate_failed_frames=sum(not all(x["arms"]["FP16-input-BF16-output"][k]["pointwise_pass"] for k in ("double","float")) for x in rows),
                model_qualified=False,task_qualified=False,performance_qualified=False)
    write(out/"RESULT.json",report); print(json.dumps({k:v for k,v in report.items() if k!="rows"}))

def main():
    p=argparse.ArgumentParser();p.add_argument("phase",choices=["extract","replay"]);p.add_argument("--inputs-ref");p.add_argument("--frames-ref");p.add_argument("--output",required=True)
    a=p.parse_args()
    import torch
    torch.set_num_threads(4);torch.set_num_interop_threads(1)
    try: (extract if a.phase=="extract" else replay)(a,torch)
    except BaseException as e:
        out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
        if not (out/"FAILURE.json").exists():write(out/"FAILURE.json",dict(error=repr(e),traceback=traceback.format_exc(),source=ref(__file__)))
        raise

if __name__=="__main__":main()
