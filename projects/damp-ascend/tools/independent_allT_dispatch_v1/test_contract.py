#!/usr/bin/env python3
"""Synthetic stdlib/source tests ONLY; never Torch/load/Docker/NPU."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import independent_contract as c
import controller as d
import reference_seam as r

class Toy:
    def __init__(self,data):self.data=list(data)
    def clone(self):return Toy(self.data)

class ContractTests(unittest.TestCase):
    def test_no_device_import(self):
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
    def test_packet_actual_closure(self):
        p=c.packet();self.assertEqual(set(p["sources"]),set(c.OWN))
        self.assertEqual(len(p["reused_sources"]),34)
        self.assertEqual(len(c.source_snapshot()),41)
    def test_geometry_source_not_calibration(self):
        g=c.model_geometry();self.assertEqual((g["linear_layers"],g["local_key_heads"],g["local_value_heads"]),(48,4,12))
        self.assertNotIn("source_lock",g)
    def test_true_batch_admission(self):
        for t in range(1,17):r.guard_batch(t,True)
        for t in(0,17,True,1.5):
            with self.assertRaises(ValueError):r.guard_batch(t,True)
        with self.assertRaises(ValueError):r.guard_batch(2,False)
    def test_row_own_feedback_and_untouched(self):
        before=Toy([5,9,100,77])
        observations=[]
        def one(i,working):
            observations.append(list(working.data));new=working.clone();new.data[(0,1)[i]]+=i+1
            return {"packed":new,"output":new.data[(0,1)[i]]}
        got=r.compose_rows(before,2,one,lambda packed,rows:(packed,[x["output"] for x in rows]))
        self.assertEqual(before.data,[5,9,100,77])
        self.assertEqual(observations,[[5,9,100,77],[6,9,100,77]])
        self.assertEqual(got[0].data,[6,11,100,77]);self.assertEqual(got[1],[6,11])
    def test_row_failure_is_original(self):
        primary=RuntimeError("row1 original")
        def one(i,w):
            if i==1:raise primary
            return {"packed":w.clone()}
        with self.assertRaises(RuntimeError) as hit:r.compose_rows(Toy([1]),3,one,lambda *x:x)
        self.assertIs(hit.exception,primary)
    def test_private_function_globals_do_not_patch_old(self):
        graph=types.ModuleType("synthetic_graph")
        exec("def helper(): return native_step()\ndef graph_case(): return helper(), observe(), metadata_cases(), storage_disjoint()\n",graph.__dict__)
        graph.native_step=lambda:"OLD";graph.observe=lambda:"OLD";graph.metadata_cases=lambda:"OLD";graph.storage_disjoint=lambda:"OLD"
        protocols=types.ModuleType("synthetic_protocol")
        exec("def invoke_prepare_guard(): return observe(), storage_disjoint()\n",protocols.__dict__)
        registry=types.SimpleNamespace(observe=lambda:"NEWobserve");rows=types.SimpleNamespace(step=lambda:"NEWnative")
        original=graph.graph_case
        cloned=r.clone_graph_case(graph,protocols,rows,registry,lambda:"NEWmeta",lambda:"NEWspan")
        self.assertIs(cloned.__code__,original.__code__)
        self.assertEqual(cloned(),("NEWnative","NEWobserve","NEWmeta","NEWspan"))
        self.assertEqual(original(),("OLD","OLD","OLD","OLD"));self.assertIs(graph.graph_case,original)
        self.assertNotIn("observe",protocols.__dict__)
    def test_evidence_failure_keeps_original(self):
        with tempfile.TemporaryDirectory() as root:
            errors=[];primary=RuntimeError("native before mkdir")
            self.assertFalse(d.emit(Path(root)/"absent"/"raw.json",{},errors,primary=primary))
            self.assertEqual(len(errors),1)
            with self.assertRaises(FileNotFoundError):d.emit(Path(root)/"absent"/"raw.json",{},errors)
    def test_command_primary_survives_receipt_write(self):
        with tempfile.TemporaryDirectory() as root:
            cmd=d.Commands(root,[]);primary=RuntimeError("subprocess original")
            # Real output files, forced emission failure instead of fake evidence.
            def broken(path,value,errors,*,primary=None):
                if primary is not None:
                    errors.append({"path":str(path),"error":"synthetic write failed"});return False
                raise OSError("write failed")
            with patch.object(d.subprocess,"run",side_effect=primary),patch.object(d,"emit",side_effect=broken):
                with self.assertRaises(RuntimeError) as hit:cmd.run("synthetic",["never-executed"])
            self.assertIs(hit.exception,primary);self.assertEqual(len(cmd.errors),1)
    def test_command_primary_survives_raw_hash_failure(self):
        with tempfile.TemporaryDirectory() as root:
            cmd=d.Commands(root,[]);primary=RuntimeError("actual command primary")
            with patch.object(d.subprocess,"run",side_effect=primary),patch.object(d,"sha",side_effect=OSError("hash storage unavailable")):
                with self.assertRaises(RuntimeError) as hit:cmd.run("synthetic_hash",["never-executed"])
            self.assertIs(hit.exception,primary);self.assertEqual(len(cmd.errors),2)
            record=json.loads((Path(root)/"0001-synthetic_hash.receipt.json").read_text())
            self.assertIsNone(record["stdout_sha256"]);self.assertIn("actual command primary",record["error"])
    def test_real_runner_except_keeps_primary_when_retain_throws(self):
        import traceback
        source=ast.parse((c.BASE_NEW/"runner.py").read_text())
        helper=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=="retain_failure")
        main=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=="main")
        original_try=next(n for n in main.body if isinstance(n,ast.Try) and n.handlers)
        handler=copy.deepcopy(original_try.handlers[0])
        # Execute the ACTUAL runner except body, not a copied fake implementation.
        trial=ast.FunctionDef(name="actual_except",args=ast.arguments(
            posonlyargs=[],args=[ast.arg(arg=n) for n in("gate","report","primary")],
            kwonlyargs=[],kw_defaults=[],defaults=[]),body=[ast.Try(
            body=[ast.Raise(exc=ast.Name(id="primary",ctx=ast.Load()),cause=None)],
            handlers=[handler],orelse=[],finalbody=[])],decorator_list=[])
        env={"sys":sys,"traceback":traceback}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(helper),trial],type_ignores=[])),
                     "actual_runner_except","exec"),env)
        class BrokenRetain:
            case={"status":"running"}
            def retain(self):raise OSError("snapshot before frozen torch.save try")
        gate=BrokenRetain();report={};primary=RuntimeError("actual native primary")
        from contextlib import redirect_stderr
        import io
        stderr=io.StringIO()
        with redirect_stderr(stderr):result=env["actual_except"](gate,report,primary)
        self.assertEqual(result,1);self.assertEqual(report["status"],"failed")
        self.assertEqual(report["error"],repr(primary))
        self.assertIn("actual native primary",report["traceback"])
        self.assertEqual(gate.case["error"],repr(primary))
        self.assertIn("snapshot before frozen torch.save try",report["failure_retention_secondary_error"])
        self.assertIn("original primary",stderr.getvalue())
    def test_four_shard_exact_cli(self):
        planner=c.load("_test_frozen_planner",c.PROJECT/"tools/allT_dispatch_plan_v1/plan.py")
        plan=d.make_plan("synthetic_check",planner,"a"*64)
        self.assertFalse(plan["launchable"]);self.assertFalse(plan["calibration_source_lock_required"])
        for e in plan["shards"]:
            card=e["physical_card"];argv=e["docker_create_argv"];gate=e["gate_argv_source_bound_incomplete"]
            self.assertEqual(e["batches"],list(range(1+4*(card-4),5+4*(card-4))))
            self.assertIn("/dev/davinci"+str(card)+":/dev/davinci0",argv)
            self.assertNotIn("--privileged",argv);self.assertEqual(argv[argv.index("--cpus")+1],"1")
            self.assertEqual(argv[argv.index("--memory")+1],"8g");self.assertIn("DAMP_RUN_INDEPENDENT_ALLT_V1=1",argv)
            self.assertEqual(gate[2],str(c.BASE_NEW/"runner.py"));self.assertEqual(gate[-2:],["--packet-sha256","a"*64])
            self.assertEqual(e["create_argv_sha256"],planner.argv_sha(argv))
            self.assertEqual(e["docker_canary_exec_argv"][-2],e["create_argv_sha256"])
            self.assertIsNone(e["gate_argv"]);self.assertIsNone(e["docker_gate_exec_argv"])
    def test_actual_failed_terminal_is_scheduling_only(self):
        selected=c.load("_test_frozen_scheduling",c.PROJECT/"tools/selected_prefill_dispatch_v1/controller.py")
        host=c.load("_test_frozen_host",c.PROJECT/"tools/allT_dispatch_controller_v1/controller.py")
        raw=c.read("/cache/cch/qwen36-damp-20261006/full-reference-resume-v1-terminal-original.json")
        got=selected.parent_terminal(raw,host)
        self.assertEqual(got["exit_code"],1);self.assertFalse(got["capture_success"])
        self.assertNotIn("source_lock",got)
        for edit in("timedOut","cancelled"):
            bad=copy.deepcopy(raw)
            node=bad.get("structuredContent",bad);node["operation"]["result"]["record"][edit]=True
            with self.assertRaises(RuntimeError):selected.parent_terminal(bad,host)
    def test_source_anchor_precedes_registered_matrix(self):
        source=(c.BASE_NEW/"runner.py").read_text()
        self.assertLess(source.index("native_rows.anchor(native)"),source.index("for batch in BATCH_GROUPS"))
        self.assertLess(source.index("run_npu_gate.mapped_bindings("),source.index("native_rows.anchor(native)"))
        self.assertNotIn("protocols.observe=",source);self.assertNotIn("graph_protocol.observe=",source)
        self.assertNotIn("source_lock",source)
        self.assertIn("clone_graph_case(",source);self.assertIn('"calibrated_plan_count":0',source)
    def test_anchor_incomplete_rejected(self):
        with self.assertRaises(ValueError):c.validate_native_anchors({"native_row_reference":{"anchors_passed":True}})
    def test_original_source_source_lock_not_called(self):
        tree=ast.parse((c.BASE_NEW/"controller.py").read_text())
        calls=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        self.assertNotIn("finalized",calls) # Real proof call is intentional.
        self.assertIn("parent_terminal",calls);self.assertIn("parent_stopped",calls)
    def test_no_fake_padding_or_threshold_changes(self):
        source=(c.BASE_NEW/"reference_seam.py").read_text()
        self.assertIn("q[row:row+1]",source);self.assertNotIn("pad(",source)
        self.assertEqual(c.LIMITS,{"state":1e-5,"output":0.00303})
    def test_cli_default_off_static(self):
        tree=ast.parse((c.BASE_NEW/"controller.py").read_text())
        literals=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant)]
        self.assertIn("store_true",literals);self.assertIn("DAMP_INDEPENDENT_ALLT_EXECUTE",literals)
        self.assertNotIn("source-lock-sha256",literals)
    def test_fixed_deadline(self):
        from datetime import datetime,timezone
        with self.assertRaises(ValueError):d.deadline(now=datetime(2026,10,7,8,48,3,tzinfo=timezone.utc))
    def test_every_new_python_parses(self):
        for name in c.OWN:
            if name.endswith(".py"):ast.parse((c.BASE_NEW/name).read_text())

if __name__=="__main__":unittest.main(verbosity=2)
