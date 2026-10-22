"""Device-free contract tests. No NPU import, mock tensor or algorithm PASS."""
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

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay_review", HERE / "replay_collective.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


class ReplayTests(unittest.TestCase):
    def env(self):
        return dict(RANK="0", LOCAL_RANK="0", WORLD_SIZE="4", LOCAL_WORLD_SIZE="4",
                    ASCEND_RT_VISIBLE_DEVICES="0,1,2,3", MASTER_ADDR="127.0.0.1", MASTER_PORT="29754")

    def fixture(self, root):
        def put(name, body):
            path = root / name
            path.write_bytes(body)
            return R.file_ref(path)
        source = put("SOURCE_BOUND.json", b'{"frozen":true}\n')
        mapping = put("MAPPING.json", b'{"physical_npus":[4,5,6,7]}\n')
        inputs, records = {}, []
        raw = bytes(R.TENSOR_BYTES)
        for rank in range(4):
            ref = put("input%d.bin" % rank, raw)
            inputs[str(rank)] = ref
            rec = dict(schema="bole.native-prefill-boundary-repeatability/v1", event="PROJECTION-INTERNAL",
                       rank=rank, generation=1, source_sha256=source["sha256"],
                       record=dict(generation=1, diagnostic_only=True, stages=dict(pre_reduce=dict(
                           observed=True, full_actual_tensor=True, dtype="torch.bfloat16",
                           shape=[131, 5120], bytes=R.TENSOR_BYTES, finite=True, raw=ref, sha256=ref["sha256"]))))
            records.append(put("projection%d.json" % rank, json.dumps(rec).encode()))
        manifest = dict(schema=R.SCHEMA, worker_ref=R.file_ref(R.__file__), variant="default",
                        generation=1, iterations=8, shape=[131, 5120], dtype="torch.bfloat16",
                        physical_to_logical=[[4,0],[5,1],[6,2],[7,3]], mapping_evidence=mapping,
                        source_ref=source, projection_records=records, inputs=inputs)
        return manifest

    def manifest_ref(self, root, manifest):
        path = root / "INPUT.json"
        path.write_text(json.dumps(manifest))
        return R.file_ref(path)

    def test_default_off_real_cli_and_no_torch_import(self):
        proc = subprocess.run([sys.executable, "-B", str(HERE/"replay_collective.py")],
                              capture_output=True, text=True, check=True)
        value = json.loads(proc.stdout)
        self.assertFalse(value["enabled"] or value["NPU"] or value["candidate_qualification"])
        self.assertNotIn("torch", sys.modules)
        self.assertNotIn("torch_npu", sys.modules)

    def test_cli_execute_missing_inputs_fails_before_torch(self):
        proc = subprocess.run([sys.executable, "-B", str(HERE/"replay_collective.py"), "--execute"],
                              capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("explicit manifest", proc.stderr)

    def test_rank_visible_and_loopback_negatives(self):
        self.assertEqual(R.execution_environment(self.env()), (0,0))
        for delta in ({"RANK":"4"},{"LOCAL_RANK":"1"},{"WORLD_SIZE":"8"},
                      {"LOCAL_WORLD_SIZE":"8"},{"RANK":"00"},
                      {"ASCEND_RT_VISIBLE_DEVICES":"4,5,6,7"},{"MASTER_ADDR":"10.0.0.1"}):
            with self.assertRaises(ValueError):
                R.execution_environment(dict(self.env(), **delta))

    def test_complete_manifest_no_device(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);m=self.fixture(root)
            result, raw, refs = R.validate_manifest(self.manifest_ref(root,m), 3)
            self.assertEqual(result,m)
            self.assertEqual(len(raw),R.TENSOR_BYTES)
            self.assertEqual(len(refs),12)

    def test_wrong_model_generation_dtype_and_mapping_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);m=self.fixture(root)
            for delta in ({"generation":2},{"iterations":7},{"dtype":"torch.float16"},
                          {"shape":[8,5120]},{"physical_to_logical":[[0,0],[1,1],[2,2],[3,3]]}):
                with self.assertRaises(ValueError):
                    R.validate_manifest(self.manifest_ref(root,dict(m,**delta)),0)

    def test_changed_input_and_truncated_input_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);m=self.fixture(root);mr=self.manifest_ref(root,m)
            p=Path(m["inputs"]["0"]["path"]);p.write_bytes(b"x")
            with self.assertRaises(ValueError):R.validate_manifest(mr,0)

    def test_duplicate_rank_record_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);m=self.fixture(root)
            m["projection_records"][1]=m["projection_records"][0]
            with self.assertRaises(ValueError):R.validate_manifest(self.manifest_ref(root,m),0)

    def test_nonfinite_actual_word_rejected_even_rehashed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);m=self.fixture(root)
            p=Path(m["inputs"]["0"]["path"]);p.write_bytes(b"\x80\x7f"+bytes(R.TENSOR_BYTES-2))
            ref=R.file_ref(p);m["inputs"]["0"]=ref
            rp=Path(m["projection_records"][0]["path"]);rec=json.loads(rp.read_bytes())
            rec["record"]["stages"]["pre_reduce"].update(raw=ref,sha256=ref["sha256"])
            rp.write_text(json.dumps(rec));m["projection_records"][0]=R.file_ref(rp)
            with self.assertRaisesRegex(ValueError,"finite original"):
                R.validate_manifest(self.manifest_ref(root,m),0)

    def test_worker_ref_and_producer_source_join_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);m=self.fixture(root)
            wrong=copy.deepcopy(m);wrong["worker_ref"]["sha256"]="0"*64
            with self.assertRaises(ValueError):R.validate_manifest(self.manifest_ref(root,wrong),0)
            rp=Path(m["projection_records"][0]["path"]);rec=json.loads(rp.read_bytes())
            rec["source_sha256"]="f"*64;rp.write_text(json.dumps(rec))
            m["projection_records"][0]=R.file_ref(rp)
            with self.assertRaises(ValueError):R.validate_manifest(self.manifest_ref(root,m),0)

    def test_symlink_ref_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);(p/"real").write_bytes(b"x");(p/"link").symlink_to(p/"real")
            with self.assertRaises(ValueError):R.file_ref(p/"link")

    def test_exclusive_output_preserves_first(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"post.bin";R.write_file(p,b"first")
            with self.assertRaises(FileExistsError):R.write_file(p,b"second")
            self.assertEqual(p.read_bytes(),b"first")

    def test_variant_whitelist_and_no_secret_export(self):
        torch=types.SimpleNamespace(are_deterministic_algorithms_enabled=lambda:False,
                                   is_deterministic_algorithms_warn_only_enabled=lambda:False)
        with patch.dict(os.environ,{"PRIVATE_SECRET":"do-not-export"},clear=True):
            flags=R.runtime_flags(torch,"default")
            self.assertNotIn("do-not-export",json.dumps(flags))
            self.assertIsNone(flags["environment"]["HCCL_DETERMINISTIC"])
            with self.assertRaises(ValueError):R.runtime_flags(torch,"deterministic_true")
        with patch.dict(os.environ,{"HCCL_DETERMINISTIC":"true"},clear=True):
            self.assertEqual(R.runtime_flags(torch,"deterministic_true")["environment"]["HCCL_DETERMINISTIC"],"true")
            with self.assertRaises(ValueError):R.runtime_flags(torch,"default")

    def test_manifest_failure_retains_primary_without_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);bad=dict(path=str(root/"missing"),bytes=0,sha256="0"*64)
            with patch.dict(os.environ,self.env(),clear=True):
                self.assertEqual(R.run(bad,root),1)
            result=json.loads((root/"rank-0"/"RESULT.json").read_bytes())
            self.assertFalse(result["completed"] or result["NPU_executed"])
            self.assertIsNotNone(result["primary"])
            self.assertFalse(result["candidate_qualification"])
            with patch.dict(os.environ,self.env(),clear=True):
                with self.assertRaises(FileExistsError):R.run(bad,root)

    def test_import_first_fault_preserved_with_input_recheck_failure(self):
        import builtins
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);m=self.fixture(root);mr=self.manifest_ref(root,m)
            original_import=builtins.__import__
            def failed_import(name,*args,**kwargs):
                if name == "torch":
                    Path(m["inputs"]["0"]["path"]).write_bytes(b"changed-after-validation")
                    raise RuntimeError("fixture first import fault")
                return original_import(name,*args,**kwargs)
            with patch.dict(os.environ,self.env(),clear=True), patch("builtins.__import__",failed_import):
                self.assertEqual(R.run(mr,root),1)
            result=json.loads((root/"rank-0"/"RESULT.json").read_bytes())
            self.assertEqual(result["primary"]["message"],"fixture first import fault")
            self.assertIsNotNone(result["input_recheck_error"])
            self.assertFalse(result["input_refs_rechecked"] or result["completed"] or result["NPU_executed"])

    def test_actual_python_wrapper_chain_sources(self):
        import functools
        def core():pass
        @functools.wraps(core)
        def wrapper():return core()
        observed=R.callable_source(wrapper)
        self.assertEqual(len(observed["python_wrapper_chain"]),2)
        self.assertTrue(all(len(row["code_sha256"])==64 for row in observed["python_wrapper_chain"]))


if __name__ == "__main__":
    unittest.main()
