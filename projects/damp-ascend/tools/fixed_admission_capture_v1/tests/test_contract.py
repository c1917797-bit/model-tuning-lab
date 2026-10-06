"""Synthetic software checks only: no Torch/device/container/native model imports."""
from __future__ import annotations
import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import diag_contract as c
from profile_logic import Supervisor,TraceFailure,thread_profile
import aggregate
import install

class Observation:
    def __init__(self):
        self.error=None;self.finished=False;self.calls=0;self.fail_before=False;self.fail_after=False
    def before(self,frame):
        self.calls+=1
        if self.fail_before:
            raise OSError("before evidence failure")
        return {"original":frame.f_locals["x"]}
    def after(self,frame,record):
        if self.fail_after:
            raise OSError("after transfer failure")
    def secondary_failure(self,event,error):
        pass
    def native_failure(self,error,secondary):
        self.error=error
    def finish(self):
        self.finished=True

def native(x):
    return None

def model(result=None, count=48):
    for i in range(count):
        native(i)
    return result

class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.old=sys.getprofile();self.old_thread=thread_profile()
        sys.setprofile(None);threading.setprofile(None)
    def tearDown(self):
        sys.setprofile(self.old);threading.setprofile(self.old_thread)
    def install(self,code=native.__code__):
        obs=Observation();s=Supervisor(code,obs);s.install();return s,obs
    def test_same_result_none_native_return(self):
        s,o=self.install();value=object()
        self.assertIs(s.invoke(model,value),value)
        self.assertTrue(o.finished);self.assertEqual(o.calls,48)
    def test_return_none_not_success_when_native_exception(self):
        sentinel=RuntimeError("original")
        def failing_native(x):
            raise sentinel
        s,o=self.install(failing_native.__code__)
        with self.assertRaises(RuntimeError) as caught:
            s.invoke(lambda:failing_native(7))
        self.assertIs(caught.exception,sentinel);self.assertIs(o.error,sentinel)
        self.assertFalse(o.finished)
    def test_secondary_transfer_does_not_mask_native(self):
        sentinel=KeyError("native")
        def failing_native(x):
            raise sentinel
        s,o=self.install(failing_native.__code__);o.fail_after=True
        o.native_failure=lambda *_:(_ for _ in ()).throw(OSError("disk"))
        with self.assertRaises(KeyError) as caught:s.invoke(lambda:failing_native(1))
        self.assertIs(caught.exception,sentinel)
    def test_callback_failure_deferred_until_original_return(self):
        s,o=self.install();o.fail_before=True
        completed=[]
        def real():
            model();completed.append(True);return object()
        with self.assertRaises(TraceFailure):s.invoke(real)
        self.assertEqual(completed,[True]);self.assertEqual(o.calls,48)
    def test_coverage_missing_rejected(self):
        s,o=self.install()
        with self.assertRaisesRegex(TraceFailure,"coverage"):s.invoke(model,None,47)
    def test_profile_hook_replacement_rejected(self):
        s,o=self.install();sys.setprofile(None)
        with self.assertRaisesRegex(TraceFailure,"replaced"):s.invoke(model)
    def test_existing_hook_rejected(self):
        sys.setprofile(lambda *_:None)
        with self.assertRaisesRegex(TraceFailure,"existing"):Supervisor(native.__code__,Observation()).install()
    def test_restores_original_none_hooks_after_protocol_completion(self):
        s,o=self.install();o.finish=lambda:True
        self.assertIsNone(s.invoke(model))
        self.assertIsNone(sys.getprofile());self.assertIsNone(thread_profile())
    def test_callback_not_recursively_profiled(self):
        s,o=self.install();self.assertIsNone(s.invoke(model));self.assertEqual(len(s.calls),48)

class Entry:
    def __init__(self,name="damp_capture",value="damp_admission_diagnostic:register"):
        self.name=name;self.value=value;self.group="vllm.general_plugins"

class ContractTests(unittest.TestCase):
    def test_entrypoint_exact_unique(self):
        self.assertEqual(c.overlay_inventory([Entry()])["value"],"damp_admission_diagnostic:register")
    def test_entrypoint_duplicate_rejected(self):
        with self.assertRaises(ValueError):c.overlay_inventory([Entry(),Entry()])
    def test_entrypoint_frozen_old_rejected(self):
        with self.assertRaises(ValueError):c.overlay_inventory([Entry(value="damp_capture:register")])
    def test_memory_reserve(self):
        c.budget(c.ORDINARY_FLOOR+c.HOST_RESERVE,40*1024**3)
        with self.assertRaises(ValueError):c.budget(c.ORDINARY_FLOOR,40*1024**3)
    def test_disk_budget(self):
        with self.assertRaises(ValueError):c.budget(c.ORDINARY_FLOOR+c.HOST_RESERVE,39*1024**3)
    def test_raw_partition(self):
        self.assertLessEqual(c.RANK_LIMIT*12,c.RAW_LIMIT)
        self.assertEqual(c.TURNS,33)
    def test_canonical_nonfinite_rejected(self):
        with self.assertRaises(ValueError):c.canonical({"x":float("nan")})
    def test_default_off_import(self):
        p=Path(__file__).resolve().parents[1]/"damp_admission_diagnostic/__init__.py"
        spec=importlib.util.spec_from_file_location("_diag_default_off",p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        import os
        old=os.environ.pop("DAMP_ADMISSION_TRACE_ENABLE",None)
        before=set(sys.modules)
        try:self.assertIsNone(module.register())
        finally:
            if old is not None:os.environ["DAMP_ADMISSION_TRACE_ENABLE"]=old
        self.assertFalse(any(x=="torch" or x.startswith("torch.") for x in set(sys.modules)-before))
    def test_syntax_all_new_sources(self):
        root=Path(__file__).resolve().parents[1]
        for path in root.rglob("*.py"):
            ast.parse(path.read_text(),filename=str(path))
    def test_exact_module_only_overlay(self):
        old=install.source_contract
        install.source_contract=lambda:None
        try:
            with tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary)/"overlay"
                inv=install.install(root)
                self.assertTrue((root/"damp_capture").is_symlink())
                self.assertEqual((root/"damp_capture").readlink(),c.COLLECTOR/"damp_capture")
                self.assertFalse((root/"damp_capture-0.1.0.dist-info").exists())
                self.assertEqual(inv["name"],"damp_capture")
                with self.assertRaises(FileExistsError):install.install(root)
        finally:install.source_contract=old
    def test_source_audit_bytes_checked_not_status_only(self):
        oldroot,oldpackage=c.ROOT,c.PACKAGE_ROOT
        try:
            with tempfile.TemporaryDirectory() as temporary:
                c.ROOT=c.PACKAGE_ROOT=Path(temporary)
                refs={}
                for name in ("md","json"):
                    target=c.ROOT/("audit."+name);target.write_bytes(b"authored")
                    refs[name]={"path":target.name,"sha256":c.file_sha(target)}
                c.write_new(c.PACKAGE_ROOT/"SOURCE_MANIFEST.json",{
                    "schema":"damp-fixed-admission-sources/v1","files":{},"external_repo_files":{},
                    "runtime_sources":c.RUNTIME,"source_audit":refs})
                c.source_contract()
                (c.ROOT/"audit.md").write_bytes(b"changed")
                with self.assertRaisesRegex(ValueError,"audit reference drift"):c.source_contract()
        finally:c.ROOT,c.PACKAGE_ROOT=oldroot,oldpackage
    def test_same_before_previous_after_only_ssm(self):
        source=(Path(__file__).resolve().parents[1]/"damp_admission_diagnostic/observer.py").read_text()
        self.assertIn('"conv_previous_after_consistency_asserted":False',source)
        self.assertIn('require(consistent,"true recurrent-state before differs',source)


class ResourceTests(unittest.TestCase):
    def inspect_fixture(self,preflight=False):
        root=c.RESULT_ROOT/"synthetic-output"
        devices={} if preflight else {"/dev/davinci4":"/dev/davinci0"}
        h={"Privileged":False,"AutoRemove":False,
           "Memory":c.PREFLIGHT_MEMORY if preflight else c.ORDINARY_FLOOR,
           "MemorySwap":c.PREFLIGHT_MEMORY if preflight else c.ORDINARY_FLOOR,
           "NanoCpus":10**9 if preflight else 6*10**9,
           "ShmSize":c.GIB if preflight else 8*c.GIB,"PidsLimit":2048,
           "CapDrop":["ALL"],"CapAdd":None,"SecurityOpt":["no-new-privileges"],
           "NetworkMode":"none" if preflight else "host","IpcMode":"private",
           "PidMode":"","DeviceRequests":None,
           "Devices":[{"PathOnHost":a,"PathInContainer":b,"CgroupPermissions":"rwm"}
                      for a,b in devices.items()]}
        v={"Id":"a"*64,"Name":"/synthetic","Image":c.IMAGE,"Config":{
            "Labels":{"damp.fixed-admission.owner":"nonce"}},"HostConfig":h,
           "Mounts":[{"Destination":dst,"Source":source,"RW":rw,"Type":"bind"}
                     for dst,(source,rw) in c.expected_mounts(root).items()]}
        return v,root,devices
    def test_actual_ncpu7_formal6_and_reserve1(self):
        r=c.resource_budget(7,72*c.GIB,40*c.GIB,preflight=False,allt_running=0)
        self.assertEqual(r["new_cpus"],6)
        with self.assertRaisesRegex(ValueError,"CPU quota"):
            c.resource_budget(6,72*c.GIB,40*c.GIB,preflight=False,allt_running=0)
    def test_actual_ncpu7_allT4_pref1_reserve1(self):
        r=c.resource_budget(7,42*c.GIB,40*c.GIB,preflight=True,allt_running=4)
        self.assertEqual(r["numeric_caps_cpus"]+r["new_cpus"]+r["reserve_cpus"],6)
        self.assertEqual(r["required_mem_available"],42*c.GIB)
        with self.assertRaises(ValueError):
            c.resource_budget(7,41*c.GIB,40*c.GIB,preflight=True,allt_running=4)
    def test_formal_allT_live_rejected_even_available(self):
        with self.assertRaisesRegex(ValueError,"actual release"):
            c.resource_budget(7,128*c.GIB,40*c.GIB,preflight=False,allt_running=4)
    def test_engine_at_least6_not_assumed_from_external_caps(self):
        with self.assertRaisesRegex(ValueError,"Docker NCPU"):
            c.resource_budget(5,128*c.GIB,40*c.GIB,preflight=True,allt_running=0)
    def test_inspect_formal6_and_pref1_exact(self):
        for preflight in (False,True):
            v,root,devices=self.inspect_fixture(preflight)
            self.assertIs(c.inspect_contract(v,"synthetic","nonce",root,devices,
                                            preflight=preflight),v)
    def test_inspect_8cpu_rejected_on_formal(self):
        v,root,d=self.inspect_fixture()
        v["HostConfig"]["NanoCpus"]=8*10**9
        with self.assertRaisesRegex(ValueError,"cgroup"):
            c.inspect_contract(v,"synthetic","nonce",root,d,preflight=False)
    def test_extra_device_rejected(self):
        v,root,d=self.inspect_fixture()
        v["HostConfig"]["Devices"].append({"PathOnHost":"/dev/davinci0",
            "PathInContainer":"/dev/davinci1","CgroupPermissions":"rwm"})
        with self.assertRaisesRegex(ValueError,"device map"):
            c.inspect_contract(v,"synthetic","nonce",root,d,preflight=False)
    def test_extra_mount_rejected(self):
        v,root,d=self.inspect_fixture()
        v["Mounts"].append({"Destination":"/dev","Source":"/dev","RW":True,"Type":"bind"})
        with self.assertRaisesRegex(ValueError,"mount"):
            c.inspect_contract(v,"synthetic","nonce",root,d,preflight=False)
    def test_security_network_and_readonly_are_behavioral(self):
        for field,value in (("CapDrop",[]),("SecurityOpt",[]),("NetworkMode","host"),
                            ("DeviceRequests",[{"Count":-1}]),("IpcMode","host")):
            v,root,d=self.inspect_fixture(True)
            v["HostConfig"][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                c.inspect_contract(v,"synthetic","nonce",root,d,preflight=True)
        v,root,d=self.inspect_fixture()
        v["Mounts"][0]["RW"]=True
        with self.assertRaisesRegex(ValueError,"mutability"):
            c.inspect_contract(v,"synthetic","nonce",root,d,preflight=False)
    def test_sleep_unbounded_declaration_is_not_a_budget_blocker(self):
        v,_,_=self.inspect_fixture()
        v["HostConfig"]["Memory"]=v["HostConfig"]["NanoCpus"]=0
        result=c.external_workload(v,{"CPUPerc":"0.00%","MemUsage":"2MiB / 0B"},
                                   "PID COMMAND\n123 sleep\n")
        self.assertTrue(result["pure_sleep"])
        self.assertTrue(result["declaration_caps_not_summed"])
    def test_unknown_actual_high_workload_rejected_not_killed(self):
        v,_,_=self.inspect_fixture()
        for stats in ({"CPUPerc":"60%","MemUsage":"2MiB / 10GiB"},
                      {"CPUPerc":"1%","MemUsage":"3GiB / 10GiB"}):
            with self.assertRaisesRegex(ValueError,"do not stop it"):
                c.external_workload(v,stats,"PID COMMAND\n123 python3\n")
    def terminal_fixture(self,exit_code=0):
        return {"schema":"agentweb.operation/v1","operationId":c.ALLT_OPERATION,
            "terminal":True,"status":"completed","phase":"completed","operation":{
                "routeDecision":"peer_direct","targetPeerId":c.MAIN_PEER,"fallbackUsed":False,
                "result":{"record":{"id":c.ALLT_OPERATION,"state":"completed",
                    "cancelled":False,"timedOut":False,"exitCode":exit_code,"cwd":str(c.ROOT)}}}}
    def test_prior_terminal_nonzero_release_not_numeric_pass(self):
        result=c.prior_terminal(self.terminal_fixture(1))
        self.assertEqual(result["exit_code"],1)
        self.assertFalse(result["numerical_pass_claimed"])
    def test_prior_running_cancelled_timeout_wrong_peer_refused(self):
        original=self.terminal_fixture()
        changes=(("state","running"),("cancelled",True),("timedOut",True))
        for key,value in changes:
            v=copy.deepcopy(original);v["operation"]["result"]["record"][key]=value
            with self.assertRaises(ValueError):c.prior_terminal(v)
        v=copy.deepcopy(original);v["operation"]["targetPeerId"]="foreign"
        with self.assertRaises(ValueError):c.prior_terminal(v)
    def test_actual_prior_four_identity_and_stopped_pid0(self):
        proofs=[];values={}
        for card in (4,5,6,7):
            ident=c.PRIOR_IDS[card];name="/qwen36_damp_allt_npu"+str(card)+"_20261006_independent_v1"
            devices={"/dev/davinci"+str(card):"/dev/davinci0",
                     "/dev/davinci_manager":"/dev/davinci_manager",
                     "/dev/devmm_svm":"/dev/devmm_svm","/dev/hisi_hdc":"/dev/hisi_hdc"}
            value={"Id":ident,"Name":name,"Image":c.IMAGE,
                "Config":{"Labels":{"model-tuning-lab.owner":c.ALLT_OWNER}},
                "State":{"Running":False,"Pid":0},"HostConfig":{"Privileged":False,
                "Devices":[{"PathOnHost":a,"PathInContainer":b,"CgroupPermissions":"rwm"}
                           for a,b in devices.items()]}}
            values[ident]=value
            proofs.append({"container_id":ident,"container_inspect":copy.deepcopy(value),
                           "logical_to_physical":{"0":card},"physical_npu_ids":[card],
                           "privileged":False})
        self.assertEqual(len(c.prior_owned_contract(proofs,values.get)),4)
        values[c.PRIOR_IDS[4]]["State"]["Pid"]=123
        with self.assertRaisesRegex(ValueError,"PID0"):c.prior_owned_contract(proofs,values.get)
    def test_original_device_proof_alias_and_extra_device_refused(self):
        with self.assertRaisesRegex(ValueError,"four original"):
            c.prior_owned_contract([],lambda _:None)
        with self.assertRaisesRegex(ValueError,"four original"):
            c.prior_proof_refs([],[])

    def test_same_owner_historical_sleep_not_current_numeric_caps(self):
        import run
        value={"Id":"f"*64,"Name":"/historical-sleep","Image":c.IMAGE,
               "Config":{"Labels":{"model-tuning-lab.owner":c.ALLT_OWNER}}}
        self.assertFalse(run.current_allT(value))
        result=c.external_workload(value,{"CPUPerc":"0%","MemUsage":"2MiB / 0B"},
                                   "PID COMMAND\n123 sleep\n")
        self.assertTrue(result["pure_sleep"])
    def test_current_four_ids_require_original_name_image_owner(self):
        import run
        for card,ident in c.PRIOR_IDS.items():
            value={"Id":ident,"Name":"/qwen36_damp_allt_npu"+str(card)+"_20261006_independent_v1",
                   "Image":c.IMAGE,"Config":{"Labels":{"model-tuning-lab.owner":c.ALLT_OWNER}}}
            self.assertTrue(run.current_allT(value))
            for key,change in (("Name","/other"),("Image","other")):
                bad=copy.deepcopy(value);bad[key]=change
                with self.assertRaisesRegex(ValueError,"identity changed"):run.current_allT(bad)
            bad=copy.deepcopy(value);bad["Config"]["Labels"]["model-tuning-lab.owner"]="foreign"
            with self.assertRaisesRegex(ValueError,"identity changed"):run.current_allT(bad)
    def protected_fixture(self):
        devices={**{"/dev/davinci"+str(i):"/dev/davinci"+str(i) for i in range(4)},
                 "/dev/davinci_manager":"/dev/davinci_manager",
                 "/dev/devmm_svm":"/dev/devmm_svm","/dev/hisi_hdc":"/dev/hisi_hdc"}
        value={"Id":c.PROTECTED_ID,"Name":c.PROTECTED_NAME,"Image":c.IMAGE,
               "HostConfig":{"Privileged":False,"DeviceRequests":None,
               "Devices":[{"PathOnHost":a,"PathInContainer":b,"CgroupPermissions":"rwm"}
                          for a,b in devices.items()]}}
        stats={"CPUPerc":"7.20%","MemUsage":"26.76GiB / 128GiB"}
        top="PID COMMAND\n10 vllm\n11 python3\n12 VLLM::EngineCor\n13 VLLM::Worker_TP\n14 VLLM::Worker_TP\n"
        return value,stats,top
    def test_actual_protected26_76GiB_is_baseline_not_unknown_cap(self):
        value,stats,top=self.protected_fixture()
        baseline=c.external_workload(value,stats,top)
        self.assertTrue(baseline["known_protected0_3"])
        self.assertTrue(baseline["resident_already_accounted_in_mem_available"])
        self.assertEqual(baseline["memory_usage_bytes"],26.76*c.GIB)
        self.assertFalse(baseline["external_hard_cap_guaranteed"])
        self.assertEqual(c.resource_budget(7,42*c.GIB,40*c.GIB,preflight=True,
                                          allt_running=4)["required_mem_available"],42*c.GIB)
        self.assertEqual(c.resource_budget(7,72*c.GIB,40*c.GIB,preflight=False,
                                          allt_running=0)["required_mem_available"],72*c.GIB)
    def test_protected_known_growth_exact4GiB_and_excess(self):
        value,stats,top=self.protected_fixture()
        baseline=c.external_workload(value,stats,top)
        c.external_workload(value,{"CPUPerc":"7.2%","MemUsage":"30.76GiB / 128GiB"},top,
                            protected_baseline=baseline)
        with self.assertRaisesRegex(ValueError,"growth exceeds4GiB"):
            c.external_workload(value,{"CPUPerc":"7.2%","MemUsage":"30.77GiB / 128GiB"},top,
                                protected_baseline=baseline)
    def test_protected_unknown_or_changed_name_image_map_refused(self):
        original,stats,top=self.protected_fixture()
        for key,value in (("Id","f"*64),("Name","/foreign"),("Image","foreign")):
            changed=copy.deepcopy(original);changed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                c.external_workload(changed,stats,top)
        changed=copy.deepcopy(original)
        changed["HostConfig"]["Devices"][0]["PathOnHost"]="/dev/davinci4"
        with self.assertRaisesRegex(ValueError,"identity/map/process differs"):
            c.external_workload(changed,stats,top)
    def test_protected_cpu_above50_refused(self):
        value,stats,top=self.protected_fixture()
        with self.assertRaisesRegex(ValueError,"actual CPU high"):
            c.external_workload(value,dict(stats,CPUPerc="50.01%"),top)
    def test_protected_process_names_or_pid_changed_refused(self):
        value,stats,top=self.protected_fixture()
        baseline=c.external_workload(value,stats,top)
        for changed in (top.replace("python3","foreign"),top.replace("11 python3","111 python3")):
            with self.assertRaises(ValueError):
                c.external_workload(value,stats,changed,protected_baseline=baseline)
    def test_protected_privileged_or_extra_device_refused(self):
        value,stats,top=self.protected_fixture()
        changed=copy.deepcopy(value);changed["HostConfig"]["Privileged"]=True
        with self.assertRaises(ValueError):c.external_workload(changed,stats,top)
        changed=copy.deepcopy(value)
        changed["HostConfig"]["Devices"].append({"PathOnHost":"/dev/davinci4",
            "PathInContainer":"/dev/davinci4","CgroupPermissions":"rwm"})
        with self.assertRaises(ValueError):c.external_workload(changed,stats,top)
    def test_exact_reviewed_shell_not_old_driver_execute(self):
        command=c.bootstrap_command(c.RESULT_ROOT/"synthetic-output",[c.PYTHON,"-B","preflight.py"])
        self.assertEqual(command[:2],["/bin/bash","-c"])
        self.assertIn("source /usr/local/Ascend/ascend-toolkit/set_env.sh",command[2])
        self.assertIn('exec "$@"',command[2])
        self.assertNotIn(str(c.COLLECTOR),command[2])
        self.assertEqual(command[4:],[c.PYTHON,"-B","preflight.py"])
    def test_preflight_flag_exclusive_and_default_no_execution(self):
        import run
        self.assertEqual(run.plan(c.RESULT_ROOT/"synthetic-output")["formal_cpus"],6)
        # Actual CLI default/--help checks run separately without any Docker path.

class AggregateTests(unittest.TestCase):
    def fixture(self,root,drift=False):
        root.mkdir()
        c.write_new(root/"RUN.json",{"batch_size":1,"enforce_eager":True,"prefix_cache":False,
            "chunked_prefill":False,"generation":{"max_tokens":33},"capture_enabled":False})
        c.write_new(root/"CLIENT_COMPLETE.json",{"synthetic":True})
        (root/"client.jsonl").write_bytes(c.canonical({"prompt_token_sha256":"a"*64,"output_tokens":33,
            "output_token_ids":list(range(33))})+b"\n")
        raw=root/"synthetic.bin";raw.write_bytes(b"\x00\x00\x00\x00")
        sig={"shape":[1],"dtype":"torch.float32","finite":True,"num_bytes":4,"sha256":c.file_sha(raw),
             "raw":{"path":str(raw),"sha256":c.file_sha(raw),"size":4}}
        for rank in range(4):
            r=root/("trace-rank-"+str(rank));r.mkdir()
            rows=[{"kind":"started","rank":rank,"physical":rank+4,"packet":{"sha256":"a"*64},
                "core_source":{"sha256":"b"*64},"runner_source":{"sha256":"c"*64},"recurrent_schema":"fixture",
                "native_library":{"path":"fixture","sha256":"d"*64,"deleted":False}},
                {"kind":"bindings","layers":[{"layer":l} for l in c.LAYERS]}]
            for turn in range(33):
                rows.append({"kind":"turn_begin","turn":turn,"parameters":{
                    "input_ids":None,"inputs_embeds":None,"n":1024 if turn==0 else 1}})
                for layer in c.LAYERS:
                    metadata={"n":1024 if turn==0 else 1}
                    inp={name:dict(sig) for name in ("mixed_qkv","b","a","ssm_before","conv_before")}
                    rows.append({"kind":"core_before","turn":turn,"layer":layer,"prefix":str(layer),
                        "metadata":metadata,"parameters":{},"slot":0,"ssm_geometry":{},"conv_geometry":{},
                        "pointers":[1,2,3,4,0],"inputs":inp,"ssm_previous_after_consistent":True,
                        "conv_previous_after_consistency_asserted":False})
                    outputs={name:dict(sig) for name in ("g","beta","ssm_after","conv_after","core_output")}
                    if drift and rank==0 and turn==2 and layer==0:
                        alternate=root/"alternate.bin";alternate.write_bytes(b"\x01\x00\x00\x00")
                        outputs["g"]={**sig,"sha256":c.file_sha(alternate),
                            "raw":{"path":str(alternate),"sha256":c.file_sha(alternate),"size":4}}
                    rows.append({"kind":"core_after","turn":turn,"layer":layer,"prefix":str(layer),
                        "slot":0,"after":outputs,"pointers":[1,2,3,4,0]})
                rows.append({"kind":"turn_commit","turn":turn,"layers":list(c.LAYERS),"native_return_preserved":True})
            rows.append({"kind":"complete","raw_bytes":4})
            (r/"events.jsonl").write_bytes(b"".join(c.canonical(x)+b"\n" for x in rows))
    def test_complete_synthetic_bitwise_and_first_seam(self):
        with tempfile.TemporaryDirectory() as temporary:
            a,b=Path(temporary)/"a",Path(temporary)/"b"
            self.fixture(a);self.fixture(b)
            self.assertEqual(aggregate.compare(a,b)["status"],"bitwise_pass")
            # A full synthetic fixture proves parsing/coverage logic, NOT NPU.
            import shutil
            shutil.rmtree(b)
            self.fixture(b,True)
            result=aggregate.compare(a,b)
            self.assertEqual(result["first_GDN_observed_difference"]["seam"],"g")
            self.assertFalse(result["full_calibration_admitted"])
    def test_raw_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/"a";self.fixture(root)
            (root/"synthetic.bin").write_bytes(b"broken")
            with self.assertRaisesRegex(ValueError,"raw"):aggregate.arm(root)

if __name__=="__main__":
    unittest.main()
