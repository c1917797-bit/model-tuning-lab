import ast,copy,json,unittest
from pathlib import Path
from unittest.mock import patch
import lifecycle_delivery_r16_tp4 as controller
import test_audit_lifecycle_startup_controls as startup_fixture
import test_audit_lifecycle_sequence as sequence_fixture
from audit_delivery_lifecycle_startup_controls import audit_startup_controls
from audit_delivery_lifecycle_sequence import audit_sequence_records
CHECKS=json.loads("{\"lifecycle_delivery_r16_tp4.py\":{\"base\":\"lifecycle_r16_tp4.py\",\"changes\":[[\"CONTRACT = HERE / \\\"LIFECYCLE_R16_CONTRACT.json\\\"\",\"CONTRACT = HERE / \\\"LIFECYCLE_DELIVERY_R16_CONTRACT.json\\\"\"],[\"    stage,treatment_on=lifecycle_mode(contract)\",\"    if contract.get(\\\"delivery_adapter\\\")is not True:raise ValueError(\\\"explicit delivery adapter lifecycle contract required\\\")\\n    stage,treatment_on=lifecycle_mode(contract)\"],[\"bootstrap=\\\"compact_bootstrap\\\" if diagnostic.get(\\\"compact_manifest\\\") else \\\"diagnostic_bootstrap\\\"\",\"bootstrap=\\\"delivery_runtime\\\" if diagnostic.get(\\\"compact_manifest\\\") else \\\"diagnostic_bootstrap\\\"\"]]},\"audit_delivery_lifecycle_startup_controls.py\":{\"base\":\"audit_lifecycle_startup_controls.py\",\"changes\":[[\"    stage=c.get(\\\"lifecycle_stage\\\");\",\"    if c.get(\\\"delivery_adapter\\\")is not True:raise ValueError(\\\"explicit delivery adapter lifecycle required\\\")\\n    stage=c.get(\\\"lifecycle_stage\\\");\"],[\"/probe/compact_bootstrap:/probe:\",\"/probe/delivery_runtime:/probe:\"]]},\"audit_delivery_lifecycle_terminal.py\":{\"base\":\"audit_lifecycle_terminal.py\",\"changes\":[[\"from audit_lifecycle_startup_controls import\",\"from audit_delivery_lifecycle_startup_controls import\"],[\"\\\"lifecycle_r16_tp4.py\\\"\",\"\\\"lifecycle_delivery_r16_tp4.py\\\"\"],[\"    stage,on=lifecycle_mode(c);\",\"    if c.get(\\\"delivery_adapter\\\")is not True:raise ValueError(\\\"explicit delivery adapter lifecycle required\\\")\\n    stage,on=lifecycle_mode(c);\"]]},\"audit_delivery_lifecycle_sequence.py\":{\"base\":\"audit_lifecycle_sequence.py\",\"changes\":[[\"from audit_lifecycle_terminal import\",\"from audit_delivery_lifecycle_terminal import\"],[\"IDENTITY=(\\\"image\\\",\",\"IDENTITY=(\\\"delivery_adapter\\\",\\\"image\\\",\"],[\"    contracts=[s[\\\"contract\\\"]for s in stages];base=contracts[0]\",\"    contracts=[s[\\\"contract\\\"]for s in stages];base=contracts[0]\\n    if base.get(\\\"delivery_adapter\\\")is not True:raise ValueError(\\\"explicit delivery adapter lifecycle required\\\")\"]]}}")
class Tests(unittest.TestCase):
    def test_only_declared_source_spans(self):
        for name,spec in CHECKS.items():
            old=Path(spec["base"]).read_text();new=Path(name).read_text()
            for before,after in spec["changes"]:
                self.assertEqual(new.count(after),1,(name,after));new=new.replace(after,before)
            a=ast.parse(old);b=ast.parse(new)
            self.assertEqual(ast.dump(ast.Module(body=a.body[1:],type_ignores=[])),ast.dump(ast.Module(body=b.body[1:],type_ignores=[])),name)
    def test_missing_explicit_delivery_contract_fails_before_devices(self):
        with patch.object(controller,"snapshot",side_effect=AssertionError("device check reached")):
            with self.assertRaisesRegex(ValueError,"explicit delivery"):controller.run_contract({})
    def startup(self,stage):
        a=startup_fixture.Tests().fixture(stage);a[1]["delivery_adapter"]=True
        for w in a[0]["workers"]:
            if w["controls"]["PYTHONPATH"]:w["controls"]["PYTHONPATH"]=w["controls"]["PYTHONPATH"].replace("/probe/compact_bootstrap:","/probe/delivery_runtime:")
        a[4]["argv"]=[x.replace("/probe/compact_bootstrap:","/probe/delivery_runtime:")for x in a[4]["argv"]]
        return a
    def test_three_startup_stages(self):
        for stage in ("disabled","enabled","uninstalled"):self.assertTrue(audit_startup_controls(*self.startup(stage),package_root="/pkg")["startup_controls_verified"])
    def test_legacy_bootstrap_rejected(self):
        a=self.startup("enabled");a[4]["argv"]=[x.replace("/probe/delivery_runtime:","/probe/compact_bootstrap:")for x in a[4]["argv"]]
        with self.assertRaises(ValueError):audit_startup_controls(*a,package_root="/pkg")
    def test_startup_missing_explicit_flag(self):
        a=self.startup("enabled");a[1].pop("delivery_adapter")
        with self.assertRaises(ValueError):audit_startup_controls(*a,package_root="/pkg")
    def test_sequence(self):
        rows=sequence_fixture.Tests().fixture()
        for r in rows:r["contract"]["delivery_adapter"]=True
        self.assertTrue(audit_sequence_records(rows)["lifecycle_sequence_audited"])
    def test_sequence_legacy_contract_rejected(self):
        rows=sequence_fixture.Tests().fixture()
        with self.assertRaises(ValueError):audit_sequence_records(rows)
if __name__=="__main__":unittest.main()
