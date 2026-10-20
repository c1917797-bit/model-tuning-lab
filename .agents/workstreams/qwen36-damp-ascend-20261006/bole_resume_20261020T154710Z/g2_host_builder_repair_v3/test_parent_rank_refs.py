"""Actual sibling rank inputs must be mounted explicitly; no broader directory."""
import copy,importlib.util,json
from pathlib import Path
import tempfile,unittest
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r3_builder',P/'prepare_g2_host_v3.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)


class Tests(unittest.TestCase):
 def fixture(self,change=None):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name);source={'source':1};refs=[]
  for rank in range(4):
   requests=[dict(rank=rank,generation=g,request='req%d'%g,output_token_ids=[7,11],actual_final_retirement_observed=True,component_checks_pass=True,actual_next_counter_acknowledgements=0,model_ready=False)for g in(1,2)]
   doc=dict(source=source,requests=requests)
   if change and rank==2:change(doc)
   path=root/('RANK-%d.json'%rank);B.write(path,doc);refs.append(B.ref(path))
  q=root/'ATTRIBUTION.json';B.write(q,dict(ranks=refs));return source,B.ref(q),refs
 def test_all_four_exact_actual_siblings_are_returned_for_dependencies(self):
  source,q,refs=self.fixture();self.assertEqual(B.parent_rank_reports(source,q),refs)
 def test_missing_report_fails_before_source_preparation(self):
  source,q,refs=self.fixture();Path(refs[1]['path']).unlink()
  with self.assertRaises(ValueError):B.parent_rank_reports(source,q)
 def test_wrong_source_rank_generation_retirement_math_or_request_identity_fails(self):
  mutations=[lambda d:d.update(source={'foreign':1}),lambda d:d['requests'][0].update(rank=3),
    lambda d:d['requests'][1].update(generation=1),lambda d:d['requests'][1].update(actual_final_retirement_observed=False),
    lambda d:d['requests'][0].update(component_checks_pass=False),lambda d:d['requests'][1].update(request='foreign')]
  for mutation in mutations:
   with self.subTest(mutation=mutation):
    source,q,refs=self.fixture(mutation)
    with self.assertRaises(ValueError):B.parent_rank_reports(source,q)
 def test_changed_actual_report_hash_is_rejected(self):
  source,q,refs=self.fixture();Path(refs[2]['path']).write_text('{}')
  with self.assertRaises(ValueError):B.parent_rank_reports(source,q)
 def test_symlink_report_is_rejected(self):
  source,q,refs=self.fixture();path=Path(refs[0]['path']);other=path.parent/'actual';path.rename(other);path.symlink_to(other)
  with self.assertRaises(ValueError):B.parent_rank_reports(source,q)


if __name__=='__main__':unittest.main()

class ClosureTests(unittest.TestCase):
 def fixture(self):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name)
  parent=root/'PARENT.json';B.write(parent,dict(files={}));parent_ref=B.ref(parent);ranks=[]
  for rank in range(4):
   path=root/('RANK-%d.json'%rank);B.write(path,dict(source=parent_ref,requests=[dict(rank=rank,generation=g,request='req%d'%g,output_token_ids=[7,11],actual_final_retirement_observed=True,component_checks_pass=True,actual_next_counter_acknowledgements=0,model_ready=False)for g in(1,2)]));ranks.append(B.ref(path))
  q=root/'ATTRIBUTION.json';B.write(q,dict(ranks=ranks));qref=B.ref(q)
  owner=root/'OWNER.json';B.write(owner,{});oref=B.ref(owner)
  current=root/'CURRENT.json';B.write(current,dict(g2_predecessor=dict(source=parent_ref,owner_result=oref,qualification=qref)))
  historical=root/'HISTORICAL.py';historical.write_text('exact original helper\n');href=B.ref(historical)
  return B.ref(current),parent_ref,[href],[href,parent_ref,oref,qref,*ranks]
 def test_missing_rank_inputs_are_detected_before_any_CPU_container(self):
  from unittest.mock import patch
  sr,parent,historical,full=self.fixture()
  with patch.object(B,'source_readset',side_effect=lambda r:historical if r==parent else full[:-4]):
   with self.assertRaisesRegex(ValueError,'closure missing'):B.audit_prerequisite_closure(sr)
 def test_complete_exact_parent_software_and_validation_readset_closes(self):
  from unittest.mock import patch
  sr,parent,historical,full=self.fixture()
  with patch.object(B,'source_readset',side_effect=lambda r:historical if r==parent else full):
   result=B.audit_prerequisite_closure(sr)
  self.assertEqual(result['missing'],[]);self.assertEqual(len(result['independently_validated_parent_rank_reports']),4)
  self.assertFalse(result['directory_mounts_added'])
