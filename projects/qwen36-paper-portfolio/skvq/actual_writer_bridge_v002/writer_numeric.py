"""Explicit single-card real-capture writer ABI only; default OFF; no model launch.
Owned host must separately consume proof semantics and stop-retain actual CID.
"""
import argparse,hashlib,json,os,sys,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import writer_contract as C
def identity():
    root=Path("/proc/self");text=(root/"stat").read_text()
    command=(root/"cmdline").read_bytes()
    return dict(pid=os.getpid(),start_ticks=int(text[text.rfind(")")+2:].split()[19]),
      cgroup=(root/"cgroup").read_text(),argv=[x.decode()for x in command.split(b"\0")if x],
      cmdline_sha256=hashlib.sha256(command).hexdigest())
def blob(tensor,torch):
    return tensor.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()
def tensor_descriptor(tensor,getter,F):
    fmt=getter(tensor)
    return dict(shape=list(tensor.shape),stride=list(tensor.stride()),dtype=str(tensor.dtype),
      device=str(tensor.device),storage_offset=tensor.storage_offset(),
      storage_nbytes=tensor.untyped_storage().nbytes(),data_ptr=tensor.data_ptr(),
      original_format=F.raw_format(fmt)),fmt
def run(expected,plan_ref,proof_ref,output):
    start=time.monotonic();source=C.source(expected,device_stage=True)
    C.need(os.environ.get("MAIN_SKVQ_WRITER_NUMERIC_ENABLE")=="1"and
      os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0"and os.environ.get("MAIN_OWNED_CID"),
      "MAIN-only single mapped logical0 guest; no implicit lease")
    from writer_inputs import consume_plan
    plan=consume_plan(plan_ref,source);proof=C.device_proof(C.obj(proof_ref),source,plan_ref)
    C.need(os.environ["MAIN_OWNED_CID"]==proof["cid"],"same actual owned CID")
    out=C.new_output(output);who=identity()
    C.publish(out/"RAW_BEFORE_NATIVE_IMPORT.json",dict(source_ref=source,input_plan_ref=plan_ref,
      device_proof_ref=proof_ref,identity=who,phase="before actual framework import",**C.scopes()))
    result=dict(schema="skvq.actual-writer.producer/v1",status="FAILED",source_ref=source,
      input_plan_ref=plan_ref,device_proof_ref=proof_ref,identity=who,cases=[],primary=None,
      physical_card=4,logical_device=0,owned_cid=proof["cid"],**C.scopes())
    try:
        import torch,torch_npu
        torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.npu.set_device(0)
        fmtrow=next(r for r in C.obj(C.CAPTURE)["files"]if r["path"].endswith("/n1_format.py"))
        F=C.module("_skvq_writer_actual_format",fmtrow)
        getter,enum,qualification=F.qualify(torch,torch_npu,source)
        actual_writer=C.module("_skvq_actual_original_device_writer",C.WRITER)
        layout_module=C.module("_skvq_actual_writer_layout",C.LAYOUT)
        for item in plan["rows"]:
            for bits in(2,4):
                case=dict(rank=item["rank"],logical_layer=item["logical_layer"],bits=bits,axes={})
                case_root=out/("r%d-l%s-q%d"%(item["rank"],item["logical_layer"].split(".")[2],bits));case_root.mkdir()
                for axis in("K","V"):
                    selected=item["axes"][axis];kind=selected["original_dtype"].removeprefix("torch.")
                    dtype={"float16":torch.float16,"bfloat16":torch.bfloat16}[kind]
                    input_bytes=C.checked(selected["input_ref"],2**22);l=selected["layout"];width=C.extent(l["starts"],bits)
                    layout=layout_module.Layout(tuple(l["permutation"]),tuple(l["starts"]),tuple(l["smooth"]),l["clip"])
                    rows=torch.frombuffer(bytearray(input_bytes),dtype=dtype).clone().reshape(C.TOKENS,C.DIM).to("npu:0")
                    payload=torch.full((C.TOKENS,width),165,dtype=torch.uint8,device="npu:0")
                    scales=torch.full((C.TOKENS,4),.5,dtype=dtype,device="npu:0")
                    zeros=torch.full((C.TOKENS,4),-1.,dtype=dtype,device="npu:0")
                    planes={"payload":payload,"scales":scales,"zero_points":zeros}
                    before={name:C.raw(case_root/(axis+"-"+name+"-before.bin"),blob(t,torch))for name,t in planes.items()}
                    descriptors={};native_formats={}
                    for name,t in {"input":rows,**planes}.items():
                        descriptors[name],native_formats[name]=tensor_descriptor(t,getter,F)
                    observation=dict(tokens=C.TOKENS,middle=[C.START,C.STOP],shape=[C.TOKENS,C.DIM],
                      input_ref=selected["input_ref"],before=before,before_descriptors=descriptors,
                      actual_format_qualification=qualification,identity=identity())
                    C.publish(case_root/(axis+"-RAW_BEFORE_WRITER.json"),observation)
                    # Exact borrowed enum/chain gate after raw evidence. New allocations are ND, not native-cache assertions.
                    policy=F.policy();serial={name:policy.serial(value,enum)for name,value in native_formats.items()}
                    written=actual_writer.seal_into(rows[C.START:C.STOP],layout,payload,scales,zeros,C.START,bits=bits)
                    torch.npu.synchronize()
                    after={name:C.raw(case_root/(axis+"-"+name+"-after.bin"),blob(t,torch))for name,t in planes.items()}
                    input_after=C.raw(case_root/(axis+"-INPUT_AFTER.bin"),blob(rows,torch))
                    observation.update(after=after,input_after_ref=input_after,returned_bytes=written,
                      serialized_formats=serial,writer_source=C.WRITER,after_identity=identity())
                    rawref=C.publish(case_root/(axis+"-RAW_AFTER_WRITER.json"),observation)
                    C.need(observation["identity"]==observation["after_identity"]==who,"same native actual process throughout")
                    C.need(C.ref(C.WRITER["path"])==C.WRITER,"original device writer not modified")
                    case["axes"][axis]=rawref
                    del rows,payload,scales,zeros,planes
                result["cases"].append(case)
        C.need(len(result["cases"])==128 and sum(len(x["axes"])for x in result["cases"])==256,"complete named writer ABI scope")
        result.update(status="ACTUAL_ALL64_Q2Q4_WRITER_RETURNED_RAW_PENDING_INDEPENDENT",
          actual_case_count=128,actual_axis_writer_calls=256,npu_executed=True,host_owned_semantic_consumer_required=True)
    except BaseException as exc:
        result["primary"]=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
    result["elapsed_seconds"]=time.monotonic()-start;result["identity_at_terminal"]=identity()
    terminal=C.publish(out/"PRODUCER_RESULT.json",result)
    C.need(result["primary"]is None,"real writer failed; original/raw retained, no fake admission")
    return terminal
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true")
    ap.add_argument("--source-manifest-sha256");ap.add_argument("--input-plan-ref-json")
    ap.add_argument("--device-proof-ref-json");ap.add_argument("--output");a=ap.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**C.scopes())));return
    C.need(a.input_plan_ref_json and a.device_proof_ref_json and a.output,"actual owned proof/actual input/new output")
    plan=json.loads(Path(a.input_plan_ref_json).read_bytes());proof=json.loads(Path(a.device_proof_ref_json).read_bytes())
    print(json.dumps(run(a.source_manifest_sha256,plan,proof,a.output),sort_keys=True))
if __name__=="__main__":main()
