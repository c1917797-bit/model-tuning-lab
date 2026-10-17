"""Registered new experiment clock; strict original historical clocks retained."""
import copy,difflib,hashlib,json,unittest
from pathlib import Path
import phase_budget_r21 as B,postconsume_recipe as C,postwork_verify as V
P=Path(__file__).resolve().parent

class Phase(unittest.TestCase):
 def test_actual_manifest_and_both_command_phase_registrations(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());cmd=json.loads((P/'COMMANDS_FINAL.json').read_bytes());B.manifest(m)
  self.assertEqual(cmd['whole_seconds'],3600);self.assertEqual(cmd['postconsumer']['whole_seconds'],3600)
  self.assertEqual(cmd['phase_budget_registration'],B.registration());self.assertEqual(m['phase_budget_registration'],B.registration())
  for key,value in(('phase_seconds',2700),('cleanup_seconds',180)):
   bad=copy.deepcopy(m);bad['budgets'][key]=value
   with self.assertRaises(ValueError):B.manifest(bad)
  bad=copy.deepcopy(m);bad['cutoff_epoch']+=1
  with self.assertRaises(ValueError):B.manifest(bad)

 def test_work_monotonic_and_absolute_cut_are_both_hard(self):
  self.assertEqual(B.WORK,2340);self.assertEqual(B.work_remaining(0,0,B.CUT-10000,B.CUT),2340)
  self.assertEqual(B.work_remaining(930,0,B.CUT-9070,B.CUT),1410)
  self.assertEqual(C.cap(2000,0,B.CUT-10000,B.CUT),340)
  self.assertEqual(C.cap(0,0,B.CUT-1300,B.CUT),40)
  for now,wall,cut in((2340,B.CUT-10000,B.CUT),(0,B.CUT-1260,B.CUT),(0,B.CUT-10000,B.CUT+1)):
   with self.assertRaises(ValueError):B.work_remaining(now,0,wall,cut)

 def test_post900_and_margin90_never_reset_whole_or_cut(self):
  self.assertEqual(V.available(2400,0,B.CUT-10000,B.CUT),900)
  self.assertEqual(V.available(3400,0,B.CUT-10000,B.CUT),110)
  self.assertEqual(V.available(0,0,B.CUT-200,B.CUT),110)
  for now,wall in((3510,B.CUT-10000),(0,B.CUT-90)):
   with self.assertRaises(ValueError):V.available(now,0,wall,B.CUT)

 def test_full_runtime_clock_body_inverse_and_original_deadline_dag(self):
  x=json.loads((P/'PHASE_EDITS_R21.json').read_bytes())
  self.assertEqual(set(x['files']),{'window_overlay.py','postconsume_recipe.py','postwork_verify.py'})
  for name,row in x['files'].items():
   before=''.join(difflib.restore(row['ndiff'],1)).encode();after=''.join(difflib.restore(row['ndiff'],2)).encode()
   self.assertEqual((len(before),hashlib.sha256(before).hexdigest()),(row['original_ref']['bytes'],row['original_ref']['sha256']))
   self.assertEqual(after,(P/name).read_bytes())
  donor=(P/'software_dependencies/donor008.py').read_text()
  for seam in('S.PHASE = PHASE','end=start + PHASE','start = time.monotonic()','time.time() + PHASE <= CUTOFF'):
   self.assertIn(seam,donor)
  safety=(P/'actual_loader/safety_host.py').read_text();self.assertIn('self.deadline=parent_start+PHASE',safety)
  for name in('prior_empty_r19.py','prior_released_empty_r20r1.py'):
   self.assertIn("owner['elapsed']<=2700",(P/name).read_text())

if __name__=='__main__':unittest.main()
