"""SYNTHETIC stdlib successor contracts; no real kernel/load/graph/PASS authority."""
import copy,json,sys,unittest
from unittest.mock import patch
from contract import FINITE_BUFFERS,FINITE_SCOPE,NAMESPACE,validate_cases,protocol
import run,meta_probe

def fixture(batch):
    report={"schema":"kvbp.split-native-gate/v2","status":"single_batch_kernel_native_eager_graph_pass",
            "finite_scope":FINITE_SCOPE,"candidate_namespace":NAMESPACE,"cases":[]}
    for mode,trial in (("eager",0),("graph",0),("graph",1),("graph",2)):
        lengths=[0]*(batch+3);rows=[];merges=0
        for i in range(160):
            active=(0,1,3,7,12,15,16,16)[i%8] if mode=="graph" and batch==16 else batch
            reset=(i//16)%(batch+3) if i in (64,112) else None
            if reset is not None:lengths[reset]=0
            for token in range(active):
                slot=(token+i)%(batch+3)
                if lengths[slot]==15:merges+=1;lengths[slot]=0
                else:lengths[slot]+=1
            row={"step":i+1,"active":active,"reset_slot":reset,"output_error":0.,
                 "complete_state_l2":0.,"max_per_head_l2":0.,"passed":True,
                 "all_logs_bitwise_outside_new_U":{n:True for n in
                                                 ("k_log","u_log","lambda_log","decay","length")},
                 "finite_scope":FINITE_SCOPE,"finite_buffer_checks":{n:True for n in FINITE_BUFFERS},
                 "native_expected_defined_rows":active,
                 "native_expected_undefined_padding_rows":batch-active,
                 "native_padding_values_rewritten":False,
                 "raw_step":{"file":"raw-step-b%d-%s-t%d-step%d.pt"%(batch,mode,trial,i+1),
                             "step":i+1,"retained":False,"bytes":1,"sha256":"1"*64}}
            for name in ("untouched_slots_bitwise","nonflush_base_bitwise","guards","pointers",
                         "input_immutable","zero_length_output_zero","finite","metric_finite"):
                row[name]=True
            rows.append(row)
        report["cases"].append({"batch":batch,"mode":mode,"trial":trial,"status":"passed",
                                "steps":rows,"resets":2,"merges":merges,
                                "max_output_error":0.,"max_state_l2":0.,"max_head_l2":0.})
    return report

class SourceContracts(unittest.TestCase):
    def test_synthetic_complete_b1_b16_not_operation_authority(self):
        for b in (1,16):
            d=validate_cases(fixture(b),b)
            self.assertEqual(d["changing_feedback_steps"],640)
            self.assertFalse(d["operation_authority_verified"])
            self.assertFalse(d["serving_ready"])
    def reject(self,change):
        r=fixture(16);change(r)
        with self.assertRaises(ValueError):validate_cases(r,16)
    def test_old_v1_report_not_retro_promoted(self):
        self.reject(lambda r:r.update(schema="kvbp.split-native-gate/v1"))
    def test_old_namespace_not_promoted(self):
        self.reject(lambda r:r.update(candidate_namespace="qwen36_kvbuffer_parallel_fp32"))
    def test_changed_scope_rejected(self):
        self.reject(lambda r:r["cases"][1]["steps"][0].update(finite_scope="full-native-output-v1"))
    def test_active_domain_must_match_exact_schedule(self):
        self.reject(lambda r:r["cases"][1]["steps"][0].update(native_expected_defined_rows=1))
    def test_candidate_full_finite_remains_required(self):
        self.reject(lambda r:r["cases"][1]["steps"][0]["finite_buffer_checks"].update(actual_all=False))
    def test_native_full_state_finite_remains_required(self):
        self.reject(lambda r:r["cases"][1]["steps"][0]["finite_buffer_checks"].update(native_state_all=False))
    def test_complete_logs_finite_keys_required(self):
        self.reject(lambda r:r["cases"][0]["steps"][0]["finite_buffer_checks"].pop("state.lambda_log"))
    def test_native_output_not_rewritten(self):
        self.reject(lambda r:r["cases"][1]["steps"][0].update(native_padding_values_rewritten=True))
    def test_original_output_limit_unchanged(self):
        self.reject(lambda r:r["cases"][0]["steps"][0].update(output_error=.0030300001))
    def test_original_state_limit_unchanged(self):
        self.reject(lambda r:r["cases"][0]["steps"][0].update(complete_state_l2=2.000001e-6))
    def test_failed_raw_retained_cannot_promote(self):
        self.reject(lambda r:r["cases"][0]["steps"][0]["raw_step"].update(retained=True))
    def test_exact_160_and_three_graph(self):
        self.reject(lambda r:r["cases"][0]["steps"].pop())
        self.reject(lambda r:r["cases"].pop())
    def test_scope_protocol_does_not_change_old_math(self):
        p=protocol(1,5)
        self.assertEqual((p["steps_per_case"],p["graph_trials"],p["output_limit"],
                          p["complete_and_per_head_l2_limit"]),(160,3,.00303,2e-6))
        self.assertEqual(p["candidate_namespace"],NAMESPACE)
    def test_default_OFF_no_Torch(self):
        with patch("builtins.print") as out:run.main([])
        self.assertFalse(json.loads(out.call_args.args[0])["default_enabled"])
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)

    def test_meta_default_OFF_no_Torch(self):
        with patch("builtins.print") as out:meta_probe.main([])
        self.assertFalse(json.loads(out.call_args.args[0])["default_enabled"])
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)

if __name__=="__main__":unittest.main()
