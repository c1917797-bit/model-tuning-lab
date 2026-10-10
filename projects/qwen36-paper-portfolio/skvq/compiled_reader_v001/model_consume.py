"""After-release independent all4/all16/two-step compiled SKVQ model smoke.
This is NOT whole176, GDN48 content/graph/lifecycle/model-ready authority.
A final whole-operation consumer must bind this component to actual owned host.
"""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import contract as C
import reference as O
from reader_consume import qualified_numpy
LAYERS=tuple("model.layers."+str(i)+".self_attn"for i in range(3,64,4))
def original_rows(frame,axis):
    pre=C.obj(frame["original_prefill_ref"]);raw=C.read(pre["original"][axis])
    C.need(pre["schema"]=="skvq.compiled-reader.original-prefill/v1"and pre["source_ref"]==frame["source_ref"]and
      pre["full32768_input"]is True and pre["post_RoPE_K"]is True and len(raw)==32768*512,
      "real original full32768 postRoPE K/V, not candidate reconstructed values")
    expect=list(range(32769,frame["length"]+1))
    C.need([x["length"]for x in frame["original_decode_history"]]==expect,"every original native decode row in causal order")
    for row in frame["original_decode_history"]:
        current=C.read(row["original"][axis]);C.need(len(current)==512,"one original native new KV row")
        raw+=current
    C.need(len(raw)==frame["length"]*512,"complete causal original token domain")
    return raw
def decode_frame(frame,np):
    source=frame["source_ref"];binding=frame["native_binding"];length=frame["length"];kind=frame["kind"]
    C.need(frame["schema"]=="skvq.compiled-reader.model-frame/v1"and length in(32769,32770)and
      frame["capacity"]==33792 and frame["bits"]==2 and binding["source_ref"]==source and binding["phase"]=="decode"and
      binding["logical_layer"]==frame["logical_layer"]and binding["seq_lens_list"]==[length]and
      binding["actual_total_scheduled"]==1 and binding["num_computed_tokens"]==length-1 and
      binding["epoch"]==1 and binding["graph_mode"]=="NONE"and
      frame["native_dense_prefill_and_cache_write_retained"]is True and frame["no_memory_reduction_claim"]is True,
      "actual first/two eager decode; no memory savings or synthetic token/ID")
    q=O.values(C.read(frame["current_input"]["Q"]),kind);C.need(len(q)==1536,"all actual6x256 query elements")
    decoded={}
    for axis in("K","V"):
        p=frame["pool"][axis];layout=frame["layouts"][axis];n,widths=O.geometry(layout,2);stride=sum(widths)
        payload=C.read(p["payload"]);scales=C.read(p["scales"]);low=C.read(p["zero_points"])
        C.need(len(payload)==33792*stride and len(scales)==len(low)==33792*8 and
          len(C.read(p["edges"]))==133*512 and len(C.read(p["map"]))==256*3*4,"entire allocated live compact/edge/map bytes")
        original=original_rows(frame,axis)
        decoded[axis]=O.decode_numpy(payload[:length*stride],scales[:length*8],low[:length*8],
          original,layout,2,kind,length,np)
        # Full writer source equations on ORIGINAL data; never candidate reader decode or mapping.
        W,_=C.writer_modules();body=C.obj(C.WRITER_SOURCE);oracle_row=next(r for r in body["files"]if r["path"].endswith("/writer_byte_oracle.py"))
        byte_oracle=C.load("_skvq_model_independent_writer_equations",oracle_row)
        start=min(5,length);stop=length-128
        encoded=byte_oracle.encode_numpy(original[start*512:stop*512],layout,2,kind,np)
        for name,full,width,unit in(("payload",payload,stride,1),("scales",scales,4,2),("zero_points",low,4,2)):
            C.need(full[start*width*unit:stop*width*unit]==encoded[name],"all actual model affine/round/pack bytes "+axis+":"+name)
        edge=C.read(p["edges"]);expected_edge=original[:start*512]+original[stop*512:]
        C.need(edge==expected_edge,"full sink5/window128 original live edges exact")
    expected=O.attention_numpy([q[h*256:(h+1)*256]for h in range(6)],decoded["K"],decoded["V"],kind,np)
    metrics={name:O.compare(C.read(frame["actual"][name]),expected[name],kind)for name in expected}
    heads=[O.compare(C.read(frame["actual"]["output"])[h*512:(h+1)*512],expected["output"][h*512:(h+1)*512],kind)for h in range(6)]
    return dict(metrics=metrics,heads=heads,all1536_output_elements_checked=True,
      complete_original_quantized_KV_bytes_checked=True,complete_native_sink_recent_edges_checked=True)
def consume(cohort_ref,sha):
    source=C.source(sha);cohort=C.obj(cohort_ref)
    C.need(cohort["schema"]=="skvq.compiled-reader.model-cohort/v1"and cohort["source_ref"]==source and
      cohort["status"]=="ACTUAL_ALL4_FIRST_TWO_DECODE_RAW_RELEASED_PENDING_CPU"and
      len(cohort["rank_final_refs"])==4 and cohort["actual_prompt_tokens"]==32768 and
      cohort["requested_output_tokens"]==3 and cohort["actual_native_decode_steps"]==2,
      "real current cohort, 3 outputs means2 native decode calls; not HTTP-DONE inference")
    C.need(cohort["owned_release_independently_consumed"]is True,"must run this expensive CPU component AFTER own exact release")
    prerequisite=C.reader_whole(cohort["reader_whole_ref"])
    C.need(prerequisite["writer_whole_ref"]==cohort["writer_whole_ref"],"same actual writer and compiled reader prerequisites")
    whole=C.writer_whole(cohort["writer_whole_ref"]);np,nref=qualified_numpy(whole)
    checked=[];ranks=set();request=None
    for final_ref in cohort["rank_final_refs"]:
        final=C.obj(final_ref);identity=final["rank_identity"];rank=identity["public_TP_rank"]
        C.need(type(rank)is int and 0<=rank<4 and rank not in ranks and final["source_ref"]==source and
          final["schema"]=="skvq.compiled-reader.worker-final/v1"and final["restored"]is True and
          final["GDN48_function_identities_unchanged"]is True and final["actual_native_prefill_calls"]==16 and
          final["actual_compiled_decode_calls"]==32 and len(final["events"])==32,
          "all4 real unique rank finals/instance restoration, not GDN numeric claim")
        ranks.add(rank);seen=set()
        for row in final["events"]:
            frame=C.obj(row);binding=frame["native_binding"];key=(frame["logical_layer"],frame["length"])
            C.need(key not in seen and key[0]in LAYERS and key[1]in(32769,32770)and
              binding["rank_identity"]==identity and frame["source_ref"]==source,"all unique actual same-source/rank/layer/step frames")
            if request is None:request=binding["request_id"]
            C.need(binding["request_id"]==request,"same actual native assigned request across all4 workers")
            seen.add(key);checked.append(dict(rank=rank,layer=key[0],length=key[1],frame_ref=row,**decode_frame(frame,np)))
        C.need(seen=={(l,n)for l in LAYERS for n in(32769,32770)},"whole all16/two-step coverage without omissions")
        finish=C.obj(final["actual_native_finished_ref"])
        C.need(finish["schema"]=="skvq.compiled-reader.native-finished/v1"and finish["source_ref"]==source and
          finish["rank_identity"]==identity and finish["finished_req_ids"]==[request]and
          finish["requests_after"]==[]and finish["input_batch_after"]==[]and finish["called_original_update"]is True,
          "actual original finished dispatch/empty native state, not HTTP DONE")
    C.need(ranks==set(range(4))and len(checked)==128,"all64 actual model instances/two compiled decode steps")
    return dict(schema="skvq.compiled-reader.model-independent/v1",status="ALL4_ALL16_TWO_DECODE_NUMERIC_SMOKE_CONSUMED",
      source_ref=source,cohort_ref=cohort_ref,writer_whole_ref=cohort["writer_whole_ref"],actual_numpy_ref=nref,
      actual_frames=128,actual_output_elements=128*1536,checked=checked,threshold_relative_rms=.005,
      actual_prompt_tokens=32768,actual_native_decode_steps=2,no_memory_reduction_or_E2E_claim=True,
      remaining=["whole original owner/resource/source terminal consumer","GDN48 content oracle",
        "complete176/state/mixed/reset/fork/changed-input160/graph","matched1024 performance","final official tasks"],
      **C.scopes())
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--cohort-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**C.scopes())));return
    C.need("torch"not in sys.modules and"torch_npu"not in sys.modules and
      not list(Path("/dev").glob("davinci*")),"independent no-device CPU only")
    C.need(a.cohort_ref_json and a.output,"actual cohort/new sink required")
    print(json.dumps(C.atomic(a.output,consume(json.loads(Path(a.cohort_ref_json).read_bytes()),
      a.source_manifest_sha256)),sort_keys=True))
if __name__=="__main__":main()
