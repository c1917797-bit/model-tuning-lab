"""After-release same-image independent SKVQ attention oracle; no Torch/device."""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import contract as C
import reference as O
def qualified_numpy(whole):
    plan=C.obj(whole["input_plan_ref"]);cal=C.obj(plan["calibration_whole_ref"])
    independent=C.obj(cal["independent_ref"]);producer=C.obj(independent["producer_ref"])
    library=C.obj(producer["actual_library_probe_ref"]);expected=library["actual_modules"]["numpy"]
    import numpy as np
    C.need(C.ref(np.__file__)==expected,"actual same-image NumPy bytes qualified from actual calibration")
    return np,expected
def case(item,actual,np):
    kind=item["axes"]["K"]["original_dtype"].removeprefix("torch.")
    a,b=item["query_byte_slice"];query=O.values(C.read(item["query_full_ref"])[a:b],kind)
    C.need(len(query)==1536 and item["query_token_offset"]==4095,"full captured last causal query")
    q=[query[i*256:(i+1)*256]for i in range(6)];decoded={}
    for axis in("K","V"):
        x=item["axes"][axis];w=C.obj(item["writer_axes"][axis]);planes=w["after"]
        decoded[axis]=O.decode_numpy(C.read(planes["payload"]),C.read(planes["scales"]),
          C.read(planes["zero_points"]),C.read(x["input_ref"]),x["layout"],item["bits"],kind,4096,np)
    expected=O.attention_numpy(q,decoded["K"],decoded["V"],kind,np)
    result={name:O.compare(C.read(actual[name]),expected[name],kind)for name in("output","scores","probabilities")}
    heads=[]
    for h in range(6):
        raw=C.read(actual["output"])[h*512:(h+1)*512]
        heads.append(O.compare(raw,expected["output"][h*512:(h+1)*512],kind))
    return dict(metrics=result,output_heads=heads,actual_elements=1536,all6_heads_independently_checked=True)
def consume(producer_ref,sha):
    source=C.source(sha);producer=C.obj(producer_ref);whole=C.writer_whole(producer["writer_whole_ref"])
    C.need(producer["schema"]=="skvq.compiled-reader.producer/v1"and
      producer["status"]=="ALL64_Q2Q4_COMPILED_READER_RAW_PENDING_INDEPENDENT"and
      producer["source_ref"]==source and producer["primary"]is None and producer["npu_executed"]is True and
      producer["actual_cases"]==128 and producer["actual_kernel_calls"]==384 and producer["actual_context"]==4096 and
      producer["physical_card"]==4 and producer["logical_device"]==0 and
      producer["identity"]==producer["identity_at_terminal"]and all(producer[k]is False for k in C.scopes()),
      "actual compiled source/full terminal scope; not another paper's PASS")
    C.proof(C.obj(producer["proof_ref"]),source,producer["writer_whole_ref"])
    items=C.input_rows(whole);C.need(len(producer["cases"])==128,"all actual cases complete")
    np,nref=qualified_numpy(whole);checked=[];root=Path(producer_ref["path"]).parent
    for item,row in zip(items,producer["cases"]):
        value=C.obj(row);directory=root/("r%d-l%s-q%d"%(item["rank"],item["logical_layer"].split(".")[2],item["bits"]))
        C.need(Path(row["path"])==directory/"CASE.json"and value["input"]==item and
          (value["rank"],value["logical_layer"],value["bits"])==(item["rank"],item["logical_layer"],item["bits"])and
          value["pool_before_sha256"]==value["pool_after_sha256"]and value["query_unchanged"]is True and
          value["controls_unchanged"]is True and value["identity"]==producer["identity"]and value["actual_calls"]==3,
          "all complete same-input read-only raw case, identities and no duplicate")
        C.need(set(value["actual"])=={"output","scores","probabilities"},"all three real stage outputs")
        for name,ref in value["actual"].items():
            C.need(Path(ref["path"])==directory/(name+".bin")and
              ref["bytes"]==(3072 if name=="output"else 4096*12),"exact complete output shape/path/byte domain")
        result=case(item,value["actual"],np)
        checked.append(dict(rank=item["rank"],logical_layer=item["logical_layer"],bits=item["bits"],case_ref=row,**result))
    C.need(C.ref(producer_ref["path"])==producer_ref and len(checked)==128,"unchanged all128 original terminal")
    return dict(schema="skvq.compiled-reader.independent/v1",status="ALL64_Q2Q4_COMPILED_ATTENTION_CONSUMED",
      source_ref=source,producer_ref=producer_ref,writer_whole_ref=producer["writer_whole_ref"],
      actual_numpy_ref=nref,checked=checked,actual_cases=128,actual_output_elements=128*1536,
      threshold_relative_rms=.005,source_qualified_output_vs_independent_original_equations=True,
      actual_scope="same real calibration tensors last causal query at4096; no model/lifecycle/graph/full176 authority",
      whole_original_ownership_cleanup_consumer_pending=True,**C.scopes())
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--producer-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**C.scopes())));return
    C.need("torch"not in sys.modules and"torch_npu"not in sys.modules and not list(Path("/dev").glob("davinci*"))and
      not any(Path("/dev",x).exists()for x in("devmm_svm","hisi_hdc")),"actual independent Devices[] CPU")
    C.need(a.producer_ref_json and a.output,"real producer/new sink")
    print(json.dumps(C.atomic(a.output,consume(json.loads(Path(a.producer_ref_json).read_bytes()),
      a.source_manifest_sha256)),sort_keys=True))
if __name__=="__main__":main()
