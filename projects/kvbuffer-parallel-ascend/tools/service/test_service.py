"""NO-device stdlib tests. These cannot certify runtime/NPU success."""
import ast
import copy
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import unittest
from contract import (COMMON, IMAGE, LIBRARY_SHA, PLUGIN_SHA, PROBE_SHA, TOTAL,
                      budget, digest, prompt_ids, summarize, validate_identity, validate_native_gate)
from bench import StreamState

class ServiceContractTests(unittest.TestCase):
    def gate(self):
        cases=[dict(batch=b,mode=m,trial=t,status="passed",merges=1,resets=2,
                    steps=[{"passed":True} for _ in range(160)])
               for m,ts in (("eager",(0,)),("graph",range(3))) for t in ts for b in (1,16)]
        return dict(schema="kvbp-parallel-fp32-native-gate/v1",
                    status="kernel_native_eager_graph_pass",script_sha256=PROBE_SHA,
                    library_sha256=LIBRARY_SHA,cases=cases)
    def test_full_matrix_required(self):
        validate_native_gate(self.gate())
        g=self.gate();g["cases"].pop()
        with self.assertRaises(ValueError):validate_native_gate(g)
    def test_meta_is_not_npu(self):
        g=self.gate();g["status"]="Meta_pass"
        with self.assertRaises(ValueError):validate_native_gate(g)
    def test_failed_step_rejected(self):
        g=self.gate();g["cases"][0]["steps"][10]["passed"]=False
        with self.assertRaises(ValueError):validate_native_gate(g)
    def test_budget_equal_and_max455(self):
        self.assertEqual(budget("dense")["common_total_bytes"],TOTAL)
        self.assertEqual(budget("candidate",455)["common_total_bytes"],TOTAL)
        with self.assertRaises(ValueError):budget("candidate",456)
    def test_prompts_exact_shared_prefix(self):
        prompts=[prompt_ids(i) for i in range(40)]
        self.assertTrue(all(len(p)==32768 for p in prompts))
        self.assertEqual(len({digest(p) for p in prompts}),40)
        self.assertEqual(len({digest(p[:16384]) for p in prompts}),1)
    def test_stream_empty_text_real_ids(self):
        s=StreamState([1,2],2)
        s.feed(json.dumps({"choices":[{"index":0,"text":"","prompt_token_ids":[1,2],
                    "token_ids":[7],"finish_reason":None}]}).encode(),1.)
        s.feed(json.dumps({"choices":[{"index":0,"text":"","token_ids":[8],
                    "finish_reason":"length"}]}).encode(),3.)
        s.feed(json.dumps({"choices":[],"usage":{"prompt_tokens":2,"completion_tokens":2,
                    "total_tokens":4}}).encode(),4.)
        s.feed(b"[DONE]",5.);s.finish_check()
        self.assertEqual((s.first,s.last),(1.,3.))
    def test_text_chunks_cannot_substitute(self):
        s=StreamState([1],1)
        with self.assertRaises(ValueError):
            s.feed(b'{"choices":[{"index":0,"text":"abc"}]}',1.)
    def test_no_usage_no_done_rejected(self):
        s=StreamState([1],1)
        s.feed(b'{"choices":[{"index":0,"prompt_token_ids":[1],"token_ids":[2],"finish_reason":"length"}]}',1.)
        with self.assertRaises(ValueError):s.finish_check()
    def test_cumulative_ids_rejected(self):
        s=StreamState([1],2)
        s.feed(b'{"choices":[{"index":0,"token_ids":[2]}]}',1.)
        with self.assertRaises(ValueError):s.feed(b'{"choices":[{"index":0,"token_ids":[2,3]}]}',2.)
    def test_wrong_prompt_rejected(self):
        with self.assertRaises(ValueError):
            StreamState([1],1).feed(b'{"choices":[{"index":0,"prompt_token_ids":[9],"token_ids":[2]}]}',1.)
    def test_identity_exact_device_and_common(self):
        ident=dict(schema="kvbp.service-identity/v1",image_id=IMAGE,physical_devices=[4,5,6,7],
                   logical_to_physical={"0":4,"1":5,"2":6,"3":7},fresh_idle_verified=True,
                   nonprivileged=True,source_canary_passed=True,native_gate_sha256="a"*64,
                   arm="dense",port=8246,common=COMMON,common_total_budget_bytes=TOTAL,
                   preflight_utc=datetime.now(timezone.utc).isoformat(),evidence={"fresh":"parent-receipt"})
        validate_identity(ident,"a"*64,"dense",8246)
        ident["preflight_utc"]=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()
        with self.assertRaises(ValueError):validate_identity(ident,"a"*64,"dense",8246)
        ident["preflight_utc"]=datetime.now(timezone.utc).isoformat()
        ident["physical_devices"]=[0,1,2,3]
        with self.assertRaises(ValueError):validate_identity(ident,"a"*64,"dense",8246)
    def test_frozen_source_pin_matches_known(self):
        self.assertEqual(PLUGIN_SHA,"71be0c99af19d66bc5f44ebb983b748cd56e2e776d567b0b4df0789ca0d89e2d")
    def test_observer_no_tensor_read_or_core_rebinding(self):
        path=Path(__file__).parent/"kvbuffer_service/evidence.py";text=path.read_text()
        ast.parse(text)
        self.assertNotIn(".detach(",text)
        self.assertNotIn(".synchronize(",text)
        self.assertNotIn("target._forward_core=",text)
        self.assertNotIn("cls._forward_core=",text)
        self.assertIn("return result",text)
    def test_client_raw_before_parser(self):
        text=(Path(__file__).parent/"bench.py").read_text()
        self.assertLess(text.index('stream.write(canonical(dict(receipt='),text.index('state.feed(line[6:]'))
        self.assertNotIn("streamed_chunks",text)
    def test_rank_pid_not_environment_rank(self):
        text=(Path(__file__).parent/"compare.py").read_text()
        self.assertIn('pid_rank[r["pid"]]==rank',text)
        self.assertNotIn('int(r["rank"])',text)
    def test_actual_common_guard_and_pointer_checks(self):
        text=(Path(__file__).parent/"kvbuffer_service/evidence.py").read_text()
        self.assertIn('require(actual_common==COMMON',text)
        self.assertIn('require(fingerprint()==base_pins',text)
        self.assertIn('require(actual_aux==aux_pins',text)
    def test_40_usage_required(self):
        with self.assertRaises(ValueError):summarize([],"token-ids")

if __name__=="__main__":unittest.main()
