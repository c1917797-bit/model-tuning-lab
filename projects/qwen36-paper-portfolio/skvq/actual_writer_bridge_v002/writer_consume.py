"""Devices[] independent all64 Q2/Q4 byte oracle; no Torch or candidate writer call.
A successful component is STILL pending whole owned-host original/cleanup consumption.
"""
import argparse,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import writer_contract as C
import writer_byte_oracle as O
def numpy_module(plan):
    cal=C.obj(plan["calibration_whole_ref"]);independent=C.obj(cal["independent_ref"])
    producer=C.obj(independent["producer_ref"]);library=C.obj(producer["actual_library_probe_ref"])
    expected=library["actual_modules"]["numpy"]
    import numpy as np
    C.need(C.ref(np.__file__)==expected,"actual same660 NumPy source from prior library/calibration gate")
    return np,expected
def check_allocations(descriptors,layout,bits,kind):
    """Actual controlled allocations, not a claim about native model shared slabs."""
    stride=C.extent(layout["starts"],bits);regions=[]
    for name,shape,unit,dtype in(("input",[C.TOKENS,C.DIM],2,"torch."+kind),
      ("payload",[C.TOKENS,stride],1,"torch.uint8"),
      ("scales",[C.TOKENS,4],2,"torch."+kind),("zero_points",[C.TOKENS,4],2,"torch."+kind)):
        d=descriptors[name];pointer=d["data_ptr"];capacity=d["storage_nbytes"]
        C.need(d["shape"]==shape and d["stride"]==[shape[1],1]and d["dtype"]==dtype and
          d["device"]=="npu:0"and type(d["storage_offset"])is int and d["storage_offset"]==0 and
          type(pointer)is int and 0<pointer<2**64 and type(capacity)is int and
          shape[0]*shape[1]*unit<=capacity<2**40 and pointer+capacity<2**64,
          "actual contiguous controlled plane extent/type/device/base")
        regions.append((pointer,pointer+capacity))
    C.need(all(a[1]<=b[0]or b[1]<=a[0]for i,a in enumerate(regions)for b in regions[i+1:]),
      "complete original input/compact/SS/ZP storage allocations disjoint")
def check_formats(observed,source):
    fmtrow=next(r for r in C.obj(C.CAPTURE)["files"]if r["path"].endswith("/n1_format.py"))
    F=C.module("_skvq_writer_actual_format",fmtrow);policy=F.policy()
    q=observed["actual_format_qualification"];C.need(q["policy_ref"]==F.POLICY,"same original native format policy")
    policy.validate_chain(q["binding"],C.checked)
    x=q["observation"]
    C.need(x["wrapper_origin"]==x["enum_origin"]and x["wrapper_origin"]["sha256"]==policy.FORMAT_SHA and
      x["wrapper_origin"]["path"]==q["binding"]["runtime_path"]and
      x["wrapper_origin"]["bytes"]==q["binding"]["archive_ref"]["bytes"],"source-qualified actual native getter/enum")
    C.need(set(observed["serialized_formats"])==set(observed["before_descriptors"])=={"input","payload","scales","zero_points"},
      "all actual controlled allocations, not native-cache layout inference")
    for name,value in observed["serialized_formats"].items():
        policy.validate_serial(value);raw=observed["before_descriptors"][name]["original_format"]
        C.need(raw==dict(actual_type=policy.FORMAT_TYPE,repr=value["repr"],enum_member="ND",
          native_value=2,native_value_type="builtins.int"),"actual native enum serialization; no coercion")
def consume(producer_ref,expected):
    source=C.source(expected);result=C.obj(producer_ref)
    C.need(result["schema"]=="skvq.actual-writer.producer/v1"and
      result["status"]=="ACTUAL_ALL64_Q2Q4_WRITER_RETURNED_RAW_PENDING_INDEPENDENT"and
      result["source_ref"]==source and result["primary"]is None and result["physical_card"]==4 and
      result["logical_device"]==0 and result["actual_case_count"]==128 and result["actual_axis_writer_calls"]==256 and
      result["npu_executed"]is True and result["host_owned_semantic_consumer_required"]is True and
      all(result[k]is False for k in C.scopes()),"actual all64 writer terminal, not model/reader/176")
    from writer_inputs import consume_plan
    plan=consume_plan(result["input_plan_ref"],source)
    proof=C.device_proof(C.obj(result["device_proof_ref"]),source,result["input_plan_ref"])
    C.need(result["owned_cid"]==proof["cid"]and result["identity_at_terminal"]==result["identity"],"same actual owned process identity")
    np,numpy_ref=numpy_module(plan)
    from numpy_preflight import self_test
    prior=C.obj(proof["prior_numpy_ref"])
    C.need(prior["actual_numpy_ref"]==numpy_ref and prior["configurations"]==self_test(np),
      "actual independent same-NumPy scalar/vector whole-output replay")
    checked=[];cases=result["cases"]
    want=[(r,l,b)for r in range(4)for l in C.LAYERS for b in(2,4)]
    C.need([(x["rank"],x["logical_layer"],x["bits"])for x in cases]==want,"complete ordered all4/all16/Q2Q4 without duplicates")
    inputs={(x["rank"],x["logical_layer"]):x for x in plan["rows"]}
    root=Path(producer_ref["path"]).parent
    for case in cases:
        r,l,b=case["rank"],case["logical_layer"],case["bits"];selected=inputs[(r,l)]
        C.need(set(case["axes"])=={"K","V"},"actual both writer axes")
        for axis in("K","V"):
            actual_ref=case["axes"][axis];obs=C.obj(actual_ref);s=selected["axes"][axis]
            directory=root/("r%d-l%s-q%d"%(r,l.split(".")[2],b))
            C.need(Path(actual_ref["path"])==directory/(axis+"-RAW_AFTER_WRITER.json")and
              obs["input_ref"]==s["input_ref"]and obs["writer_source"]==C.WRITER and
              obs["tokens"]==C.TOKENS and obs["middle"]==[C.START,C.STOP]and
              obs["identity"]==obs["after_identity"]==result["identity"],"exact selected same original writer/source/domain/identity")
            for timing in("before","after"):
                C.need(set(obs[timing])=={"payload","scales","zero_points"},"all complete raw planes")
                for name,row in obs[timing].items():
                    C.need(Path(row["path"])==directory/(axis+"-"+name+"-"+timing+".bin"),"exact ordinary owned raw plane path")
            C.need(Path(obs["input_after_ref"]["path"])==directory/(axis+"-INPUT_AFTER.bin"),"complete original input-after bytes")
            check_allocations(obs["before_descriptors"],s["layout"],b,s["original_dtype"].removeprefix("torch."))
            check_formats(obs,source)
            input_bytes=C.checked(s["input_ref"],2**22)
            value=O.check_axis(obs,input_bytes,s["layout"],b,s["original_dtype"].removeprefix("torch."),
              lambda ref:C.checked(ref,2**22),vector=np)
            checked.append(dict(rank=r,logical_layer=l,bits=b,axis=axis,raw_observation_ref=actual_ref,**value))
    C.need(len(checked)==256 and C.ref(producer_ref["path"])==producer_ref,"all256 original writers immutable through independent oracle")
    return dict(schema="skvq.actual-writer.independent/v1",status="ACTUAL_ALL64_Q2Q4_WRITER_BYTES_CONSUMED",
      source_ref=source,producer_ref=producer_ref,input_plan_ref=result["input_plan_ref"],
      device_proof_ref=result["device_proof_ref"],actual_numpy_ref=numpy_ref,checked=checked,
      actual_cases=128,actual_axis_writer_calls=256,all_original_payload_SS_ZP_bytes_exact=True,
      sink5_recent128_full_guards_exact=True,original_full_input_bytes_unchanged=True,
      runtime_post_RoPE_original_K=True,unified_clip=.95,smooth_enabled=False,
      actual_scope="writer ABI replay only; independent attention/reader/lifecycle/model pending",
      whole_owned_original_cleanup_semantic_consumption_pending=True,**C.scopes())
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true")
    ap.add_argument("--source-manifest-sha256");ap.add_argument("--producer-ref-json");ap.add_argument("--output");a=ap.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**C.scopes())));return
    C.need("torch"not in sys.modules and"torch_npu"not in sys.modules and
      not list(Path("/dev").glob("davinci*"))and
      not any(Path("/dev",x).exists()for x in("devmm_svm","hisi_hdc")),
      "actual Devices[] independent CPU; no NPU idle requirement")
    producer=json.loads(Path(a.producer_ref_json).read_bytes());out=Path(a.output)
    C.need(out==Path(producer["path"]).parent/"WRITER_INDEPENDENT.json"and not out.exists(),"unique after-release independent sink")
    print(json.dumps(C.publish(out,consume(producer,a.source_manifest_sha256)),sort_keys=True))
if __name__=="__main__":main()
