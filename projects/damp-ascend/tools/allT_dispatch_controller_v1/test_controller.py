#!/usr/bin/env python3
"""Stdlib source/controller safety contracts only; no Docker, Torch or NPU execution."""
import ast
import contextlib
import copy
from datetime import datetime,timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("new_damp_allT_controller",BASE/"controller.py")
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

def terminal():
    record={"id":c.PARENT_OPERATION,"lane":"job","state":"completed","exitCode":0,"cancelled":False,
            "timedOut":False,"error":None,"command":"/usr/bin/python3","cwd":str(c.REPO)}
    return {"operationId":c.PARENT_OPERATION,"terminal":True,"ok":True,
            "operation":{"routeDecision":"peer_direct","targetPeerId":c.PARENT_PEER,
                         "result":{"found":True,"ok":True,"lane":"job","state":"completed","record":record}}}

def process_table(rows=()):
    body=["| NPU Chip | Process id | Process name | Process memory(MB) |",
          "+---+---+---+---+"]
    present=set()
    for card,chip,pid,name,memory in rows:
        body.append(f"| {card} {chip} | {pid} | {name} | {memory} |");present.add(card)
    for card in range(8):
        if card not in present:body.append(f"| No running processes found in NPU {card} |")
    body.append("+---+")
    return "\n".join(body)

def entry(e,cid="a"*64,running=True):
    argv=e["docker_create_argv"];mounts=[]
    for i,x in enumerate(argv):
        if x=="--mount":
            options=dict(v.split("=",1) for v in argv[i+1].split(",") if "=" in v)
            mounts.append({"Destination":options["target"],"Source":options["source"],
                           "Type":"bind","RW":not argv[i+1].endswith(",readonly")})
    env=[argv[i+1] for i,x in enumerate(argv) if x=="-e"]
    after=argv[argv.index("--entrypoint")+2:]
    return {"Id":cid,"Name":"/"+e["container_name"],"Image":c.load_module("controller_fixture_plan",c.PLAN/"plan.py").IMAGE,
        "Config":{"Labels":{"model-tuning-lab.owner":"damp-allT-dispatch-v1",
                           "model-tuning-lab.run":e["container_name"].split("_20261006_",1)[1]},
                  "Env":env,"Entrypoint":["/bin/bash"],"Cmd":after[1:],"WorkingDir":str(c.REPO)},
        "HostConfig":{"Privileged":False,"NetworkMode":"none","DeviceRequests":None,"IpcMode":"private",
                      "Memory":8*c.GIB,"MemorySwap":8*c.GIB,"NanoCpus":10**9,"CapDrop":["ALL"],
                      "SecurityOpt":["no-new-privileges"],
                      "Devices":[{"PathOnHost":"/dev/davinci"+str(e["physical_card"]),"PathInContainer":"/dev/davinci0"}]+[
                          {"PathOnHost":"/dev/"+x,"PathInContainer":"/dev/"+x}
                          for x in ("davinci_manager","devmm_svm","hisi_hdc")]},
        "Mounts":mounts,"State":{"Running":running,"Status":"running" if running else "exited","Pid":123}}

class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.planner=c.load_module("controller_test_frozen_plan",c.PLAN/"plan.py")
        cls.shard=cls.planner.shard("software_fixture",4,c.ROOT/"allT-dispatch-software_fixture")

    def test_authoritative_terminal_record(self):
        self.assertEqual(c.parent_terminal(terminal())["exit_code"],0)
        self.assertEqual(c.parent_terminal({"structuredContent":terminal()})["operation_id"],c.PARENT_OPERATION)
        for key,value in (("terminal",False),("operationId","exec-other")):
            row=terminal();row[key]=value
            with self.subTest(key=key),self.assertRaises(RuntimeError):c.parent_terminal(row)
        for key,value in (("routeDecision","upstream_local_peer"),("targetPeerId","wrong")):
            row=terminal();row["operation"][key]=value
            with self.subTest(key=key),self.assertRaises(RuntimeError):c.parent_terminal(row)
        for key,value in (("exitCode",1),("state","running"),("cancelled",True),("timedOut",True),
                          ("error","failure"),("lane","process"),("id","other"),("command","bash"),("cwd","/tmp")):
            row=terminal();row["operation"]["result"]["record"][key]=value
            with self.subTest(key=key),self.assertRaises(RuntimeError):c.parent_terminal(row)
        row=terminal();del row["operation"]["result"]["record"]
        with self.assertRaises(RuntimeError):c.parent_terminal(row)

    def test_actual_combined_process_table(self):
        self.assertEqual(c.parse_processes(process_table()),{i:[] for i in range(8)})
        parsed=c.parse_processes(process_table(((0,0,111,"python",2000),(4,0,222,"python",150))))
        self.assertEqual(parsed[4],[{"pid":222,"name":"python","memory_mib":150}])
        for raw in ("unknown",process_table().replace("NPU 7","NPU 8"),
                    process_table(((4,1,222,"python",1),)),
                    process_table(((4,0,222,"python",1),(4,0,222,"python",1))),
                    process_table()+"\n| unknown |"):
            with self.subTest(raw=raw),self.assertRaises(RuntimeError):c.parse_processes(raw)

    def test_immutable_id_exec(self):
        out=c.immutable_exec(["docker","exec","name","python","-B"],"a"*64)
        self.assertEqual(out,["docker","exec","a"*64,"python","-B"])
        for argv,cid in ((["docker","stop","name"],"a"*64),(["docker","exec","name"],"wrong")):
            with self.assertRaises(RuntimeError):c.immutable_exec(argv,cid)

    def test_container_scope_and_mutability(self):
        e=copy.deepcopy(self.shard);good=entry(e)
        self.assertEqual(c.inspect_proof(good,e,"a"*64)["physical"],4)
        for number in range(11):
            row=copy.deepcopy(good)
            if number==0:row["Id"]="b"*64
            elif number==1:row["HostConfig"]["Privileged"]=True
            elif number==2:row["HostConfig"]["Devices"][0]["PathOnHost"]="/dev/davinci0"
            elif number==3:row["HostConfig"]["Devices"].append({"PathOnHost":"/dev/davinci7","PathInContainer":"/dev/davinci7"})
            elif number==4:row["Mounts"][0]["RW"]=True
            elif number==5:row["HostConfig"]["NanoCpus"]=2*10**9
            elif number==6:row["HostConfig"]["MemorySwap"]=9*c.GIB
            elif number==7:row["Config"]["Labels"]["model-tuning-lab.owner"]="foreign"
            elif number==8:row["HostConfig"]["NetworkMode"]="host"
            elif number==9:row["Config"]["Env"]=[]
            else:row["Config"]["Cmd"]=["different"]
            with self.subTest(number=number),self.assertRaises(RuntimeError):c.inspect_proof(row,e,"a"*64)

    def test_cgroup_paths_respect_mount_root(self):
        text="0::/system.slice/docker-"+("a"*64)+".scope/subgroup\n"
        rows=c.parse_cgroup(text)
        raw="28 1 0:24 /system.slice /sys/fs/cgroup rw - cgroup2 cgroup rw\n"
        mounts=c.cgroup_mounts(raw)
        self.assertEqual(c.cgroup_path(rows,mounts,"unified","memory.max"),
                         Path("/sys/fs/cgroup")/("docker-"+("a"*64)+".scope")/"subgroup/memory.max")
        with self.assertRaises(RuntimeError):c.parse_cgroup("0::/bad/../path")
        with self.assertRaises(RuntimeError):c.cgroup_path({"unified":"/outside"},mounts,"unified","memory.max")

    def test_exact_pid_cgroup_owner_component(self):
        cid="a"*64
        for group in (f"0::/docker/{cid}/nested\n",f"0::/system.slice/docker-{cid}.scope/nested\n"):
            with patch.object(c,"proc_identity",return_value={"pid":111,"cgroup":group}):
                self.assertEqual(c.owner_pid(111,cid)["pid"],111)
        for group in (f"0::/docker/prefix{cid}\n",f"0::/docker/{cid}suffix\n","0::/foreign\n"):
            with patch.object(c,"proc_identity",return_value={"pid":111,"cgroup":group}):
                with self.assertRaises(RuntimeError):c.owner_pid(111,cid)

    def test_no_overwrite_and_finite_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"finite.json";c.write_new(p,{"first_failure":None,"original_error":"real","flags":[False]})
            self.assertEqual(c.read_json(p)["first_failure"],None)
            with self.assertRaises(FileExistsError):c.write_new(p,{})
            bad=Path(tmp)/"bad.json"
            with self.assertRaises(ValueError):c.write_new(bad,{"bad":float("nan")})
            bad.write_text('{"bad":NaN}')
            with self.assertRaises(ValueError):c.read_json(bad)

    def test_raw_command_failure_preserved(self):
        def fake(argv,stdout,stderr,timeout,check):
            stdout.write(b"raw out\n");stderr.write(b"raw original failure\n")
            return SimpleNamespace(returncode=9)
        with tempfile.TemporaryDirectory() as tmp,patch.object(c.subprocess,"run",side_effect=fake):
            cmd=c.Commands(tmp)
            with self.assertRaises(RuntimeError):cmd.run("failure",["mock-not-docker"])
            row=c.read_json(Path(tmp)/"0001-failure.receipt.json")
            self.assertEqual(row["exit_code"],9);self.assertFalse(row["automatic_retry"])
            self.assertEqual(Path(row["stderr"]).read_text(),"raw original failure\n")

    def test_stop_exact_owned_and_retain(self):
        e=copy.deepcopy(self.shard);before=entry(e);after=entry(e,running=False)
        cmd=SimpleNamespace(run=unittest.mock.Mock())
        with patch.object(c,"inspect",side_effect=[before,after]):
            row=c.stop_owned(cmd,e,"a"*64)
        self.assertFalse(row["deleted"]);cmd.run.assert_called_once()
        self.assertEqual(cmd.run.call_args.args[1],["docker","stop","--time","30","a"*64])
        cmd=SimpleNamespace(run=unittest.mock.Mock())
        foreign=entry(e);foreign["Id"]="b"*64
        with patch.object(c,"inspect",return_value=foreign),self.assertRaises(RuntimeError):
            c.stop_owned(cmd,e,"a"*64)
        cmd.run.assert_not_called()

    def test_no_device_source_preparation(self):
        with patch.object(c.subprocess,"run",side_effect=AssertionError("NO Docker/command")),\
             patch.object(c.subprocess,"Popen",side_effect=AssertionError("NO process")):
            prepared=c.source_preparation()
        self.assertEqual(prepared[4]["source"]["compiled_sources"],9)
        self.assertEqual(prepared[4]["source"]["runtime_sources"],20)
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)

    def test_default_plan_without_create_or_device_claim(self):
        prepared=(SimpleNamespace(make_plan=lambda *a:{"shards":[{"physical_card":4}]}),None,None,None,{})
        stream=io.StringIO()
        with patch.object(sys,"argv",["controller.py"]),patch.object(c,"source_preparation",return_value=prepared),\
             patch.object(c,"execute",side_effect=AssertionError("execute forbidden")),contextlib.redirect_stdout(stream):
            self.assertEqual(c.main(),0)
        row=json.loads(stream.getvalue())
        self.assertEqual(row["status"],"dry-plan-not-executed");self.assertTrue(row["no_docker_or_npu"])
        self.assertFalse(row["performance_claim"])

    def test_execute_requires_env_before_preparation(self):
        with patch.dict(os.environ,{},clear=True),patch.object(sys,"argv",["controller.py","--execute"]),\
             patch.object(c,"source_preparation",side_effect=AssertionError("must reject first")):
            with self.assertRaises(RuntimeError):c.main()

    def test_fixed_deadline(self):
        c.deadline_ok(datetime(2026,10,6,tzinfo=timezone.utc))
        with self.assertRaises(RuntimeError):c.deadline_ok(datetime(2026,10,7,8,48,3,tzinfo=timezone.utc))

    def test_source_contract(self):
        text=(BASE/"controller.py").read_text();tree=ast.parse(text)
        self.assertNotIn("shell=True",text);self.assertNotIn('"rm"',text)
        self.assertIn('["docker","stop","--time","30",cid]',text)
        self.assertIn('source_preparation();packet_identity',text)
        self.assertIn('GATE_TIMEOUT=3600',text);self.assertIn('CANARY_TIMEOUT=90',text)
        self.assertIn("unknown create outcome",text)
        self.assertIn('binding.get("library_sha256")==planner.LIBRARY_SHA',text)
        self.assertIn('binding.get("runtime_manifest_sha256")==planner.RUNTIME_SHA',text)
        self.assertIn('for e in entries:',text)
        # No module-level call to any command/controller or device helper.
        for node in tree.body:
            if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):
                self.fail("unexpected module-level call")
        self.assertEqual(c.PLAN_PINS["plan.py"],"b2facaebbdef3fcc8636af4fc0b2b8a230947e9d31e734f4769f3b75b7410179")

if __name__=="__main__":
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    print("SOFTWARE CONTRACTS ONLY; Docker/NPU/Torch not invoked")
    raise SystemExit(0 if result.wasSuccessful() else 1)
