#!/usr/bin/env python3
"""NEW true-P2..15 eager native continuation gate. Default OFF; MAIN executes."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
from contract import HERE,REPO,PROJECT,LEGACY,SHARDS,admission,after_check,deadline,matrix,source_check,require,BUILDER_SNAPSHOT,BUILDER_SHA

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true")
    p.add_argument("--check-sources",action="store_true")
    p.add_argument("--shard",choices=tuple(SHARDS),default="P2-8")
    p.add_argument("--physical-card",type=int,choices=(4,5,6,7),default=4)
    for name in ("preflight","build-receipt","library","out","decode-build-receipt",
                 "decode-library","native-anchor-report","reference-library","builder-snapshot"):
        p.add_argument("--"+name,type=Path)
    for name in ("packet-sha256","legacy-runtime-manifest-sha256","decode-library-sha256",
                 "reference-library-sha256","builder-sha256"):
        p.add_argument("--"+name)
    p.set_defaults(builder_snapshot=BUILDER_SNAPSHOT,builder_sha256=BUILDER_SHA)
    return p

def tensor_hash(torch,x):
    if x is None:return None
    return {"shape":list(x.shape),"dtype":str(x.dtype),
            "sha256":hashlib.sha256(x.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()}

def record_summary(record,digest):
    return {"pointers_before":record.get("pointers_before"),"pointers_after":record.get("pointers_after"),
            "dispatch_error":record.get("dispatch_error"),"output_copy_errors":record.get("output_copy_errors"),
            "input_copy_errors":record.get("input_copy_errors"),
            "before_hashes":[digest(x) for x in (record.get("before") or [])],
            "after_hashes":[digest(x) for x in (record.get("after") or [])],
            "return_hashes":[digest(x) for x in (record.get("returns") or [])]}

class RowwiseReference:
    """Explicit callable dependency, never replacement of a frozen global/op."""
    def __init__(self,torch,invoke,journal,counters,digest=None,clock=time.perf_counter_ns,guard=deadline):
        self.torch,self.invoke,self.journal,self.counters,self.clock=torch,invoke,journal,counters,clock
        self.digest=digest or (lambda x:tensor_hash(torch,x))
        self.guard=guard
    def __call__(self,gate,ref,inputs,selected,plans,sr,nd):
        self.guard()
        p=selected.shape[0]
        require(1<=p<=16 and all(x.shape[0]==p for x in inputs),"rowwise actual request geometry")
        state={"p":p,"active_row":None,"records":[],"partial_outputs":[],
               "full_selected":selected.clone(),"resynchronizes_candidate_state":False}
        gate.fixture["rowwise_reference"]=state
        result_rows=[[],[],[]]
        for row in range(p):
            self.guard();state["active_row"]=row
            # g rows48B/beta rows24B: do not pass potentially unaligned offset views.
            row_inputs=[nd(x[row:row+1].contiguous().clone()) for x in inputs]
            row_selected=selected[row:row+1].contiguous().clone()
            primary=[];dispatched=[False];started=self.clock()
            def tracked_reference(*operands):
                try:
                    dispatched[0]=True;self.counters["row_reference_calls"]+=1
                    value=ref(*operands)
                    self.torch.npu.synchronize()
                    return value
                except BaseException as error:
                    # Preserve original async/dispatch error before old nullable-copy queries.
                    primary.append((error,error.__traceback__))
                    state["original_native_error"]={"row":row,"error":repr(error),
                                                      "traceback":traceback.format_exc()}
                    raise
            try:
                outputs=self.invoke(gate,tracked_reference,row_inputs,row_selected,plans,sr,nd)
                require(len(outputs)==3 and all(x.shape[0]==1 for x in outputs),"B1 reference output geometry")
            except BaseException as error:
                record=gate.fixture.get("independent_reference",{})
                state["records"].append({"row":row,"record":record,"exception":repr(error)})
                failure={"row":row,"p":p,"elapsed_ns":self.clock()-started,"exception":repr(error),
                         "native_primary":state.get("original_native_error"),"executed":dispatched[0],
                         "step":gate.fixture.get("step"),"stage":gate.fixture.get("stage")}
                try:failure["record"]=record_summary(record,self.digest)
                except BaseException as secondary:failure["summary_error"]=repr(secondary)
                try:self.journal(failure,True)
                except BaseException as secondary:print("secondary row journal failure: "+repr(secondary),file=sys.stderr)
                try:gate.retain("intermediate_row_failure")
                except BaseException as secondary:print("secondary row fixture failure: "+repr(secondary),file=sys.stderr)
                if primary:raise primary[0][0].with_traceback(primary[0][1])
                raise
            record=gate.fixture["independent_reference"]
            state["records"].append({"row":row,"record":record,"exception":None})
            state["partial_outputs"].append(outputs)
            for i,x in enumerate(outputs):result_rows[i].append(x)
            summary=record_summary(record,self.digest)
            # The frozen invoke checked these in addition to ABI/ND/finite/nonalias.
            summary.update(immutable_inputs_guard=True,physical_ND_guard=True,
                           outputs_nonalias_guard=True,sole_final_BF16_cast_guard=True)
            self.journal({"row":row,"p":p,"elapsed_ns":self.clock()-started,"exception":None,
                          "executed":True,"step":gate.fixture.get("step"),"stage":gate.fixture.get("stage"),"record":summary},row==p-1)
        state["active_row"]=None
        return tuple(self.torch.cat(rows,dim=0) for rows in result_rows)

def journal_writer(out,context):
    path=out/"reference_rows.jsonl"
    with path.open("x"):pass
    serial=[0]
    def write(row,commit):
        serial[0]+=1
        row={"serial":serial[0],"context":dict(context),**row}
        with path.open("a") as stream:
            stream.write(json.dumps(row,allow_nan=False)+"\n")
            stream.flush()
            if commit:os.fsync(stream.fileno())
    return write

def durable(torch,out,label,data):
    target=out/(label+".pt")
    with target.open("xb") as stream:
        torch.save(data,stream);stream.flush();os.fsync(stream.fileno())
    return {"path":str(target),"sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
            "durable_before_CPU_golden":True}

class TimedOps:
    def __init__(self,ops,counters,clock=time.perf_counter_ns):
        self.ops,self.counters,self.clock=ops,counters,clock
        self.last_pack_start=None
    def prepare(self,*args):
        deadline();self.counters["candidate_prepare_calls"]+=1
        return self.ops.prepare(*args)
    def pack(self,*args):
        deadline();self.last_pack_start=self.clock();self.counters["candidate_pack_calls"]+=1
        return self.ops.pack(*args)
    def decode(self,*args):
        deadline();self.counters["candidate_decode_calls"]+=1
        return self.ops.decode(*args)

def anchor(torch,nd,gate,ref,invoke,rowwise,plan,context):
    from general_sr_native_gate import turn
    from evidence import exact
    independent=importlib.import_module("independent_oracle")
    from packing_oracle import seed
    generator=torch.Generator(device="cpu").manual_seed(260627513+161616)
    q,k,v,g,beta,ids=turn(16,19,0,generator,False)
    selected=independent.unpack_value_major(seed(torch,independent,19,plan),plan).index_select(0,ids.long()).contiguous()
    inputs=[nd(x) for x in (q,k,v,g,beta)]
    plans=[nd(x) for x in (plan.pk,plan.pv,plan.pv.argsort(1).int())];sr=nd(plan.c)
    gate.fixture={"stage":"B16_split_anchor","selected":selected,"q":q,"k":k,"v":v,"g":g,"beta":beta}
    context.update(stage="anchor",label="B16_full_vs_16_B1",step=0)
    primary=[]
    def tracked_full(*operands):
        try:
            value=ref(*operands);torch.npu.synchronize();return value
        except BaseException as error:
            primary.append((error,error.__traceback__))
            gate.fixture["full_B16_original_error"]={"error":repr(error),"traceback":traceback.format_exc()}
            raise
    try:full=invoke(gate,tracked_full,inputs,selected,plans,sr,nd)
    except BaseException:
        if primary:raise primary[0][0].with_traceback(primary[0][1])
        raise
    gate.fixture["full_B16_reference"]=gate.fixture["independent_reference"]
    split=rowwise(gate,ref,inputs,selected,plans,sr,nd)
    guards=[exact(torch,a,b) for a,b in zip(full,split)]
    gate.check("actual_B16_vs_16_B1_all_three_bitwise",all(guards),{"returns_bitwise":guards})
    gate.report["rowwise_anchor"]={"status":"passed","batch":16,"full_calls":1,"row_calls":16,
                                  "returns_bitwise":guards,"npu_executed":True}
    gate.save()

def native_matrix(args,torch,npu,nd,gate,pack_ops,decode_ops,ref,rowwise,context):
    from native_feedback import native_context,continuation_initial,actual_unpack,feedback
    from packing_oracle import layout,seed
    from selected_contract import selection,REGIONS
    from evidence import observe,exact
    from arena import Arena
    from run import pack_once
    from general_sr_native_gate import turn
    independent=importlib.import_module("independent_oracle")
    gdn=importlib.import_module("vllm_ascend.ops.gdn")
    require(gate.report.get("rowwise_anchor",{}).get("status")=="passed","actual split anchor required")
    with native_context(torch,args.out):
        for p in matrix(args.shard):
            deadline();s=p+3;plan=layout(torch,independent,True)
            devplans=[nd(x) for x in (plan.pk,plan.pv,plan.c)]
            inv_pv=nd(plan.pv.argsort(1).int())
            for kind in ("adjacent","guard_gaps"):
                golden=seed(torch,independent,s,plan);arena=Arena(torch,npu,nd,s,kind,golden)
                ids=torch.tensor(selection(p,s,1),dtype=torch.int32)
                for continuation in (False,True):
                    deadline()
                    label="native_P"+str(p)+"_"+kind+("_continuation" if continuation else "_fresh")
                    context.update(stage="native",label=label,step=0)
                    gate.report["active_case"]={"label":label,"p":p,"slots":ids.tolist()}
                    started=time.perf_counter_ns()
                    initial=nd(torch.zeros((p,12,128,128),dtype=torch.float32))
                    if continuation:
                        expected=continuation_initial(torch,independent,nd,golden,plan,ids,p)
                        actual,cpu=actual_unpack(torch,npu,gdn,decode_ops,pack_ops,arena,plan,devplans,ids,p,nd,gate)
                        gate.check("true_P_service_unpack_vs_own_independent_FP32_bitwise",
                                   exact(torch,cpu,expected.cpu().clone()))
                        initial=actual
                    lengths=[65+(i%3) for i in range(p)];starts=[0]
                    for n in lengths:starts.append(starts[-1]+n)
                    total=starts[-1]
                    generator=torch.Generator(device="cpu").manual_seed(260627513+p*1009+int(continuation))
                    q=(torch.randn(1,total,4,128,generator=generator)*.1).bfloat16()
                    k=(torch.randn(1,total,4,128,generator=generator)*.1).bfloat16()
                    v=(torch.randn(1,total,12,128,generator=generator)*.02).bfloat16()
                    g=-torch.rand(1,total,12,generator=generator)*.04
                    beta=(torch.rand(1,total,12,generator=generator)*.4+.2).bfloat16()
                    operands=[nd(x) for x in (q,k,v,g,beta)]
                    cu=nd(torch.tensor(starts,dtype=torch.int64))
                    gate.fixture={"stage":"actual_native_chunk","p":p,"continuation":continuation,
                        "q":q,"k":k,"v":v,"g":g,"beta":beta,"cu":starts,
                        "initial_cpu":initial.cpu().clone(),"raw_before":arena.raw.cpu().clone(),
                        "plan":{"c":plan.c,"pk":plan.pk,"pv":plan.pv}}
                    chunk_start=time.perf_counter_ns()
                    result,cpu,after,record=observe(torch,gate,"native_chunk",
                        lambda:gdn.chunk_gated_delta_rule(*operands,initial_state=initial,
                            output_final_state=True,cu_seqlens=cu,prebuilt_meta=None,head_first=False,
                            use_qk_l2norm_in_kernel=True),operands+[initial,cu,arena.raw])
                    chunk_end=time.perf_counter_ns()
                    gate.healthy(record,"actual_native_chunk_dispatch")
                    gate.check("native_chunk_all_inputs_and_arena_immutable",
                        record["pointers_before"]==record["pointers_after"] and
                        all(exact(torch,a,b) for a,b in zip(record["before"],after)))
                    require(isinstance(result,(tuple,list)) and len(result)==2,"native chunk arity")
                    output,last=result
                    require(tuple(last.shape)==(p,12,128,128) and last.dtype==torch.float32 and
                        tuple(output.shape)==(1,total,12,128) and output.dtype==torch.bfloat16 and
                        bool(torch.isfinite(cpu[0]).all()) and bool(torch.isfinite(cpu[1]).all()),"native output/final ABI/finite")
                    final=nd(last.transpose(-1,-2).contiguous());indices=nd(ids)
                    checkpoint=durable(torch,args.out,label+"_native_before_golden",{
                        "fixture":gate.fixture,"native_final_value_major":cpu[1].transpose(-1,-2).contiguous(),
                        "raw_before":arena.raw.cpu().clone(),"golden_before":{n:getattr(golden,n).clone() for n in REGIONS},
                        "indices":ids,"source_bindings":gate.report["bindings"]})
                    gate.report.setdefault("native_checkpoints",[]).append(checkpoint);gate.save()
                    prepare_inputs=[final,*arena.states,*devplans,indices,arena.raw]
                    _,_,prepared_after,prepared=observe(torch,gate,"native_pack_prepare",
                        lambda:pack_ops.prepare(final,*arena.states,*devplans,indices,False),prepare_inputs)
                    gate.healthy(prepared,"native_pack_prepare")
                    gate.check("native_pack_prepare_entire_inputs_raw_immutable",
                        prepared["returns"] is None and prepared["pointers_before"]==prepared["pointers_after"] and
                        all(exact(torch,a,b) for a,b in zip(prepared["before"],prepared_after)))
                    gate.fixture["durable_native_checkpoint"]=checkpoint
                    import packing_oracle
                    cache_before=packing_oracle.exact_divide.cache_info()._asdict()
                    pack_start=time.perf_counter_ns()
                    pack_once(torch,npu,gate,pack_ops,arena,final,(plan,devplans),indices,golden,label)
                    pack_end=time.perf_counter_ns()
                    gate.report["cases"][-1]["fixture_origin"]="actual_native_chunk_FP32_final_true_P"
                    before_steps=gate.report["counts_actual"]["candidate_decode_calls"]
                    feedback_start=time.perf_counter_ns()
                    context.update(stage="feedback",label=label)
                    feedback(torch,npu,nd,decode_ops,ref,rowwise,turn,gate,arena,golden,plan,devplans,inv_pv,p,label)
                    end=time.perf_counter_ns()
                    require(gate.report["counts_actual"]["candidate_decode_calls"]-before_steps==160,
                            "actual candidate true-P full160 calls")
                    gate.report.setdefault("timings",[]).append({"label":label,"p":p,
                        "native_chunk_observe_wall_ns":chunk_end-chunk_start,
                        "pack_total_wall_ns":pack_end-pack_start,
                        "pre_dispatch_oracle_and_copy_wall_ns":pack_ops.last_pack_start-pack_start,
                        "feedback_wall_ns":end-feedback_start,"case_total_wall_ns":end-started,
                        "fraction_cache_before":cache_before,
                        "fraction_cache_after":packing_oracle.exact_divide.cache_info()._asdict(),
                        "scope":"correctness process timings, NOT kernel or E2E performance"})
                    gate.save()
                    del initial,final,last,result,cpu
    gate.report.pop("active_case",None)

def decode_reference_schema(decode,ref):
    ds,ps,rs=decode.decode.default._schema,decode.prepare.default._schema,ref.default._schema
    require([x.name for x in ds.arguments]==["query","key","value","g","beta","high_state","low_state",
        "low_scale","pk","pv","inv_pv","sr","actual_seq_lengths","state_indices"],"actual decode14")
    require([x.name for x in ps.arguments]==["query","high_state","pk","pv","inv_pv","sr"],"actual prepare6")
    require([i for i,x in enumerate(ds.arguments) if x.alias_info and x.alias_info.is_write]==[5,6,7] and
            len(ds.returns)==1 and ds.returns[0].alias_info is None and not ps.returns and
            not any(x.alias_info for x in ps.arguments),"decode state-only aliases / immutable prepare")
    require([x.name for x in rs.arguments]==["q","k","v","g","beta","state_selected","pk","pv","inv_pv","sr"] and
            len(rs.returns)==3 and not any(x.alias_info for x in list(rs.arguments)+list(rs.returns)),
            "actual independent reference10/three nonalias returns")
    return {"decode":str(ds),"prepare":str(ps),"reference":str(rs)}

def main(argv=None):
    args=parser().parse_args(argv)
    if not args.execute:
        if args.check_sources:source_check(args.packet_sha256)
        print(json.dumps({"status":"source_checked_disabled" if args.check_sources else "disabled",
            "default_enabled":False,"npu_executed":False,"graph_supported":False,"serving_ready":False}))
        return 0
    binding=admission(args)
    args.out.mkdir(parents=True,exist_ok=False)
    report={"schema":"damp-native-prefill-intermediate-npu/v1","status":"running","shard":args.shard,
            "actual_batches":list(matrix(args.shard)),"bindings":binding,"cases":[],"checks":[],
            "limits":binding["limits"],"steps":160,"npu_executed":False,"graph_supported":False,
            "prebuilt_metadata_verified":False,"mixed_fresh_continuation_verified":False,
            "model_cache_admitted":False,"serving_ready":False,"performance_measurement_admitted":False,
            "counts_actual":{"row_reference_calls":0,"candidate_prepare_calls":0,
                             "candidate_pack_calls":0,"candidate_decode_calls":0}}
    os.environ["TORCH_DEVICE_BACKEND_AUTOLOAD"]="0"
    try:
        (args.out/"report.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
        import torch
        import torch_npu
        from evidence import Recorder
        gate=Recorder(torch,args.out,report)
    except BaseException as error:
        report.update(status="failed_before_recorder",error=repr(error),traceback=traceback.format_exc())
        try:(args.out/"report.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
        except BaseException as secondary:print("secondary startup report failure: "+repr(secondary),file=sys.stderr)
        print("primary startup failure: "+repr(error),file=sys.stderr);return 1
    try:
        import selected_contract as old
        old.validate_proof(json.loads(args.preflight.read_text()),args.physical_card)
        torch.npu.set_device(0)
        require(torch.npu.get_device_name(0)=="Ascend910B4" and
                torch.__version__=="2.10.0+cpu" and torch_npu.__version__=="2.10.0.post4","actual runtime ABI/SoC")
        require(os.environ.get("DAMP_ENABLE_NATIVE_REFERENCE")=="1","test-only native reference opt-in")
        def nd(x):
            value=torch_npu.npu_format_cast(x.contiguous().to("npu:0"),2)
            if value.data_ptr()%32:value=torch_npu.npu_format_cast(value.clone(),2)
            require(torch_npu.get_npu_format(value)==2 and value.is_contiguous() and value.data_ptr()%32==0,"physical ND32")
            return value
        import run as legacy_run
        require(Path(legacy_run.__file__).resolve()==LEGACY/"run.py","explicit frozen run module origin")
        schema,loaded=legacy_run.schema,legacy_run.loaded
        for path in (args.library,args.decode_library,args.reference_library):torch.ops.load_library(str(path))
        require(loaded(args.library)==binding["selected_library_sha256"] and
                loaded(args.decode_library)==binding["decode_library_sha256"] and
                loaded(args.reference_library)==binding["reference_library_sha256"],"actual mapped explicit SOs")
        pack_real=torch.ops.qwen36_damp_selected_prefill_v1
        decode_real=torch.ops.qwen36_damp_all_batch_v3;ref=torch.ops.qwen36_damp_reference.decode
        report["selected_schema"]=schema(torch,pack_real)
        report["decode_reference_schema"]=decode_reference_schema(decode_real,ref)
        sys.path.insert(0,str(PROJECT/"tests"))
        sys.path.insert(0,str(PROJECT/"operator/production_integer_compaction_v1/tests"))
        from protocols import invoke_reference
        from packing_oracle import layout
        independent=importlib.import_module("independent_oracle")
        context={}
        rowwise=RowwiseReference(torch,invoke_reference,journal_writer(args.out,context),report["counts_actual"])
        pack_ops=TimedOps(pack_real,report["counts_actual"]);decode_ops=TimedOps(decode_real,report["counts_actual"])
        report["npu_executed"]=True;gate.save()
        anchor(torch,nd,gate,ref,invoke_reference,rowwise,layout(torch,independent,True),context)
        native_matrix(args,torch,torch_npu,nd,gate,pack_ops,decode_ops,ref,rowwise,context)
        require(report["counts_actual"]["candidate_decode_calls"]==binding["counts"]["decode_turns"] and
                report["counts_actual"]["row_reference_calls"]==
                  binding["counts"]["row_reference_calls"]+16 and
                len(report["native_checkpoints"])==binding["counts"]["native_cases"] and
                report["counts_actual"]["candidate_pack_calls"]==binding["counts"]["native_cases"] and
                report["counts_actual"]["candidate_prepare_calls"]==2*binding["counts"]["native_cases"],"complete actual shard counts")
        after_check(args,binding)
        native=binding["native"]
        report["loaded_libraries_final"]={str(path):loaded(path) for path in
            (args.library,args.decode_library,args.reference_library,Path(native["native_runtime_library_path"]))}
        require(all(report["loaded_libraries_final"][str(path)]==expected for path,expected in
            ((args.library,binding["selected_library_sha256"]),(args.decode_library,binding["decode_library_sha256"]),
             (args.reference_library,binding["reference_library_sha256"]),
             (Path(native["native_runtime_library_path"]),native["native_runtime_library_sha256"]))),"end mapped SO identity")
        report.update(status="true_P_native_selected_pack_own_feedback_pass",completed_ns=time.time_ns())
        gate.save();print(json.dumps({"status":report["status"]}));return 0
    except BaseException as error:
        report.update(status="failed",error=repr(error),traceback=traceback.format_exc(),
                      retired_call=report.get("active_case"),retry_allowed=False)
        for label,action in (("fixture",lambda:gate.retain("intermediate_failure")),("report",gate.save)):
            try:action()
            except BaseException as secondary:print("secondary "+label+" failure: "+repr(secondary),file=sys.stderr)
        print("primary failure: "+repr(error),file=sys.stderr);return 1

if __name__=="__main__":raise SystemExit(main())
