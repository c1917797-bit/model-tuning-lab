"""Real successful014 whole -> real cal006 whole -> actual sample0 postRoPE K/V."""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import writer_contract as C
def calibration_modules():
    body=C.obj(C.CALIBRATION);rows={Path(r["path"]).name:r for r in body["files"]}
    parent=Path(C.CALIBRATION["path"]).parent
    for r in body["files"]+body["dependencies"]:C.checked(r)
    if str(parent)not in sys.path:sys.path.insert(0,str(parent))
    C.module("common",rows["common.py"])
    # All donor flat modules explicitly qualified; no candidate calibration fit imported.
    for name in("cluster_oracle","torch_zip_int64","module_snapshots","library_probe","calibration_inputs",
                "consume","cpu_entry","cpu_host","consume_cpu_whole"):
        C.module(name,rows[name+".py"])
    return sys.modules["common"],sys.modules["calibration_inputs"],sys.modules["consume_cpu_whole"]
def verify_whole(ref):
    value=C.obj(ref)
    C.need(value["schema"]=="skvq.default-tp-local.whole/v1"and
      value["status"]=="OWNED_CPU_ALL128_CALIBRATION64_CONSUMED"and value["source_ref"]==C.CALIBRATION and
      value["capture_whole_ref"]["sha256"]and value["actual_rank_fits"]==128 and
      len(value["calibration_refs"])==len(value["writer_handoffs"])==64 and value["unified_clip"]==.95 and
      value["smooth_enabled"]is False and value["runtime_pre_rope"]is False and
      value["author_global_grouping_equivalent"]is False and
      all(value[k]is False for k in("native_ready","model_ready","performance_ready","task_ready")),
      "actual CPU all128/default64 whole; failed/source-only/fixture cannot unlock")
    common,inputs,consumer=calibration_modules()
    original=consumer.consume(Path(value["host_result_ref"]["path"]).parent,value["original_ref"],C.CALIBRATION["sha256"])
    C.need(original==value,"read-only real whole CPU/source/ownership/full independent fitting replay")
    bundle=inputs.inputs(value["capture_whole_ref"])
    C.need(bundle["capture_whole_ref"]==value["capture_whole_ref"],"same current014 cohort")
    return value,bundle,common
def records(producer):
    C.need(len(producer["rank_results"])==4,"actual all4 raw rank results")
    selected={};seen_ranks=set()
    for rref in producer["rank_results"]:
        rank=C.obj(rref);r=rank["rank"]
        C.need(type(r)is int and 0<=r<4 and r not in seen_ranks and
          rank["status"]=="ALL_RANK_RAW_CAPTURED_NOT_CALIBRATED"and len(rank["events"])==4096,
          "actual complete unique rank capture")
        seen_ranks.add(r);seen=set()
        for er in rank["events"]:
            e=C.obj(er);key=(e["sample_id"],e["logical_layer"])
            C.need(type(e["sample_id"])is int and 0<=e["sample_id"]<256 and
              e["logical_layer"]in C.LAYERS and e["rank"]==r and key not in seen,"actual unique complete sample/layer")
            seen.add(key)
            if e["sample_id"]==0:selected[(r,e["logical_layer"])]=(er,e)
        C.need(seen=={(s,l)for s in range(256)for l in C.LAYERS},"complete256x16, not selected subset called whole")
    C.need(len(selected)==64,"all4x16 selected real sample0")
    return selected
def make_plan(whole_ref,source_ref):
    whole,bundle,common=verify_whole(whole_ref)
    producer=C.obj(bundle["capture_producer_ref"])
    C.need(producer["current_source_ref"]==C.CAPTURE,"current014 producer, not old failed009")
    actual=records(producer);calibrations={}
    for rr in whole["calibration_refs"]:
        value=C.obj(rr);key=(value["rank"],value["layer"])
        C.need(key not in calibrations and value["source_ref"]==C.CALIBRATION and
          value["capture_whole_ref"]==whole["capture_whole_ref"],"same whole/current64 artifacts")
        calibrations[key]=rr
    writer=C.module("_skvq_actual_writer_layout",C.LAYOUT)
    rows=[]
    for r in range(4):
        for layer in C.LAYERS:
            er,e=actual[(r,layer)];cr=calibrations[(r,layer)]
            layouts,receipt=writer.load(cr["path"],sha256=cr["sha256"],
              model_sha256=bundle["model_identity"]["model_sha256"],layer=layer,rank=r,tp=4,dim=256)
            order=e["actual_same_input_post_rope_evidence"]["actual_qkv_legacy_order"]
            C.need(order["global_kv_channel_indices"]==list(range(r*256,(r+1)*256)),"actual TP KV order")
            axes={}
            for axis in("K","V"):
                s=e["snapshots"][axis.lower()]
                C.need(s["shape"]==[C.TOKENS,1,C.DIM]and s["dtype"]==bundle["dtype"]and
                  s["snapshot_contiguous_independent_clone"]is True and s["ref"]["bytes"]==C.TOKENS*C.DIM*2,
                  "actual full4096 original A16 postRoPE K/original V shape")
                C.checked(s["ref"],limit=2**22);l=layouts[axis]
                axes[axis]=dict(input_ref=s["ref"],original_dtype=s["dtype"],
                  layout=C.layout(dict(permutation=list(l.permutation),starts=list(l.starts),smooth=list(l.smooth),clip=l.clip)))
            rows.append(dict(rank=r,logical_layer=layer,sample_id=0,event_ref=er,calibration_ref=cr,axes=axes))
    C.need(len(rows)==64,"all64 selected actual tensor/layout identities")
    return dict(schema="skvq.actual-writer.input-plan/v1",source_ref=source_ref,
      calibration_whole_ref=whole_ref,capture_whole_ref=whole["capture_whole_ref"],
      capture_producer_ref=bundle["capture_producer_ref"],rows=rows,
      actual_scope="single physical4 replay of actual four TP-rank tensors; not new TP4 model execution",
      bits=[2,4],tokens=C.TOKENS,sink=C.SINK,window=C.WINDOW,middle=[C.START,C.STOP],
      unified_clip=.95,smooth_enabled=False,runtime_pre_rope=False,
      cases=128,axis_writer_calls=256,unquantized_sink_recent_preserved=True,
      output_logical_cap_bytes=C.OUTPUT_CAP,**C.scopes())
def consume_plan(ref,source_ref):
    body=C.obj(ref);expected=make_plan(body["calibration_whole_ref"],source_ref)
    C.need(body==expected,"actual source/raw/fullcalibration read-only input plan replay");return body
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true")
    ap.add_argument("--source-manifest-sha256");ap.add_argument("--calibration-whole-ref-json");ap.add_argument("--output");a=ap.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**C.scopes())));return
    source=C.source(a.source_manifest_sha256)
    C.need(a.calibration_whole_ref_json and a.output,"actual whole and new plan output")
    whole=json.loads(Path(a.calibration_whole_ref_json).read_bytes());out=C.new_output(a.output)
    print(json.dumps(C.publish(out/"INPUT_PLAN.json",make_plan(whole,source)),sort_keys=True))
if __name__=="__main__":main()
