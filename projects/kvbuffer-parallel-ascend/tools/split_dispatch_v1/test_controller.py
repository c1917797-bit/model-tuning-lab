"""Synthetic stdlib only: no Docker/Torch/NPU and no actual authority is produced."""
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import ast
import json

BASE=Path(__file__).resolve().parent
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=module("kvbp_test_new_contracts",BASE/"contracts.py")
d=module("kvbp_test_new_controller",BASE/"controller.py")
NOW=datetime(2026,10,6,20,tzinfo=timezone.utc)
def inputs():
    return dict(parent_operation={"path":"/actual/terminal.json","sha256":"a"*64},
       parent_expected=dict(command="/usr/bin/python3",args=["-B","real-parent"],cwd=str(c.ROOT)),
       run_slug="synthetic-software-only",phase_seconds={"1":5400,"16":8100},
       formal_start_utc="2026-10-06T19:59:00Z",deadline_utc="2026-10-07T08:48:03Z",
       main_approved=True,forbid_other_owned_jobs=True)
def terminal(code=0):
    return dict(operationId=c.PARENT_OP,terminal=True,operation=dict(routeDecision="peer_direct",
        targetPeerId=c.PARENT_PEER,result=dict(found=True,lane="job",state="completed",record=dict(
            id=c.PARENT_OP,lane="job",state="completed",exitCode=code,
            error=None if code==0 else "exit code",cancelled=False,timedOut=False,
            command="/usr/bin/python3",args=["-B","real-parent"],cwd=str(c.ROOT)))))
class Contracts(unittest.TestCase):
    def test_joint_budgets(self):
        p=c.plan(inputs(),NOW)
        self.assertEqual(p["ordinary_ram_bytes"],24*1024**3)
        self.assertEqual(p["joint_cpu"],3)
        self.assertFalse(p["npu_executed"])
        self.assertEqual([x["batch"] for x in p["jobs"]],[1,16])
    def test_true_argv_no_shim(self):
        for job in c.plan(inputs(),NOW)["jobs"]:
            a=c.gate_argv(job,"b"*64)
            self.assertEqual(a[:2],["/usr/bin/docker","exec"])
            i=a.index(c.PYTHON)
            self.assertEqual(a[i:i+3],[c.PYTHON,"-B",c.RUNNER])
            self.assertNotIn("runpy"," ".join(a))
            self.assertEqual(a[a.index("--batch")+1],str(job["batch"]))
    def test_mounts_and_single_card(self):
        for j in c.plan(inputs(),NOW)["jobs"]:
            a=j["create_argv"]
            self.assertIn("/dev/davinci%d:/dev/davinci0"%j["physical_card"],a)
            self.assertNotIn("--privileged",a)
            self.assertEqual(a[a.index("--cpus")+1],"1")
            self.assertEqual(a[a.index("--memory")+1],"8g")
            mounts=[a[i+1] for i,x in enumerate(a) if x=="--mount"]
            self.assertEqual(len([x for x in mounts if not x.endswith(",readonly")]),1)
            self.assertTrue(all("source=/" in x for x in mounts))
    def test_deadline_and_missing_budgets(self):
        x=inputs();x["phase_seconds"]={"1":0,"16":3600}
        with self.assertRaises(ValueError):c.bounds(x,NOW)
        x=inputs();x["deadline_utc"]="2026-10-06T20:01:00Z"
        with self.assertRaises(ValueError):c.bounds(x,NOW)
    def test_no_clock_extension(self):
        x=inputs();x["deadline_utc"]="2026-10-08T20:00:00Z"
        with self.assertRaises(ValueError):c.bounds(x,NOW)
    def test_parent_failed_completed_is_release_only(self):
        v=c.parent_terminal(terminal(1),inputs()["parent_expected"])
        self.assertEqual(v["exit_code"],1)
        self.assertIn("not PASS",v["scope"])
    def test_parent_missing_wrong_running_rejects(self):
        for transform in (lambda x:x.update(terminal=False),
            lambda x:x["operation"]["result"]["record"].update(timedOut=True),
            lambda x:x["operation"]["result"]["record"].update(error="other error"),
            lambda x:x["operation"].update(targetPeerId="wrong"),
            lambda x:x["operation"]["result"]["record"].update(args=["fake"])):
            x=terminal();transform(x)
            with self.assertRaises(ValueError):c.parent_terminal(x,inputs()["parent_expected"])
    def test_exclusive_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"release"
            first=c.write_new(p,dict(actual=False))
            self.assertEqual(first["sha256"],c.sha(p))
            with self.assertRaises(FileExistsError):c.write_new(p,dict(actual=True))
    def test_primary_survives_command_evidence_failure(self):
        with tempfile.TemporaryDirectory() as td:
            cmd=d.Commands(td)
            primary=RuntimeError("original before completion")
            with patch.object(d.subprocess,"run",side_effect=primary), \
                 patch.object(d.c,"write_new",side_effect=OSError("receipt unavailable")):
                with self.assertRaises(RuntimeError) as caught:
                    cmd.run("synthetic",["/never-executed"])
            self.assertIs(caught.exception,primary)
            self.assertEqual(len(cmd.secondary_errors),1)
    def test_secondary_preserves_primary(self):
        errors=[]
        original=ValueError("native original")
        try:
            raise original
        except ValueError:
            d.secondary("synthetic cleanup",lambda:(_ for _ in ()).throw(OSError("save fail")),errors)
            with self.assertRaises(ValueError) as caught:
                raise
        self.assertIs(caught.exception,original)
        self.assertEqual(len(errors),1)
    def test_source_no_torch_import_execute_default_off(self):
        for name in ("controller.py","contracts.py"):
            tree=ast.parse((BASE/name).read_text())
            imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
            imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
            self.assertFalse(any(x and (x=="torch" or x=="torch_npu") for x in imports))
        s=(BASE/"controller.py").read_text()
        self.assertIn('KVBUFFER_SPLIT_DISPATCH_EXECUTE',s)
        self.assertIn('actual_gate_process=observed',s)
        self.assertIn('canary_same_process=False',s)
        self.assertIn('c.write_new(Path(job["launch_root"])/"RELEASE"',s)
    def test_device_wait_never_promotes_alone(self):
        source=(BASE/"controller.py").read_text()
        self.assertIn('process.returncode == 0 and observed',source)
        self.assertIn('gate_process_confirmation_required=True',source)
        self.assertIn('actual["start_ticks"] == waiting["start_ticks"]',source)
    def test_independent_ops_marker_one(self):
        self.assertEqual((BASE/"controller.py").read_text().count('print(c.PREFIX+'),1)
        self.assertIn('"prepare-joint","run-arm"',(BASE/"controller.py").read_text())
    def test_nonfinite_raw_json_rejects(self):
        for raw in (b'{"metric":NaN}',b'{"metric":1e999}',b'{"metrics":[-1e999]}'):
            with self.assertRaises(ValueError):c.clean(raw)

    def test_raw_report_pass_gate_unchanged(self):
        class Split:
            @staticmethod
            def protocol(b,p):return {"batch":b,"card":p}
        with self.assertRaises(ValueError):
            c.stage_report({"schema":"kvbp.split-native-gate/v1","status":"failed"},
                           {},1,None,Split,None,None)

    def test_full_producer_shaped_report_and_real_argv_bridge(self):
        import copy
        import sys
        bridge_path=c.PROJECT/"tools/split_service_authority_v1/validator.py"
        bridge=module("kvbp_test_bridge",bridge_path)
        previous=sys.modules.get("validator")
        sys.modules["validator"]=bridge
        try:
            fixture_module=module("kvbp_test_original_fixture",bridge_path.parent/"test_validator.py")
        finally:
            if previous is None:
                sys.modules.pop("validator",None)
            else:
                sys.modules["validator"]=previous
        f=fixture_module.Fixture()
        split=module("kvbp_test_split",c.PROJECT/"tools/split_gate_v1/contract.py")
        meta=bridge.clean_json(f.read(f.manifest["artifacts"]["meta"]["path"]))
        for b,a in ((1,f.b1),(16,f.b16)):
            r=f.decoded(a["report"]);ident=f.decoded(a["identity"])
            self.assertEqual(c.stage_report(r,ident,b,bridge,split,f.manifest,meta),640)
            child=f.decoded(a["child"])
            job=next(j for j in c.plan(inputs(),NOW)["jobs"] if j["batch"]==b)
            cid=child["execution"]["args"][3]
            # Real new producer argv shape, still explicitly synthetic evidence.
            child["execution"]["args"]=c.gate_argv(job,cid)[1:]
            child["image_identity_path"]=job["image_identity"]
            child["image_output_dir"]=job["image_output"]
            f.refresh(a,"child",child)
            self.assertEqual(bridge.child(a,r,ident,b,f.read,True)["physical_device"],c.CARDS[b])
            bad=copy.deepcopy(r);bad["cases"][0]["steps"][2]["guards"]=False
            with self.assertRaises(ValueError):c.stage_report(bad,ident,b,bridge,split,f.manifest,meta)


    def test_exact_executable_source_contract(self):
        s=(BASE/"controller.py").read_text()
        self.assertEqual(s.count('[c.NPU_SMI,"info"]'),3)
        self.assertNotIn('["npu-smi","info"]',s)
        self.assertNotIn('/usr/local/Ascend/driver/tools/npu-smi',s)
        self.assertEqual(c.NPU_SMI,"/usr/local/sbin/npu-smi")
        self.assertEqual(c.NPU_SMI_SHA,"c9476b1bf1a2b1cb6b1def82e27889b6f89189a12e9ff4aee5bd2047a19a3cce")
    def test_runtime_resource_positive_and_stopped_peer(self):
        groups={b:dict(running=True,memory_limit_bytes=c.MEMORY,cpu_quota=1,
                      memory_current_bytes=2*c.GIB,memory_peak_bytes=3*c.GIB) for b in (1,16)}
        row=c.runtime_budget(24*c.GIB,c.phase_disk_need(8100),8100,groups)
        self.assertEqual(row["uncommitted_owned_cap_growth_bytes"],12*c.GIB)
        self.assertEqual(row["live_ram_required_bytes"],20*c.GIB)
        groups[1]=dict(running=False,stopped_verified=True,pid=0,memory_limit_bytes=c.MEMORY,cpu_quota=1)
        row=c.runtime_budget(24*c.GIB,c.phase_disk_need(500),500,groups)
        self.assertEqual(row["uncommitted_owned_cap_growth_bytes"],6*c.GIB)
    def test_runtime_resource_negative_peak_cap_ram_and_disk(self):
        import copy
        groups={b:dict(running=True,memory_limit_bytes=c.MEMORY,cpu_quota=1,
                      memory_current_bytes=2*c.GIB,memory_peak_bytes=3*c.GIB) for b in (1,16)}
        with self.assertRaises(ValueError):c.runtime_budget(7*c.GIB,100*c.GIB,100,groups)
        with self.assertRaises(ValueError):c.runtime_budget(19*c.GIB,100*c.GIB,100,groups)
        with self.assertRaises(ValueError):c.runtime_budget(24*c.GIB,c.phase_disk_need(100)-1,100,groups)
        for patch in (dict(memory_peak_bytes=None),dict(memory_peak_bytes=9*c.GIB),
                      dict(memory_limit_bytes=9*c.GIB),dict(cpu_quota=2),
                      dict(memory_current_bytes=4*c.GIB)):
            g=copy.deepcopy(groups);g[16].update(patch)
            with self.assertRaises(ValueError):c.runtime_budget(24*c.GIB,100*c.GIB,100,g)
        with self.assertRaises(ValueError):c.runtime_budget(24*c.GIB,100*c.GIB,100,{1:groups[1]})
    def test_remaining_phase_disk_not_cumulative_write_residency(self):
        self.assertGreater(c.phase_disk_need(8100),c.phase_disk_need(5400))
        self.assertGreater(c.phase_disk_need(0),8*c.GIB)
        self.assertLess(c.phase_disk_need(10800),13*c.GIB)
        self.assertLess(c.raw_step_ceiling(16),128*1024**2)
        self.assertGreater(c.raw_step_ceiling(16),c.raw_step_ceiling(1))
        with self.assertRaises(ValueError):c.phase_disk_need(float("inf"))


    def test_source_bound_actual_idle_envelope(self):
        self.assertEqual(c.idle_hbm_ceiling(),3165)
        for usage in (0,2860,2864,3165):
            self.assertTrue(c.idle_card(dict(aicore=0,hbm_mib=usage)))
        for row in (dict(aicore=1,hbm_mib=2864),dict(aicore=0,hbm_mib=3166),
                    dict(aicore=0,hbm_mib=None),dict(hbm_mib=2864)):
            with self.assertRaises(ValueError):c.idle_card(row)
        source=(BASE/"controller.py").read_text()
        self.assertNotIn('hbm_mib"] <= 1024',source)
        self.assertIn('c.idle_card(telemetry[card])',source)

if __name__=="__main__":unittest.main()
