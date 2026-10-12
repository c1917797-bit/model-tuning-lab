import copy
import json
from pathlib import Path
import unittest
from verify_r19_final_quality_report import audit_text

FACTS = json.loads("[{\"audit_sha256\":\"40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b\",\"correct\":[227,219],\"dataset\":\"longbench\",\"decision\":\"REJECT_OR_QUALIFY\",\"delta_pp\":-2.099737532808399,\"device_execution\":false,\"length\":[49,67],\"means_pct\":[59.58005249343832,57.48031496062992],\"paired_wins_losses\":[15,23],\"per_run_samples\":127,\"provenance\":[{\"arm_result_sha256\":\"a37204901a95768121e116e72a3978ee64865ca085b09b4993265431133c200d\",\"attestation_sha256\":\"c67ceb8ed8388416e620f1c95b04dbde0d55699c339eece25091f1564e38bc22\",\"container_id\":\"f976bcebe9953925133bc8adec19e2716058167f35c170e929afecba04c7f197\",\"contract_sha256\":\"2071d4d80e2496d9d3bc583e8c87d0f0d6d790c0efdd1f59195214ff0f5f4154\",\"exact_release_replayed\":true,\"guard_samples\":865,\"root\":\"/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-full-baseline\"},{\"arm_result_sha256\":\"c1b7283c8d46ffb330af3be35232703d9b935819813a68288eb02b0608abdb74\",\"attestation_sha256\":\"6d60986406beef14be49b1375d805be635ef7709d94762652056c286503d4a35\",\"container_id\":\"1e186957c93fbc94e5188c2fe1a8d6fd8c60ffbb11109c833283d347ea5eca68\",\"contract_sha256\":\"68b518b42260ec5ca9843d91242768f212b7157b1deb9245bbc2c9ac72e8c2ab\",\"exact_release_replayed\":true,\"guard_samples\":997,\"root\":\"/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-full-hypic\"}],\"raw_rows_rescored\":true,\"runs\":[[74,77,76],[73,70,76]],\"sample_sd_pp\":[1.2027757729542865,2.362204724409448],\"scored_rows_per_arm\":381,\"source\":\"4429e35177979c874bf053ab29789e4773f39b22\"},{\"audit_sha256\":\"496f1dfacb3c3a8dd03f8ee07368fb142b432498c0ee5dbb5722e1d4f85fd187\",\"correct\":[3838,3840],\"dataset\":\"gsm8k\",\"decision\":\"PASS\",\"delta_pp\":0.05054334091483447,\"device_execution\":false,\"length\":[28,27],\"means_pct\":[96.99267121556736,97.04321455648218],\"paired_wins_losses\":[12,10],\"per_run_samples\":1319,\"provenance\":[{\"arm_result_sha256\":\"03a2093873b2dbf3a0f675c7d0d47d83cadd0389192e10fb491ca03525ece897\",\"attestation_sha256\":\"cb03725476b63a1759fce6a33d765d314f3a57f8b7cda319489ebfdbf1b9f09d\",\"container_id\":\"748ff800682d5f085fea77d7cb2b403f7bff18dca9d98bc536b07da9ca48ae98\",\"contract_sha256\":\"8f76b216800c8f75b293ca91aeeec3422e881126bfe79391484d897aed48b20e\",\"exact_release_replayed\":true,\"guard_samples\":991,\"root\":\"/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-gsm8k-baseline\"},{\"arm_result_sha256\":\"3814b62c948bdc275cc3ef221678191c1160b97dbe2f7907c545f89f108dfa9b\",\"attestation_sha256\":\"a7bf16215c534ef7de559a4eaca926fc819be948af895049914a530c5c31fb28\",\"container_id\":\"886d5fb47f380095527904b66e3936d3393051dea5e627434270ac031a6bb4a2\",\"contract_sha256\":\"334804779b3f9331574c2a29c5f2f4e0568481ffb152842c9c36125a4c0e7cf5\",\"exact_release_replayed\":true,\"guard_samples\":990,\"root\":\"/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-gsm8k-hypic\"}],\"raw_rows_rescored\":true,\"runs\":[[1280,1274,1284],[1281,1279,1280]],\"sample_sd_pp\":[0.3815938557124484,0.07581501137225644],\"scored_rows_per_arm\":3957,\"source\":\"4429e35177979c874bf053ab29789e4773f39b22\"}]")
REPORT = Path(__file__).with_name("HYPIC_R19_FINAL_QUALITY_REPORT_20261012.md")

class ReportingRegression(unittest.TestCase):
    def test_actual_report_matches_facts(self):
        self.assertTrue(audit_text(REPORT.read_text(), FACTS))

    def test_rejects_counterexamples(self):
        good = REPORT.read_text()
        replacements = [
            ("| 219/381 |", "| 220/381 |"),
            ("-2.099738", "+2.099738"),
            ("59.580052 ± 1.202776", "59.580052 ± 0.000000"),
            ("40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b", "wrong-hash"),
            ("HYPIC_R19_ARM=no-cache", "HYPIC_R19_ARM=hypic-only"),
            ("off-path", "in-path"),
            ("同源码性能未测", "当前源码性能通过"),
            ("不是整个三阶段目标完成", "整个三阶段目标完成"),
            ("精确释放", "未经核验释放"),
        ]
        for old, new in replacements:
            with self.subTest(old=old):
                self.assertIn(old, good)
                with self.assertRaises(RuntimeError):
                    audit_text(good.replace(old, new), FACTS)

    def test_rejects_placeholder(self):
        with self.assertRaises(RuntimeError):
            audit_text(REPORT.read_text() + "\nTODO\n", FACTS)

    def test_rejects_changed_raw_summary(self):
        facts = copy.deepcopy(FACTS)
        facts[0]["correct"][1] += 1
        with self.assertRaises(RuntimeError):
            audit_text(REPORT.read_text(), facts)

if __name__ == "__main__":
    unittest.main()
