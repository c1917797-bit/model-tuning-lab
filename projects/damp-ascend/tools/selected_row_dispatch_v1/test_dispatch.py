"""SYNTHETIC stdlib tests; no Docker/Torch/NPU or original operation authority."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import selected_contract as c
d=c.load("_selected_test_controller",c.HERE/"controller.py")
r=c.load("_selected_test_runner",c.HERE/"runner.py")

class BaseGate:
    def __init__(self,out,report):
        self.out=out;self.report=report;self.fixture={};self.case=None;self.saves=0
    def save(self):
        self.saves+=1
        (self.out/"report.json").write_text(json.dumps(self.report))
    def retain(self):
        self.fixture["retained"]=True
    def require(self,name,passed,details=None):
        self.report["checks"].append({"name":name,"passed":bool(passed),"details":details})
        self.save()
        if not passed:raise AssertionError(name)
class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.out=Path(self.t.name)
    def test_01_balanced_complete_and_equal_actual_T_cost(self):
        groups=c.BATCH_GROUPS
        self.assertEqual(set(groups),{4,5,6,7})
        self.assertEqual(sorted(x for g in groups.values() for x in g),list(range(1,17)))
        self.assertEqual([sum(g) for g in groups.values()],[34]*4)
        self.assertTrue(all(len(g)==4 for g in groups.values()))
        self.assertNotEqual(groups,c.OLD.BATCH_GROUPS)
    def test_02_new_source_closure_default_off(self):
        p=c.packet()
        self.assertFalse(p["npu_executed"]);self.assertFalse(p["default_enabled"])
        self.assertEqual(len(p["sources"]),5)
        self.assertEqual(len(p["dependencies"]),45)
        self.assertEqual(p["balanced_groups"],{str(k):list(v) for k,v in c.BATCH_GROUPS.items()})
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
    def test_03_actual_dry_plan_new_argv_and_hashes(self):
        prepared=d.source_preparation()
        p=d.make_plan("software_selected_row",prepared[0],c.sha(c.HERE/"PACKET.json"))
        for e in p["shards"]:
            self.assertEqual(e["batches"],list(c.BATCH_GROUPS[e["physical_card"]]))
            argv=e["gate_argv_source_bound_incomplete"]
            self.assertEqual(argv[2],str(c.HERE/"runner.py"))
            pos=argv.index("--batches")
            self.assertEqual(tuple(map(int,argv[pos+1:])),c.BATCH_GROUPS[e["physical_card"]])
            self.assertEqual(argv[argv.index("--packet-sha256")+1],c.sha(c.HERE/"PACKET.json"))
            self.assertEqual(e["create_argv_sha256"],prepared[0].argv_sha(e["docker_create_argv"]))
            self.assertEqual(e["docker_canary_exec_argv"][-2],e["create_argv_sha256"])
            self.assertIn("DAMP_RUN_SELECTED_ROW_DISPATCH_V1=1",e["docker_create_argv"])
            self.assertIn("/dev/davinci"+str(e["physical_card"])+":/dev/davinci0",e["docker_create_argv"])
    def test_04_actual_cli_dry_only(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out):exit_code=d.main(["--run-id","software_cli"])
        p=json.loads(out.getvalue())
        self.assertEqual(exit_code,0);self.assertTrue(p["no_docker_or_npu"]);self.assertFalse(p["launchable"])
    def test_05_missing_original_release_ref_rejects_before_actions(self):
        with self.assertRaisesRegex(ValueError,"MAIN original ref missing"):
            d.main(["--execute"])
    def journal(self):
        gate=r.journal_gate(BaseGate,lambda x:copy.deepcopy(x))(
            self.out,{"status":"running","checks":[],"cases":[],"immutable":"value"})
        self.addCleanup(lambda:gate.close() if not gate._journal.closed else None)
        return gate
    def test_06_journal_lossless_checks_steps_case_meta_and_header(self):
        g=self.journal();g.save()
        for i in range(3):
            case={"batch":i+1,"steps":[],"status":"running","fixed":{"a":[1,2]}}
            g.report["cases"].append(case);g.save()
            for step in range(20):
                g.require("c%d-s%d"%(i,step),True,{"real_metrics":[step,0.0]})
                case["steps"].append({"step":step,"passed":True,"indices":[i],"all_guards":{"x":True}})
                for _ in range(5):g.save()
            case["status"]="passed";case["after"]={"additional_negatives":[1,2,3]};g.save()
        g.report["status"]="passed";g.report["final_binding"]={"actual_sources":"SYNTHETIC"};g.save()
        self.assertEqual(r.rebuild_journal(g.journal_path),g.report)
        self.assertEqual(len(g.report["checks"]),60)
        self.assertEqual(sum(len(ca["steps"]) for ca in g.report["cases"]),60)
        self.assertLess(g.saves,12) # Stage checkpoints, not each old save call.
        self.assertGreater(g._seq,300)
    def test_07_journal_case_status_changes_and_header_removal(self):
        g=self.journal();g.save();del g.report["immutable"];g.report["status"]="failed";g.save()
        self.assertEqual(r.rebuild_journal(g.journal_path),g.report)
        self.assertNotIn("immutable",r.rebuild_journal(g.journal_path))
    def test_08_journal_rejects_check_or_step_erasure(self):
        g=self.journal();g.require("saved",True);g.report["checks"].clear()
        with self.assertRaisesRegex(ValueError,"erase"):g.save()
        g.report["checks"]=[{"name":"saved","passed":True,"details":None}]
        g.report["cases"]=[{"steps":[{"step":0}],"status":"running"}];g.save()
        g.report["cases"][0]["steps"].clear()
        with self.assertRaisesRegex(ValueError,"erase"):g.save()
    def test_09_journal_reconstruction_rejects_reorder_or_missing_event(self):
        g=self.journal();g.save();g.require("second",True)
        lines=g.journal_path.read_text().splitlines()
        bad=self.out/"tamper.jsonl";bad.write_text("\n".join(reversed(lines))+"\n")
        with self.assertRaisesRegex(ValueError,"ordering"):r.rebuild_journal(bad)
    def test_10_original_check_failure_keeps_original_content_and_raw(self):
        g=self.journal();g.fixture={"before":"SYNTHETIC raw-before","nullable_after":None}
        with self.assertRaisesRegex(AssertionError,"original failure"):
            g.require("original failure",False,{"dispatch_error":"original","nullable_after":None})
        g.retain();g.report["status"]="failed";g.save()
        value=r.rebuild_journal(g.journal_path)
        self.assertFalse(value["checks"][0]["passed"]);self.assertIsNone(value["checks"][0]["details"]["nullable_after"])
        self.assertEqual(g.fixture["before"],"SYNTHETIC raw-before")
    def test_11_prior_terminal_completed_failure_remains_failure(self):
        args=self.prior_fixture(exit_code=1)
        value=d.prior_release(args)
        self.assertFalse(value["prior_success"])
        self.assertEqual(len(value["entries"]),4)
    def test_12_prior_live_wrong_args_or_unreleased_slot_rejected(self):
        args=self.prior_fixture()
        raw=json.loads(args.prior_terminal.read_text());raw["terminal"]=False
        self.overwrite_ref(args,"prior_terminal",raw)
        with self.assertRaisesRegex(ValueError,"prior MA06a0"):d.prior_release(args)
        args=self.prior_fixture(prefix="new");args.prior_args_sha256="0"*64
        with self.assertRaisesRegex(ValueError,"args identity"):d.prior_release(args)
        args=self.prior_fixture(prefix="stop")
        stops=json.loads(args.prior_stop_retain.read_text());stops[0]["status"]="running"
        self.overwrite_ref(args,"prior_stop_retain",stops)
        with self.assertRaisesRegex(ValueError,"STOPPED"):d.prior_release(args)
    def test_13_new_numerical_component_needs_all_48_pairs(self):
        with self.assertRaisesRegex(ValueError,"equivalence"):
            c.validate_equivalence({"batches":[1,8,9,16]})
    def test_14_old_module_globals_not_rebound(self):
        groups=copy.deepcopy(c.OLD.LEGACY.BATCH_GROUPS)
        self.test_03_actual_dry_plan_new_argv_and_hashes()
        self.assertEqual(groups,c.OLD.LEGACY.BATCH_GROUPS)
        self.assertEqual(c.OLD.BASE_NEW,c.OLD_DIR)
        self.assertNotIn("torch",sys.modules)
    def prior_fixture(self,exit_code=0,prefix="prior"):
        argv=["-B",str(c.OLD_DIR/"controller.py"),"--execute","--packet-sha256",c.OLD_PACKET_SHA]
        error=None if exit_code==0 else "exit code"
        record={"id":d.PRIOR_OPERATION,"state":"completed","cancelled":False,"timedOut":False,
            "command":"/usr/bin/python3","cwd":str(c.REPO),"exitCode":exit_code,"args":argv,"error":error,
            "lane":"job","stdout":"SYNTHETIC no NPU","stderr":""}
        raw={"schema":"agentweb.operation/v1","kind":"exec","operationId":d.PRIOR_OPERATION,
            "terminal":True,"status":"completed","error":error,"succeeded":exit_code==0,
            "operation":{"routeDecision":"peer_direct","targetPeerId":"lgw_a6109c51076a4a2c9d2674ca5a8704a0",
                "result":{"found":True,"ok":True,"state":"completed","lane":"job","record":record}}}
        args=SimpleNamespace(prior_args_sha256=hashlib.sha256(json.dumps(argv,separators=(",",":")).encode()).hexdigest())
        cards={};shards=[];stops=[]
        for card in (4,5,6,7):
            cid=("%064x"%card);name="SYNTHETIC-card%d"%card
            cards[str(card)]={"container_id":cid,"container_name":name,"create_argv_sha256":"a"*64}
            shards.append({"physical_card":card,"container_name":name,"create_argv_sha256":"a"*64,
                "batches":list(range(1+4*(card-4),5+4*(card-4)))})
            stops.append({"id":cid,"name":name,"status":"exited","deleted":False})
        for n,value in (("prior_terminal",raw),("prior_admission",{"cards":cards}),
                        ("prior_execution_plan",{"shards":shards}),("prior_stop_retain",stops)):
            setattr(args,n,self.out/(prefix+"-"+n+".json"));self.overwrite_ref(args,n,value)
        return args
    def overwrite_ref(self,args,name,value):
        path=getattr(args,name);path.write_text(json.dumps(value));setattr(args,name+"_sha256",c.sha(path))
if __name__=="__main__":unittest.main()
