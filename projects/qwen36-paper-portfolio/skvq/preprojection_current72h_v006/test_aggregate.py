"""Transparent stdlib source/consumer regressions; fixtures confer no runtime authority."""
import argparse,ast,copy,hashlib,importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import current_contract as C
import consume_stage as stage
import consume_whole as whole
import physical_hbm as hbm
from model_kwargs import kwargs
REVIEW=None
def source(name):return (HERE/name).read_text()
def node(text,name):
    return next(x for x in ast.parse(text).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))and x.name==name)
def example():
    pref={"path":"/actual/PRODUCER_RESULT.json","bytes":123,"sha256":"a"*64}
    br={"path":"/actual/BASELINE_CONSUMED.json","bytes":234,"sha256":"b"*64}
    pr={"path":"/actual/PREPROJECTION_CONSUMED.json","bytes":345,"sha256":"c"*64}
    b=dict(schema="SKVQ_CAPTURE_RAW_CONSUMED_V1",status="FULL_BASELINE_CAPTURE_AND_ACTUAL_LEGACY_KV_CHANNEL_ORDER_CONSUMED_NOT_CALIBRATED",
        producer_ref=pref,events=16384,qkv_bytes=256*C.GIB,global_QKV_head_order_verified_from_actual_bound_loader=True,
        global_QKV_head_order_verified=True,native_ready=False,model_ready=False)
    p=dict(schema="SKVQ_PREPROJECTION_RAW_CONSUMED_V1",status="ALL_ACTUAL_PREPROJECTION_K_AND_V_EQUIVALENCE_CONSUMED_NOT_AUTHOR_CALIBRATION",
        producer_ref=pref,baseline_receipt_ref=br,events=16384,preprojection_K_raw_bytes=32*C.GIB,
        actual_original_V_equivalence_verified_for_captured_inputs_only=True,native_ready=False,model_ready=False)
    return b,p,br,pr

def protected_real():
    refs=C.PROTECTED_REFS
    if REVIEW:
        local=REVIEW.parent/"kivi-whole-consumer-reviewed-deps-20261010-001"
        refs=[dict(ref,path=str((local/name).absolute())) for ref,name in
          zip(refs,("protected_contract.py","protected_lifecycle.py"))]
    previous=C.PROTECTED_REFS
    try:
        C.PROTECTED_REFS=refs
        return C.protected_module()
    finally:C.PROTECTED_REFS=previous
def protected_row(pid=333,physical=0,cgroup="0::/external/peer",start=123):
    return dict(physical=physical,chip=0,pid=pid,start_ticks=start,cgroup=cgroup,cmdline_sha256="f"*64)
def actual_control(before,after,foreign=False):
    import os,time
    observed=[];real=protected_real()
    helper=types.SimpleNamespace(protected=lambda raw:after,
      idle_one=lambda raw,card:observed.append(("idle",card)),
      legacy=lambda:types.SimpleNamespace(process_rows=lambda raw:([(4,0,444)] if foreign else [])),
      gate_process=lambda pid:dict(pid=pid,cgroup="0::/foreign/not-own",start_ticks=444,argv=["foreign"]))
    namespace=dict(time=time,os=os,TOTAL=7200,DEADLINE=C.CUT,CLEANUP=180,C=C,require=C.require,
      R=types.SimpleNamespace(helper=lambda:types.SimpleNamespace(frozen=lambda:helper)),
      actual_hbm=lambda raw,card:{"physical":card,"used_mib":100},SMI="/usr/local/sbin/npu-smi")
    exec(compile(ast.Module(body=[node(source("MAIN_HOST.py"),"Control")],type_ignores=[]),"actual-control","exec"),namespace)
    ctl=namespace["Control"](Path("/not-created"))
    ctl.protected=before;ctl.owned=[dict(cid="a"*64,phase="tp4-capture")]
    ctl.current=ctl.owned[0]
    ctl.call=lambda *args:(dict(stdout="isolated hardware snapshot"),dict(path="/actual/smi",bytes=1,sha256="b"*64))
    def save(label,value):
        observed.append((label,copy.deepcopy(value)))
        return dict(path="/actual/"+label,bytes=1,sha256="c"*64)
    ctl.save=save
    return ctl,observed,real

def original_window_functions():
    manifest=json.loads((HERE/"SOURCE_MANIFEST.json").read_text())
    ns=dict(random=__import__("random"),struct=__import__("struct"),hashlib=hashlib,N=256,T=4096)
    for filename,names in (("io_contract.py",("require","pack_ids")),("build_inputs.py",("select_windows",))):
        row=next(x for x in manifest["dependencies"]if x["path"].endswith("skvq-calibration-capture-chain-v1-001/"+filename))
        p=Path(row["path"])
        if REVIEW:p=REVIEW/"skvq-calibration-capture-chain-v1-001"/filename
        raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row["sha256"]and raw.endswith(b"\n\n"):raw=raw[:-1]
        C.require(hashlib.sha256(raw).hexdigest()==row["sha256"],"actual unchanged donor sampling/packing bytes")
        body=[node(raw.decode(),name)for name in names]
        exec(compile(ast.Module(body=body,type_ignores=[]),str(p),"exec"),ns)
    return ns

class Aggregate(unittest.TestCase):
    def test01_compile_all_actual_own_sources(self):
        files=sorted(HERE.glob("*.py"));self.assertGreaterEqual(len(files),18)
        for p in files:compile(p.read_bytes(),str(p),"exec")
    def test02_strict_ref_real_bytes_and_bool_extra(self):
        with tempfile.TemporaryDirectory()as tmp:
            path=Path(tmp)/"actual.json";path.write_bytes(b'{"actual":1}\n')
            ref=C.reference(path.absolute());self.assertEqual(C.checked(ref),ref)
            for bad in (dict(ref,bytes=True),dict(ref,bytes=ref["bytes"]+1),dict(ref,origin="fake")):
                with self.assertRaises(ValueError):C.checked(bad)
    def test03_supported_configuration_and_same_literal(self):
        k=kwargs();self.assertEqual((k["max_model_len"],k["max_num_batched_tokens"],k["max_num_seqs"]),(4097,4096,1))
        self.assertIs(k["enable_chunked_prefill"],True);self.assertIs(k["enable_prefix_caching"],False)
        self.assertTrue(k["enforce_eager"]);self.assertEqual(k["compilation_config"],{"mode":0})
        self.assertIn("LLM(**kwargs())",source("capture_current.py"))
        self.assertIn("EngineArgs(**kwargs()).create_engine_config()",source("engine_config.py"))
    def test04_original_runtime_session_body_unchanged(self):
        dep=json.loads((HERE/"SOURCE_MANIFEST.json").read_text())["dependencies"]
        row=next(x for x in dep if x["path"].endswith("skvq-calibration-capture-chain-v1-001/runtime_capture.py"))
        path=Path(row["path"])
        if REVIEW:path=REVIEW/"skvq-calibration-capture-chain-v1-001/runtime_capture.py"
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row["sha256"]and raw.endswith(b"\n\n"):raw=raw[:-1]
        self.assertEqual(hashlib.sha256(raw).hexdigest(),row["sha256"])
        self.assertEqual(ast.dump(node(raw.decode(),"Session")),ast.dump(node(source("runtime_capture_current.py"),"Session")))
        for name in("arm_rpc","finish_rpc","restore_rpc"):
            self.assertEqual(ast.dump(node(raw.decode(),name)),ast.dump(node(source("runtime_capture_current.py"),name)))
        self.assertIn('s.enable_chunked_prefill is True',source("runtime_capture_current.py"))
        self.assertIn('extra.num_tokens==4096 and extra.pad_size==0',source("runtime_capture_current.py"))
    def test05_aggregate_real_positive_source_callable(self):
        b,p,br,pr=example();old=stage.C.clock
        try:
            stage.C.clock=lambda:{"protocol_ref":C.CLOCK,"portfolio_cutoff_epoch":C.CUT}
            v=stage.combine(b,p,{"sha256":"d"*64},br,pr)
        finally:stage.C.clock=old
        self.assertEqual(v["events"],16384);self.assertEqual(v["preprojection_K_raw_bytes"],32*C.GIB)
        self.assertIs(v["native_ready"],False);self.assertIs(v["model_ready"],False)
    def test06_aggregate_missing_and_cross_cohort_refused(self):
        b,p,br,pr=example()
        for field,value in(("events",16383),("preprojection_K_raw_bytes",0),("producer_ref",dict(p["producer_ref"],sha256="e"*64)),
            ("actual_original_V_equivalence_verified_for_captured_inputs_only",False),("model_ready",True)):
            wrong=dict(p);wrong[field]=value
            with self.assertRaises(ValueError):stage.combine(b,wrong,{"sha256":"d"*64},br,pr)
    def test07_stage_actual_two_independent_calls_not_candidate(self):
        run=node(source("consume_stage.py"),"run")
        calls=[ast.unparse(x.func)for x in ast.walk(run)if isinstance(x,ast.Call)]
        self.assertIn("baseline.consume",calls);self.assertIn("projection.consume",calls)
        self.assertIn("contracts.device_free",calls)
        text=source("consume_stage.py")
        self.assertNotIn("cluster_producer",text);self.assertNotIn("projection_tap_current",text)
    def test08_hbm_parser_memory_not_hbm(self):
        t="| Chip | Bus-Id | AICore(%) Memory-Usage(MB) HBM-Usage(MB) |\n| 4 910B4 | OK | 0 |\n| 0 | 0000:01:00.0 | 2 999/999 29696/32768 |"
        self.assertEqual(hbm.actual_hbm(t,4)["used_mib"],29696)
        with self.assertRaises(ValueError):hbm.actual_hbm(t.replace("29696/32768","29697/32768"),4)
        with self.assertRaises(ValueError):hbm.actual_hbm(t,0)
    def test09_real_owned_cpu_no_global_idle_and_n1_cid(self):
        ctrl=node(source("MAIN_HOST.py"),"Control")
        create=next(x for x in ctrl.body if isinstance(x,ast.FunctionDef)and x.name=="create")
        gates=[x for x in ast.walk(create)if isinstance(x,ast.If)and ast.unparse(x.test)=="npu"]
        self.assertTrue(any("self.observe()"in ast.unparse(x)for x in gates))
        cleanup=next(x for x in ctrl.body if isinstance(x,ast.FunctionDef)and x.name=="cleanup")
        self.assertTrue(any(isinstance(x,ast.If)and isinstance(x.test,ast.Subscript)and
            ast.dump(x.test)==ast.dump(ast.parse('self.current["npu"]',mode="eval").body)for x in ast.walk(cleanup)))
        call=next(x for x in ast.walk(node(source("MAIN_HOST.py"),"execute"))if isinstance(x,ast.Call)and
            isinstance(x.func,ast.Attribute)and x.func.attr=="exec"and x.args and isinstance(x.args[0],ast.Constant)and x.args[0].value=="all4-n1")
        self.assertIn("MAIN_OWNED_CID",ast.unparse(call));self.assertIn("--cpu-config-ref-json",ast.unparse(call))
    def test10_real_original_envelope_not_mock_schema(self):
        m=json.loads((HERE/"SOURCE_MANIFEST.json").read_text())
        ref=m["original_envelope_regression_ref"];path=Path(ref["path"])
        if REVIEW:path=REVIEW.parent/"skvq-envelope-review-015e.json"
        value=json.loads(path.read_text());argv=[value["operation"]["result"]["record"]["command"]]+value["operation"]["result"]["record"]["args"]
        self.assertEqual(whole.original(value,argv)["exitCode"],0)
        for change in("timedOut","cancelled"):
            wrong=copy.deepcopy(value);wrong["operation"]["result"]["record"][change]=True
            with self.assertRaises(ValueError):whole.original(wrong,argv)
        wrong=copy.deepcopy(value);wrong["terminal"]=False
        with self.assertRaises(ValueError):whole.original(wrong,argv)
        with self.assertRaises(ValueError):whole.original(value,argv+["changed"])
    def test11_no_deadline_reset_or_relabel_native(self):
        self.assertEqual(C.CUT,1791788425)
        text=source("MAIN_HOST.py");self.assertIn("DEADLINE=1791788425",text)
        self.assertIn("TOTAL=7200;CLEANUP=180",text)
        self.assertNotIn("DEADLINE=time.time()",text)
        self.assertIn("FULL_NATIVE_BASELINE_CAPTURE_CONSUMED_NOT_CALIBRATED",text)
        self.assertIn("native_ready=False,model_ready=False",text)
    def test12_actual_host_consumer_all_three_guest_budgets_and_fullpreK(self):
        text=source("consume_host.py")
        self.assertIn('(8 if i==0 else (64 if i==1 else 2))',text)
        self.assertIn('rs["disk_available_bytes"]>=320*2**30',text)
        self.assertIn('combine(base,pre,source',text)
        self.assertIn('actual_hbm(smi["stdout"],card)',text)
    def test13_real_partial_to_full_matcher_rejects_false_promotion(self):
        import engine_config as cfg
        src={"path":"/actual/source","bytes":1,"sha256":"f"*64}
        prior=dict(status="ACTUAL_DECLARED_SCHEDULER_CONFIG_CHECKED",source_ref=src,NPU_initialized=False,model_config_constructed=False,
            full_engine_config_verified=False,full_engine_config_required_at_N1=True,kwargs=kwargs(),
            runtime_origins={"actual":"same-source"},torch_origin={"sha256":"1"*64},
            torch_npu_origin={"sha256":"2"*64},effective={"max_num_batched_tokens":4096})
        full=dict(prior,status="ACTUAL_FULL_ENGINE_CONFIG_CHECKED",full_engine_config_verified=True,model_config_constructed=True,
            effective=dict(prior["effective"],compilation_mode="NONE"))
        cfg.match_partial(prior,full,src)
        for field,value in (("NPU_initialized",True),("full_engine_config_verified",True),
            ("status","ACTUAL_FULL_ENGINE_CONFIG_CHECKED"),("effective",{"max_num_batched_tokens":4095})):
            bad=copy.deepcopy(prior);bad[field]=value
            with self.assertRaises(ValueError):cfg.match_partial(bad,full,src)
        bad=copy.deepcopy(full);bad["kwargs"]["enable_chunked_prefill"]=False
        with self.assertRaises(ValueError):cfg.match_partial(prior,bad,src)
    def test14_actual_import_order_partial_CPU_full_only_after_all4(self):
        config=node(source("engine_config.py"),"construct")
        imports=[x for x in ast.walk(config)if isinstance(x,ast.Import)]
        explicit=next(x for x in imports if [n.name for n in x.names]==["torch","torch_npu"])
        accesses=[x.lineno for x in ast.walk(config)if isinstance(x,ast.Attribute)and
            isinstance(x.value,ast.Name)and x.value.id=="torch"and x.attr=="npu"]
        self.assertLess(explicit.lineno,min(accesses))
        conditional=next(x for x in config.body if isinstance(x,ast.If)and ast.unparse(x.test)=="full")
        self.assertIn("create_engine_config",ast.unparse(conditional.body[0]))
        self.assertIn("SchedulerConfig",ast.unparse(ast.Module(body=conditional.orelse,type_ignores=[])))
        self.assertNotIn("create_model_config",ast.unparse(ast.Module(body=conditional.orelse,type_ignores=[])))
        self.assertNotIn("create_engine_config",ast.unparse(ast.Module(body=conditional.orelse,type_ignores=[])))
        n1=node(source("n1_check.py"),"main")
        ready=next(x for x in ast.walk(n1)if isinstance(x,ast.Call)and x.args and
            any(isinstance(a,ast.Constant)and a.value=="actual all4 tiny completed"for a in x.args))
        fullcall=next(x for x in ast.walk(n1)if isinstance(x,ast.Call)and
            isinstance(x.func,ast.Name)and x.func.id=="construct")
        self.assertLess(ready.lineno,fullcall.lineno)
        self.assertEqual([(x.arg,ast.literal_eval(x.value))for x in fullcall.keywords],[("full",True)])
        self.assertIn("match_partial(cpu_config,cfg,source)",source("consume_host.py"))
    def test15_actual_worker_install_explicit_source_before_original_install(self):
        import os
        call=node(source("projection_tap_current.py"),"install_rpc")
        self.assertEqual(call.args.args[-1].arg,"current_manifest_sha256")
        observed=[];sha="a"*64
        class StopAtOriginal(Exception):pass
        def original(*args):
            observed.append(("original",args));raise StopAtOriginal()
        namespace=dict(require=C.require,os=os,ENV="SKVQ_TEST_EXPLICIT_ONLY",
            source_lock=lambda:observed.append(("source_lock",None))or{"sha256":sha},
            loader_bridge=types.SimpleNamespace(install_rpc=original))
        exec(compile(ast.Module(body=[call],type_ignores=[]),"actual-worker-install","exec"),namespace)
        old=C.configure;previous=os.environ.get("SKVQ_TEST_EXPLICIT_ONLY")
        try:
            C.configure=lambda value:observed.append(("configure",value))
            os.environ["SKVQ_TEST_EXPLICIT_ONLY"]="1"
            with self.assertRaises(StopAtOriginal):namespace["install_rpc"]("worker","inputs","out",sha)
        finally:
            C.configure=old
            if previous is None:os.environ.pop("SKVQ_TEST_EXPLICIT_ONLY",None)
            else:os.environ["SKVQ_TEST_EXPLICIT_ONLY"]=previous
        self.assertEqual(observed,[("configure",sha),("source_lock",None),("original",("worker","inputs","out"))])
        rpc=next(x for x in ast.walk(node(source("capture_current.py"),"run"))if isinstance(x,ast.Call)and
            isinstance(x.func,ast.Attribute)and x.func.attr=="collective_rpc"and x.args and
            isinstance(x.args[0],ast.Name)and x.args[0].id=="install_rpc")
        args=next(x.value for x in rpc.keywords if x.arg=="args")
        self.assertEqual(len(args.elts),3);self.assertIn("C.source()",ast.unparse(args.elts[-1]))

    def test16_real_protected_boundary_external_add_remove_restart(self):
        real=protected_real();before=[protected_row(),protected_row(334,1)]
        after=[protected_row(start=999),protected_row(335,2)]
        value=real.protected_boundary(before,after,["a"*64],[222])
        self.assertEqual(value["external_removed"],[before[1]])
        self.assertEqual(value["external_added"],[after[1]])
        self.assertEqual(value["external_changed"],[dict(before=before[0],after=after[0])])
        self.assertIs(value["own_on_protected"],False)
        self.assertIs(value["external_unchanged_claimed"],False)
        self.assertEqual(real.protected_boundary(before,[],["a"*64],[222])["external_removed"],before)
    def test17_real_protected_boundary_owned_PID_CID_refused(self):
        real=protected_real()
        for after in ([protected_row(222)],[protected_row(cgroup="0::/docker/"+"a"*64)]):
            with self.assertRaises(ValueError):real.protected_boundary([],after,["a"*64],[222])
        for before in ([protected_row(222)],[protected_row(cgroup="0::/docker/"+"a"*64)]):
            with self.assertRaises(ValueError):real.protected_boundary(before,[],["a"*64],[222])
    def test18_real_protected_boundary_malformed_duplicate_failclosed(self):
        real=protected_real();row=protected_row()
        for bad in ([row,row],[dict(row,physical=4)],[dict(row,start_ticks=0)],
          [dict(row,unknown=True)],[dict(row,cmdline_sha256="")],[dict(row,cgroup="")]):
            with self.assertRaises(ValueError):real.protected_boundary([],bad,["a"*64],[222])
        with self.assertRaises(ValueError):real.protected_boundary([],[],["short"],[222])
        with self.assertRaises(ValueError):real.protected_boundary([],[],["a"*64],[True])
    def test19_real_protected_loader_foreign_cached_namespace_refused(self):
        real=protected_real()
        from unittest.mock import patch
        fake=types.SimpleNamespace(__file__=str(HERE/"current_contract.py"))
        refs=C.PROTECTED_REFS
        if REVIEW:
            local=REVIEW.parent/"kivi-whole-consumer-reviewed-deps-20261010-001"
            refs=[dict(ref,path=str((local/name).absolute())) for ref,name in
              zip(refs,("protected_contract.py","protected_lifecycle.py"))]
        with patch.object(C,"PROTECTED_REFS",refs),patch.dict(sys.modules,{"once_contract":fake}):
            with self.assertRaises(ValueError):C.protected_module()
        self.assertIs(protected_real(),real)
    def test20_actual_Control_observe_external_churn_keeps_all4_idle_gate(self):
        before=[protected_row()];after=[protected_row(334,1)]
        ctl,observed,real=actual_control(before,after);old=C.protected_module
        try:
            C.protected_module=lambda:real
            ctl.observe()
        finally:C.protected_module=old
        self.assertEqual([x[1] for x in observed if x[0]=="idle"],[4,5,6,7])
        raw=next(v for name,v in observed if name=="PROTECTED")
        self.assertEqual(raw["boundary"]["external_removed"],before)
        self.assertEqual(raw["boundary"]["external_added"],after)
        final=next(v for name,v in observed if name=="OWNED_NPU_OBSERVATION")
        self.assertIn("protected_boundary_ref",final)
    def test21_actual_Control_observe_owned_protected_or_foreign4_rejected(self):
        import os
        for after,foreign in (([protected_row(os.getpid())],False),
          ([protected_row(cgroup="0::/docker/"+"a"*64)],False),([],True)):
            ctl,observed,real=actual_control([],after,foreign);old=C.protected_module
            try:
                C.protected_module=lambda:real
                with self.assertRaises(ValueError):ctl.observe(active=True)
            finally:C.protected_module=old
        self.assertNotIn("prot==self.protected",source("MAIN_HOST.py"))
    def test22_actual_consumer_protected_replay_and_tamper_refusal(self):
        real=protected_real();owned=[dict(cid="a"*64,phase="tp4-capture")];smi=dict(path="/actual/smi",bytes=1,sha256="b"*64)
        raw=dict(smi=smi,actual=[protected_row()],original=[],owned_cids=["a"*64],
          owned_host_pids=[222],current_cid="a"*64,current_phase="tp4-capture")
        raw["boundary"]=real.protected_boundary([],raw["actual"],raw["owned_cids"],[222])
        namespace=dict(C=C,require=C.require)
        exec(compile(ast.Module(body=[node(source("consume_host.py"),"consume_protected")],type_ignores=[]),"actual-consumer-boundary","exec"),namespace)
        old=C.protected_module
        try:
            C.protected_module=lambda:real
            self.assertEqual(namespace["consume_protected"](raw,[],owned,222,smi,True),raw["boundary"])
            for field,value in (("owned_cids",["d"*64]),("owned_host_pids",[333]),("smi",dict(smi,sha256="d"*64)),
              ("boundary",dict(raw["boundary"],external_added=[])),("current_phase","independent-consumer")):
                bad=copy.deepcopy(raw);bad[field]=value
                with self.assertRaises(ValueError):namespace["consume_protected"](bad,[],owned,222,smi,True)
        finally:C.protected_module=old

    def test23_actual_SchedulerConfig_required_InitVars_and_original_factory_call(self):
        manifest=json.loads((HERE/"SOURCE_MANIFEST.json").read_text())
        row=next(x for x in manifest["dependencies"]if x["path"].endswith("source-engine-config-660-20261010-001/scheduler.py"))
        path=Path(row["path"])
        if REVIEW:path=REVIEW.parent/"c152-native-config/scheduler.py"
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row["sha256"]and raw.endswith(b"\n\n"):raw=raw[:-1]
        self.assertEqual(hashlib.sha256(raw).hexdigest(),row["sha256"])
        definition=node(raw.decode(),"SchedulerConfig")
        required={x.target.id for x in definition.body if isinstance(x,ast.AnnAssign)and x.value is None and
          isinstance(x.annotation,ast.Subscript)and ast.unparse(x.annotation.value)=="InitVar"}
        self.assertEqual(required,{"max_model_len","is_encoder_decoder"})
        factory=next(x for x in definition.body if isinstance(x,ast.FunctionDef)and x.name=="default_factory")
        defaults={x.targets[0].slice.value:ast.literal_eval(x.value) for x in ast.walk(factory)if isinstance(x,ast.Assign)and
          isinstance(x.targets[0],ast.Subscript)and isinstance(x.targets[0].value,ast.Name)and x.targets[0].value.id=="kwargs"}
        self.assertIs(defaults["is_encoder_decoder"],False);self.assertIn("max_model_len",defaults)
        call=next(x for x in ast.walk(factory)if isinstance(x,ast.Call)and ast.unparse(x.func)=="SchedulerConfig")
        self.assertEqual([(k.arg,ast.unparse(k.value))for k in call.keywords],[(None,"kwargs")])
        partial=next(x for x in ast.walk(node(source("engine_config.py"),"construct"))if isinstance(x,ast.Call)and
          ast.unparse(x.func)=="SchedulerConfig.default_factory")
        actual={k.arg:ast.unparse(k.value)for k in partial.keywords}
        self.assertEqual(actual["max_model_len"],"engine.max_model_len")
        self.assertTrue(required<=set(actual)|set(defaults))
        self.assertNotIn("create_model_config",source("engine_config.py"))
        self.assertIn('"is_encoder_decoder":m.is_encoder_decoder',source("engine_config.py"))
        # This checks the actual source contract, not a mock installed runtime.
        with self.assertRaises(AssertionError):
            self.assertTrue(required<=set(actual)|(set(defaults)-{"is_encoder_decoder"}))

    def test24_actual_original_PLAN_and_SOURCE_INDEX_all9_same_identity(self):
        import mount_preflight as mp
        plan_path=mp.BASE/"training_plan.json";index_path=mp.TRAIN_INDEX
        if REVIEW:
            plan_path=REVIEW/"skvq-calibration-capture-chain-v1-001/training_plan.json"
            index_path=REVIEW.parent/"c154-skvq-writer-source/ACTUAL_TRAIN_SOURCE_INDEX.json"
        self.assertEqual(hashlib.sha256(plan_path.read_bytes()).hexdigest(),mp.PLAN_SHA)
        self.assertEqual(hashlib.sha256(index_path.read_bytes()).hexdigest(),mp.INDEX_SHA)
        plan=json.loads(plan_path.read_bytes());index=json.loads(index_path.read_bytes())
        self.assertEqual(len(plan["artifacts"]),9);self.assertEqual(len(index["artifacts"]),9)
        self.assertEqual(sum(a["size"]for a in plan["artifacts"]),110296287)
        for a,b in zip(plan["artifacts"],index["artifacts"]):
            self.assertTrue(all(b[k]==v for k,v in a.items()))
            rel=a["repository"].replace("/","--")+"/"+a["revision"]+"/"+a["path"]
            self.assertEqual(b["artifact_path"],mp.TRAIN_HOST.as_posix()+"/"+rel)
            self.assertEqual(a["split"],"train")
        self.assertNotEqual(str(mp.TRAIN_HOST),plan["root"])
        self.assertEqual(plan["root"],mp.TRAIN_GUEST)

    def test25_actual_regular_file_byte_hash_and_directory_refusal(self):
        import mount_preflight as mp
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp)/"real.bin";p.write_bytes(b"actual mount byte fence")
            r=mp.file_ref(p.absolute())
            self.assertEqual(r["bytes"],23);self.assertEqual(r["sha256"],hashlib.sha256(p.read_bytes()).hexdigest())
            with self.assertRaises(ValueError):mp.file_ref(Path(tmp).absolute())
            with self.assertRaises(FileNotFoundError):mp.file_ref(Path(tmp)/"missing")
            with self.assertRaises(ValueError):mp.ordinary(Path("relative"))

    def test26_actual_mount_scan_reports_precise_missing_src_dst(self):
        import mount_preflight as mp
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).absolute();good=root/"real";good.mkdir()
            mounts={"/actual/ro":(str(good),False),"/actual/missing":(str(root/"missing"),False)}
            rows,errors=mp.inspect_mounts(mounts)
            by_dst={r["dst"]:r for r in rows}
            self.assertTrue(by_dst["/actual/ro"]["checked"]);self.assertFalse(by_dst["/actual/missing"]["checked"])
            self.assertEqual(errors[0]["src"],str(root/"missing"));self.assertEqual(errors[0]["dst"],"/actual/missing")
            for dst,value in (("/actual,bad",(str(good),False)),("/actual/notbool",(str(good),1)),("/actual/../escape",(str(good),False))):
                with self.subTest(dst=dst):self.assertEqual(len(mp.inspect_mounts({dst:value})[1]),1)

    def test27_actual_mount_consumer_directory_growth_and_tamper(self):
        import mount_preflight as mp
        from unittest.mock import patch
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).absolute();data=root/"real.bin";data.write_bytes(b"original")
            mounts={mp.TRAIN_GUEST:(str(mp.TRAIN_HOST),False),"/actual/owned-out":(str(root),True),"/actual/ro":(str(data),False)}
            # This transparent training surrogate isolates the actual mount
            # replay; it is never a TRAIN/runtime receipt or calibration PASS.
            train=dict(passed=True,errors=[],fixture_only=True)
            actual_scan=mp.inspect_mounts
            def scan(m):
                subset={k:v for k,v in m.items()if k!=mp.TRAIN_GUEST}
                return actual_scan(subset)
            with patch.object(mp,"training",return_value=train),patch.object(mp,"inspect_mounts",side_effect=scan):
                value=mp.observe(mounts,"preflight",{"sha256":"a"*64})
                value=json.loads(json.dumps(value,sort_keys=True))
                mounts={k:tuple(v)for k,v in json.loads(json.dumps(mounts,sort_keys=True)).items()}
                (root/"new-log").write_bytes(b"directory grows")
                self.assertEqual(mp.consume(value,mounts,"preflight",{"sha256":"a"*64}),value)
                for change in ("src","identity","extra","source"):
                    bad=copy.deepcopy(value)
                    if change=="src":bad["mounts"][0]["src"]+="changed"
                    elif change=="identity":bad["mounts"][0]["identity"]["ino"]+=1
                    elif change=="extra":bad["origin"]="unverified"
                    else:bad["current_source_ref"]={"sha256":"b"*64}
                    with self.assertRaises(ValueError):mp.consume(bad,mounts,"preflight",{"sha256":"a"*64})
                data.write_bytes(b"mutated")
                with self.assertRaises(ValueError):mp.consume(value,mounts,"preflight",{"sha256":"a"*64})

    def test28_actual_Control_mounts_explicit_old_guest_new_host_no_alias(self):
        import mount_preflight as mp
        ctrl=node(source("MAIN_HOST.py"),"Control")
        method=next(x for x in ctrl.body if isinstance(x,ast.FunctionDef)and x.name=="mounts")
        text=ast.unparse(method)
        self.assertIn("m[TRAIN_GUEST] = (str(TRAIN), False)",text)
        self.assertNotIn("MODEL, TRAIN, LINEAR",text)
        tree=ast.parse(source("MAIN_HOST.py"))
        values={x.targets[0].id:ast.unparse(x.value)for x in tree.body if isinstance(x,ast.Assign)and
            isinstance(x.targets[0],ast.Name)}
        self.assertEqual(values["TRAIN"],'Path("/cache/cch/qwen36-damp-20261006/calibration-inputs/source-v2")'.replace('"',"'"))
        self.assertEqual(values["TRAIN_GUEST"],repr(mp.TRAIN_GUEST))
        self.assertEqual(values["MODEL"],"Path('/cache/efim/Qwen3.6-27B')")
        self.assertIn("input_entry.py",source("inside_cpu.py"))
        self.assertIn('runpy.run_path(str(D.BASE/"build_inputs.py"),run_name="__main__")',source("input_entry.py"))

    def test29_actual_Control_create_preflight_first_refusal_no_Docker(self):
        import mount_preflight as mp,os,time
        ctrl=node(source("MAIN_HOST.py"),"Control")
        namespace=dict(time=time,os=os,json=json,TOTAL=7200,DEADLINE=C.CUT,CLEANUP=180,GIB=C.GIB,C=C,require=C.require,
            R=types.SimpleNamespace(fresh=lambda *args:dict(disk_available_bytes=8*C.GIB,allocation={"guest_cpus":[1,2,3,4]})),
            M=mp,OWNER="skvq-current72h-preprojection-v1-006",DOCKER="/usr/bin/docker",
            closure=lambda:dict(sha256="a"*64))
        exec(compile(ast.Module(body=[ctrl],type_ignores=[]),"actual-Control-create","exec"),namespace)
        ctl=namespace["Control"](Path("/not-created"));saved=[];calls=[]
        ctl.save=lambda label,v:(saved.append((label,v))or{"path":"/raw/"+label,"bytes":1,"sha256":"b"*64})
        ctl.mounts=lambda *args:{mp.TRAIN_GUEST:(str(mp.TRAIN_HOST),False),"/actual/missing":("/definitely-missing-skvq",False)}
        ctl.devices=lambda *args:{};ctl.env=lambda *args:{}
        ctl.call=lambda *args: calls.append(args)
        from unittest.mock import patch
        # Actual missing path scanner executes; no surrogate positive evidence.
        with patch.object(mp,"training",return_value=dict(errors=[{"src":str(mp.TRAIN_HOST),"dst":mp.TRAIN_GUEST,"error":"local runtime data unavailable"}],passed=False)):
            with self.assertRaisesRegex(ValueError,"exact mount/TRAIN preflight refusal"):ctl.create("preflight",False,8*C.GIB)
        self.assertEqual(calls,[]);self.assertIsNone(ctl.current)
        raw=next(v for label,v in saved if label=="EXACT_MOUNT_TRAIN_PREFLIGHT")
        self.assertIs(raw["passed"],False)
        self.assertTrue(any(e["src"]=="/definitely-missing-skvq"and e["dst"]=="/actual/missing"for e in raw["errors"]))

    def test30_real_create_and_whole_consumer_both_require_same_preflight(self):
        ctrl=node(source("MAIN_HOST.py"),"Control")
        create=next(x for x in ctrl.body if isinstance(x,ast.FunctionDef)and x.name=="create")
        calls=[(x.lineno,ast.unparse(x.func))for x in ast.walk(create)if isinstance(x,ast.Call)]
        check=next(n for n,f in calls if f=="M.observe")
        docker=next(x.lineno for x in ast.walk(create)if isinstance(x,ast.Call)and ast.unparse(x.func)=="self.call")
        self.assertLess(check,docker)
        self.assertIn('e["mount_preflight_ref"]',source("consume_host.py"))
        consume=node(source("consume_host.py"),"consume")
        self.assertTrue(any(isinstance(x,ast.Call)and ast.unparse(x.func)=="M.consume"for x in ast.walk(consume)))
        main=node(source("mount_preflight.py"),"main")
        self.assertNotIn("subprocess",source("mount_preflight.py"))
        self.assertNotIn("torch",source("mount_preflight.py").splitlines()[1:])
        self.assertIn("MOUNT_TRAIN_PREFLIGHT_ONLY",ast.unparse(main))

    def test31_actual_EngineArgs_dict_normalization_and_common_LLMPipeline(self):
        manifest=json.loads((HERE/"SOURCE_MANIFEST.json").read_text())
        row=next(x for x in manifest["dependencies"]if x["path"].endswith("native009-public-graph-and-engine-source-v1-001/arg_utils.py"))
        path=Path(row["path"])
        if REVIEW:path=REVIEW.parent/"c152-native-config/arg_utils.py"
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row["sha256"]and raw.endswith(b"\n\n"):raw=raw[:-1]
        self.assertEqual(hashlib.sha256(raw).hexdigest(),row["sha256"])
        cls=node(raw.decode(),"EngineArgs")
        post=next(x for x in cls.body if isinstance(x,ast.FunctionDef)and x.name=="__post_init__")
        first=post.body[0]
        self.assertEqual(ast.unparse(first.test),"isinstance(self.compilation_config, dict)")
        assignment=first.body[0]
        self.assertEqual(ast.unparse(assignment),"self.compilation_config = CompilationConfig(**self.compilation_config)")
        self.assertEqual(kwargs()["compilation_config"],{"mode":0})
        self.assertIn("EngineArgs(**kwargs()).create_engine_config()",source("engine_config.py"))
        self.assertIn("LLM(**kwargs())",source("capture_current.py"))
        # Actual runtime constructor and fullEngine validation remain CPU/N1 gates;
        # this test does not stub them or grant model/configuration authority.

    def test32_actual_original_seed42_fixture_duplicate_is_correctly_rejected(self):
        ns=original_window_functions()
        rng=ns["random"].Random(42);starts=[rng.randint(0,65536-4096-1)for _ in range(256)]
        repeated=next((i,starts.index(start),start)for i,start in enumerate(starts)if start in starts[:i])
        self.assertEqual(repeated,(226,174,10016))
        with self.assertRaisesRegex(ValueError,"seed42 yielded duplicate full input; no resampling"):
            ns["select_windows"](list(range(65536)),[{"pool_start":0,"pool_stop":65536}])

    def test33_actual_corrected_full15_positive_method_calls_unchanged_sampler(self):
        ns=original_window_functions()
        ns.update(unittest=unittest)
        cls=node(source("SOFTWARE_TESTS_15.py"),"InputTests")
        exec(compile(ast.Module(body=[cls],type_ignores=[]),"actual-corrected-InputTests","exec"),ns)
        # Run the genuine full256 positive method; not a substitute sampler or a tiny input.
        case=ns["InputTests"]("test_full256_window_scheduler_fixture")
        case.test_full256_window_scheduler_fixture()
        rng=ns["random"].Random(42);starts=[rng.randint(0,131072-4096-1)for _ in range(256)]
        self.assertEqual(len(set(starts)),256)
        self.assertTrue(all(0<=start<131072-4096 for start in starts))

    def test34_actual_sampler_keeps_repeated_full_input_short_pool_and_vocab_rejections(self):
        ns=original_window_functions()
        with self.assertRaisesRegex(ValueError,"seed42 yielded duplicate full input; no resampling"):
            ns["select_windows"]([1]*131072,[{"pool_start":0,"pool_stop":131072}])
        with self.assertRaises(ValueError):
            ns["select_windows"](list(range(4096)),[{"pool_start":0,"pool_stop":4096}])
        for invalid in ([248320],[-1],[True]):
            with self.assertRaises(ValueError):ns["pack_ids"](invalid)

    def test35_actual_complete15_body_single_fixture_diff_and_real_CPU_consumer_edges(self):
        manifest=json.loads((HERE/"SOURCE_MANIFEST.json").read_text())
        row=next(x for x in manifest["dependencies"]if x["path"].endswith("skvq-calibration-capture-chain-v1-001/SOFTWARE_TESTS.py"))
        p=Path(row["path"])
        if REVIEW:p=REVIEW/"skvq-calibration-capture-chain-v1-001/SOFTWARE_TESTS.py"
        raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row["sha256"]and raw.endswith(b"\n\n"):raw=raw[:-1]
        self.assertEqual(hashlib.sha256(raw).hexdigest(),row["sha256"])
        original=ast.parse(raw.decode());corrected=ast.parse(source("SOFTWARE_TESTS_15.py"))
        oldclasses=[x for x in original.body if isinstance(x,ast.ClassDef)]
        newclasses=[x for x in corrected.body if isinstance(x,ast.ClassDef)]
        all_methods=lambda classes:[x.name for cls in classes for x in cls.body if isinstance(x,ast.FunctionDef)and x.name.startswith("test_")]
        self.assertEqual(all_methods(oldclasses),all_methods(newclasses));self.assertEqual(len(all_methods(newclasses)),15)
        target=next(x for cls in newclasses for x in cls.body if isinstance(x,ast.FunctionDef)and x.name=="test_full256_window_scheduler_fixture")
        constants=[x for x in ast.walk(target.body[0])if isinstance(x,ast.Constant)and x.value==131072]
        self.assertEqual(len(constants),1);constants[0].value=65536
        self.assertEqual([ast.dump(x)for x in oldclasses],[ast.dump(x)for x in newclasses])
        inside=node(source("inside_cpu.py"),"run");text=ast.unparse(inside)
        self.assertIn("(HERE, 'SOFTWARE_TESTS_15.py', 15)",text)
        self.assertIn("(ORDER, 'SOFTWARE_TESTS.py', 8)",text)
        self.assertIn("source=reference(root / name)",text)
        consumer=node(source("consume_host.py"),"consume");text=ast.unparse(consumer)
        self.assertIn("r['source'] == expected",text)
        self.assertIn("SOFTWARE_TESTS_15.py",text)
        self.assertIn("skvq-tp4-qkv-loader-order-v1-001/SOFTWARE_TESTS.py",text)

    def test36_actual_MAIN_HOST_newroot_receives_exact_ENTRY_output_in_real_sandbox(self):
        import os,re
        entry=json.loads((HERE/"ENTRY.json").read_text())
        output=entry["host"]["output"];source_root=entry["source"]["path"].rsplit("/",1)[0]
        self.assertEqual(output,entry["host"]["argv"][-1])
        calls=[]
        with tempfile.TemporaryDirectory()as temporary:
            sandbox=Path(temporary).absolute();source_here=sandbox/Path(source_root).name
            def mapped(value):
                # Only the declared Linux lowbit direct children are relocated for this
                # real filesystem test. Production Path/body/ENTRY argv remain unchanged.
                original=Path(value)
                lowbit=Path(source_root).parent
                if original.parent==lowbit:
                    calls.append(str(value));return sandbox/original.name
                raise ValueError("outside declared lowbit sandbox mapping")
            ns=dict(Path=mapped,HERE=source_here,re=re,require=C.require)
            function=node(source("MAIN_HOST.py"),"newroot")
            exec(compile(ast.Module(body=[function],type_ignores=[]),"actual-MAIN_HOST.newroot","exec"),ns)
            result=ns["newroot"](output)
            self.assertTrue(result.is_dir());self.assertEqual(result.name,Path(output).name)
            self.assertEqual(calls,[output])
            with self.assertRaises(ValueError):ns["newroot"](output)
            for prefix in("run-skvq-current72h-projection-003-","run-skvq-current72h-projection-004-","run-skvq-current72h-projection-005-","run-kivi-model-firstdecode-"):
                candidate=str(Path(source_root).parent/(prefix+"negative"))
                with self.assertRaises(ValueError):ns["newroot"](candidate)
                self.assertFalse((sandbox/Path(candidate).name).exists())
            with self.assertRaises(ValueError):ns["newroot"]("/cache/foreign/run-skvq-current72h-projection-006-foreign")
            # All actual writes stay under the test-owned Temp sandbox; target is untouched.
            self.assertTrue(result.parent==sandbox)

    def test37_real_ENTRY_source_owner_consumer_and_output_paths_are_single_current_identity(self):
        entry=json.loads((HERE/"ENTRY.json").read_text());m=json.loads((HERE/"SOURCE_MANIFEST.json").read_text())
        current=m["root"];owner="skvq-current72h-preprojection-v1-006"
        self.assertEqual(entry["source"]["path"],current+"/SOURCE_MANIFEST.json")
        self.assertEqual(current,C.ROOT.as_posix())
        self.assertEqual(entry["host"]["output"],(Path(current).parent/"run-skvq-current72h-projection-006-main-20261010-001").as_posix())
        for role,script in(("software","software_check.py"),("host","MAIN_HOST.py"),("whole","consume_whole.py"),("preflight","mount_preflight.py")):
            self.assertIn(current+"/"+script,entry[role]["argv"])
            self.assertIn(entry["source"]["sha256"],entry[role]["argv"])
        self.assertIn("OWNER="+repr(owner).replace("'",'"'),source("MAIN_HOST.py"))
        self.assertIn('=="'+owner+'"',source("consume_host.py"))
        self.assertIn('str(C.ROOT/"MAIN_HOST.py")',source("consume_whole.py"))
        for n in("current_contract.py","MAIN_HOST.py","consume_host.py","consume_whole.py","inside_cpu.py","mount_preflight.py"):
            self.assertNotIn("skvq-preprojection-current72h-v1-003",source(n))
            self.assertNotIn("skvq-preprojection-current72h-v1-004",source(n))
            self.assertNotIn("skvq-preprojection-current72h-v1-005",source(n))
        self.assertIn("SOFTWARE_TESTS_15.py",source("inside_cpu.py"))
        self.assertIn('reference(root/name)',source("inside_cpu.py"))

    def test38_actual_mount_preflight_main_accepts_ENTRY_and_rejects_old_outputs(self):
        import contextlib,io,re
        from unittest.mock import patch
        import mount_preflight as mp
        entry=json.loads((HERE/"ENTRY.json").read_text())
        output=entry["preflight"]["output"];args=entry["preflight"]["argv"]
        self.assertEqual(output,args[-1])
        manifest_root=entry["source"]["path"].rsplit("/",1)[0]
        # Execute the entire unchanged production main AST. Only absolute Linux
        # paths and unavailable deployment bindings are explicit local surrogates;
        # no target file, TRAIN authority, container, or runtime PASS is produced.
        with tempfile.TemporaryDirectory()as temporary:
            sandbox=Path(temporary).absolute();here=sandbox/Path(manifest_root).name
            data=sandbox/"actual-source.bin";data.write_bytes(b"local exact bytes")
            calls=[];published=[]
            def mapped(value):
                p=Path(value)
                if p.parent==Path(manifest_root).parent:return sandbox/p.name
                raise ValueError("outside declared lowbit sandbox mapping")
            mounts={mp.TRAIN_GUEST:(str(mp.TRAIN_HOST),False),"/actual/source":(str(data),False)}
            class LocalControl:
                def __init__(self,path):self.path=path
                def mounts(self,npu):calls.append(npu);return mounts
            def publish(path,value):
                with path.open("xb")as f:f.write(json.dumps(value,sort_keys=True).encode()+b"\n")
                published.append(path)
                return dict(path=str(path),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            module=types.ModuleType("MAIN_HOST");module.Control=LocalControl
            publisher=types.ModuleType("io_contract");publisher.publish_json=publish
            ns=dict(argparse=argparse,Path=mapped,HERE=here,re=re,sys=sys,json=json,
                require=mp.require,ordinary=mp.ordinary,observe=mp.observe)
            exec(compile(ast.Module(body=[node(source("mount_preflight.py"),"main")],type_ignores=[]),
                "actual-mount_preflight.main","exec"),ns)
            actual_scan=mp.inspect_mounts
            def scan(value):return actual_scan({k:v for k,v in value.items()if k!=mp.TRAIN_GUEST})
            training=dict(passed=True,errors=[],fixture_only=True)
            source_ref=entry["source"];saved_path=list(sys.path)
            try:
                with patch.dict(sys.modules,{"MAIN_HOST":module,"io_contract":publisher}),\
                     patch.object(C,"configure",return_value=source_ref),\
                     patch.object(mp,"training",return_value=training),\
                     patch.object(mp,"inspect_mounts",side_effect=scan):
                    with patch.object(sys,"argv",["mount_preflight.py","--execute","--source-manifest-sha256",source_ref["sha256"],"--output",output]),contextlib.redirect_stdout(io.StringIO()):
                        ns["main"]()
                    self.assertEqual(calls,[False,True]);self.assertEqual(len(published),2)
                    for p,phase in zip(published,("preflight","tp4-capture")):
                        value=json.loads(p.read_bytes())
                        self.assertEqual(mp.consume(value,mounts,phase,source_ref),value)
                    for prefix in("run-skvq-mount-preflight-003-","run-skvq-mount-preflight-004-","run-skvq-mount-preflight-005-","run-kivi-"):
                        wrong=(Path(manifest_root).parent/(prefix+"negative")).as_posix()
                        with patch.object(sys,"argv",["mount_preflight.py","--execute","--source-manifest-sha256",source_ref["sha256"],"--output",wrong]):
                            with self.assertRaisesRegex(ValueError,"explicit absent same-lowbit preflight root"):ns["main"]()
                        self.assertFalse((sandbox/Path(wrong).name).exists())
                    self.assertEqual(calls,[False,True])
            finally:sys.path[:]=saved_path


def main():
    global REVIEW
    ap=argparse.ArgumentParser();ap.add_argument("--review-root",type=Path);a=ap.parse_args();REVIEW=a.review_root
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Aggregate)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful()else 1
if __name__=="__main__":sys.exit(main())
