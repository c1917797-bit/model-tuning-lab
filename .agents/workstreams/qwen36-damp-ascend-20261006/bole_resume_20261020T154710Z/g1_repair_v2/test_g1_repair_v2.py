"""Pure controls for exact new inverse/command scope; no Torch/device import."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sourceio as C
import command_contract as CC
import g1_inverse as GI
import prepare_g1_repair_v2 as B


class Tests(unittest.TestCase):
 def test_command_scope_rejects_stale_source_output_entrypoint_and_count(self):
  sr,template={'bound':1},{'template':1}
  m=dict(root='/new-v2',output_root='/new-output-v2',component_refs={'full':'actual'},
   service_required_sameimage_software_cases=214)
  history=dict(required_sameimage_software_cases=154)
  good=dict(schema='bole.G1-actual-bound-commands/v2',source=template,bound_source=sr,
   **CC.expected(m['root'],m['output_root'],sr,template,m['component_refs']),
   required_sameimage_software_cases=214,historical_required_sameimage_software_cases=154,
   actual_G1_execution_claimed=False,legacy_entrypoints_retained_for_inverse_tests_only=True)
  self.assertTrue(CC.validate_value(good,m,sr,template,history))
  for change in('source','bound_source','required_sameimage_software_cases','output','entry','CPU','bind'):
   bad=copy.deepcopy(good)
   if change in('source','bound_source'):bad[change]={'old':1}
   elif change=='required_sameimage_software_cases':bad[change]=154
   elif change=='output':bad['model'][-1]='/stale-output'
   elif change=='entry':bad['model'][6]='/old/host090.py'
   elif change=='CPU':bad['CPU']=good['model']
   else:bad['bind'][-1]='<PLACEHOLDER>'
   with self.assertRaises(ValueError):CC.validate_value(bad,m,sr,template,history)

 def test_exact_G1_inverse_rejects_undeclared_bytes_and_wrong_before_lineage(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);old=root/'V6';old.mkdir();(old/'runtime.py').write_text('original V6 bytes\n')
   baseline=C.write(old/'SOURCE_BOUND.json',dict(files={'runtime.py':C.ref(old/'runtime.py')}))
   (root/'runtime.py').write_text('approved G1 lifecycle bytes\n');current=C.ref(root/'runtime.py')
   failed={'failed_v1':1}
   row=dict(before=C.ref(old/'runtime.py'),after=current,edits=[dict(before=(old/'runtime.py').read_text(),after=(root/'runtime.py').read_text())])
   proof=C.write(root/'G1_LIFECYCLE_EDITS_V1.json',dict(schema='bole.exact-G1-lifecycle-inverse-to-passed-V6/v1',baseline_v6=baseline,failed_g1_v1=failed,files={'runtime.py':row}))
   m=dict(files={'runtime.py':current,'G1_LIFECYCLE_EDITS_V1.json':proof},g1_inverse=dict(baseline_v6=baseline,failed_g1_v1=failed))
   C.write(root/'SOURCE_TEMPLATE.json',m)
   with patch.object(GI,'P',root):
    self.assertEqual(GI.previous_text(root/'runtime.py'),(old/'runtime.py').read_text())
    with self.assertRaisesRegex(ValueError,'current source differs'):GI.reverse('runtime.py',(root/'runtime.py').read_text()+'# undeclared\n')
    # A freshly hashed forged inverse still cannot replace the baseline Ref bytes.
    value=C.obj(proof);value['files']['runtime.py']['edits'][0]['before']='forged original\n'
    (root/'G1_LIFECYCLE_EDITS_V1.json').unlink();m['files']['G1_LIFECYCLE_EDITS_V1.json']=C.write(root/'G1_LIFECYCLE_EDITS_V1.json',value)
    (root/'SOURCE_TEMPLATE.json').unlink();C.write(root/'SOURCE_TEMPLATE.json',m)
    with self.assertRaisesRegex(ValueError,'exact passed V6'):GI.previous_text(root/'runtime.py')

 def test_registry_layer_preserves_original_R10_edits_and_rejects_wrong_postimage(self):
  before=b'R10 registered state\n';original=b'R3 historical state\n';after=b'G1 generation registered state\n'
  h=lambda b:hashlib.sha256(b).hexdigest()
  plan=dict(before_sha256=h(original),after_sha256=h(before),edits=[dict(new_start=0,new_end=len(before),new=before.decode(),old=original.decode())])
  actual=B.registry_plan(plan,before,after)
  self.assertEqual(actual['edits'][:-1],plan['edits']);self.assertEqual(actual['before_sha256'],plan['before_sha256'])
  self.assertEqual(actual['after_sha256'],h(after))
  with self.assertRaises(ValueError):B.registry_plan(plan,before+b'undeclared',after)
  malformed=copy.deepcopy(plan);malformed['edits'][0]['new']='wrong old inverse'
  with self.assertRaises(ValueError):B.registry_plan(malformed,before,after)


if __name__=='__main__':unittest.main()
