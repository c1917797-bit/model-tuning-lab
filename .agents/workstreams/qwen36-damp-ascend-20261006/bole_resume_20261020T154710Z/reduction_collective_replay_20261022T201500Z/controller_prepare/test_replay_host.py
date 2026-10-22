"""Controller preparation controls: no Docker, no device and no MAIN lock."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location("host_review",HERE/"replay_host.py")
H=importlib.util.module_from_spec(s);s.loader.exec_module(H)


class HostTests(unittest.TestCase):
    def test_default_off_real_cli(self):
        r=subprocess.run([sys.executable,"-B",str(HERE/"replay_host.py")],capture_output=True,text=True,check=True)
        d=json.loads(r.stdout)
        self.assertFalse(d["enabled"] or d["NPU"] or d["candidate_qualification"])

    def test_execute_without_input_ref_has_no_docker_call(self):
        r=subprocess.run([sys.executable,"-B",str(HERE/"replay_host.py"),"--execute"],
                         capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0)
        self.assertIn("exact controller input Ref",r.stderr)

    def test_command_default_and_true_are_separate_fresh_process_variants(self):
        def docker_argv(cid,args):
            return ["/usr/bin/docker","exec",cid,"/bin/bash","-c",'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',
                    "kvbp-diagnostic","/usr/local/python3.12.13/bin/python3","-B",*args]
        c=types.SimpleNamespace(docker_argv=docker_argv)
        x=dict(variant="default",replay_worker_ref={"path":"/exact/replay_collective.py"},
               replay_manifest_ref={"path":"/exact/inputs","bytes":1,"sha256":"0"*64},
               output_root="/opt/host/vnf/austinov/run-bole-native-ar-collective-replay-test")
        default=H.command(c,"a"*64,x)
        true=H.command(c,"b"*64,dict(x,variant="deterministic_true"))
        self.assertNotIn("HCCL_DETERMINISTIC=true",default)
        self.assertIn("HCCL_DETERMINISTIC=true",true)
        self.assertIn("--standalone",default);self.assertIn("--local-addr=127.0.0.1",default)
        self.assertIn("--nproc-per-node=4",default)
        with self.assertRaises(ValueError):H.command(c,"partial",x)

    def test_main_lock_exclusive_uses_only_temporary_test_file(self):
        with tempfile.TemporaryDirectory() as td:
            lock=Path(td)/"MAIN_ADMISSION.lock";lock.touch()
            with patch.object(H,"LOCK",str(lock)):
                with H.main_lock(str(lock)) as proof:
                    self.assertEqual(proof["inode"],lock.stat().st_ino)
                    with self.assertRaises(BlockingIOError):
                        with H.main_lock(str(lock)):pass
                with H.main_lock(str(lock)):pass

    def test_output_budget_real_bytes_and_symlink_rejection(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/"x").write_bytes(b"abc");(root/"sub").mkdir();(root/"sub"/"y").write_bytes(b"de")
            self.assertEqual(H.output_bytes(root),5)
            (root/"link").symlink_to(root/"x")
            with self.assertRaises(ValueError):H.output_bytes(root)

    def test_ref_change_and_nonordinary_path_reject(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"input";path.write_bytes(b"one");r=H.ref(path)
            path.write_bytes(b"two")
            with self.assertRaises(ValueError):H.checked(r)
            with self.assertRaises(ValueError):H.ref("relative")

    def test_main_review_cannot_be_omitted_or_wrong_source(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            cpu=root/"cpu.json";cpu.write_text(json.dumps(dict(schema="bole.collective-replay-sameimage-software/v1",
                passed=False,devices=[],worker_ref={"sha256":"a"},controller_ref={"sha256":"b"},
                NPU=False,image=H.IMAGE)))
            x=dict(controller_ref={"sha256":"b"},replay_worker_ref={"sha256":"a"},
                   same_image_software_ref=H.ref(cpu))
            r=dict(schema="bole.collective-replay-main-review/v1",input_ref={"sha256":"input"},
                   controller_ref=x["controller_ref"],approved=False,NPU_executed=False,
                   same_image_software_ref=x["same_image_software_ref"])
            review=root/"review.json";review.write_text(json.dumps(r))
            with self.assertRaises(ValueError):H.review(H.ref(review),r["input_ref"],x)
            r["approved"]=True;review.write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,"real pinned-image"):H.review(H.ref(review),r["input_ref"],x)

    def test_controller_import_does_not_import_tensor_libraries(self):
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)

    def test_real_worker_rank_pretry_failure_stderr_is_retained(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);stdout=root/"out";stderr=root/"err"
            worker=HERE.parent/"replay_collective.py"
            env=dict(os.environ,RANK="4",LOCAL_RANK="4",WORLD_SIZE="4",LOCAL_WORLD_SIZE="4",
                     ASCEND_RT_VISIBLE_DEVICES="0,1,2,3",MASTER_ADDR="127.0.0.1",MASTER_PORT="29754")
            with stdout.open("xb") as so,stderr.open("xb") as se:
                child=subprocess.Popen([sys.executable,"-B",str(worker),"--execute",
                    "--manifest-ref","{}","--output",str(root)],stdout=so,stderr=se,env=env)
            child.wait(timeout=10)
            receipt=H.terminal_logs(types.SimpleNamespace(ref=H.ref),child,stdout,stderr)
            self.assertNotEqual(receipt["exit_code"],0)
            self.assertTrue(receipt["logs_frozen_after_termination"])
            self.assertIn("one-node four-rank",stderr.read_text())
            self.assertEqual(receipt["stderr"],H.ref(stderr))
            self.assertFalse((root/"rank-4").exists())

    def test_namespace_exit_error_is_recorded_before_lock_release(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);lock=root/"MAIN_ADMISSION.lock";lock.touch()
            def write(path,value):path.write_text(json.dumps(value))
            report=dict(completed=True,primary=None,secondary=[])
            with patch.object(H,"LOCK",str(lock)):
                with H.recorded_lock(str(lock),report,root,types.SimpleNamespace(write=write)):
                    raise ValueError("inverse fixture failure")
                result=json.loads((root/"RESULT.json").read_text())
                self.assertFalse(result["completed"] or result["namespace_scope_returned"])
                self.assertEqual(result["primary"]["message"],"inverse fixture failure")
                with H.main_lock(str(lock)):pass


if __name__=="__main__":unittest.main()
