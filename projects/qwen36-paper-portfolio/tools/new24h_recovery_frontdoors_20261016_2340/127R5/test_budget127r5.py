import ast,base64,hashlib,json,pathlib,subprocess,sys,unittest
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import clock127r4 as C,timing_transform127r5 as T
class BudgetTests(unittest.TestCase):
 def test_dynamic_clock(self):
  p=json.loads((P/'BUDGET_PROFILE127R5.json').read_bytes());C.profile({'cpu_budget_profile':p})
  self.assertEqual(C.child_cap(3600,p,now=420),2700)
  self.assertEqual(C.child_cap(3600,p,now=500),2620)
  with self.assertRaises(ValueError):C.child_cap(3600,p,now=3120)
  with self.assertRaises(ValueError):C.remaining(3600,now=3600)
 def test_no_budget_mutation(self):
  p=json.loads((P/'BUDGET_PROFILE127R5.json').read_bytes())
  for key,value in [('cleanup_reserve_seconds',89),('final_fence_reserve_seconds',299),('predicted_child_seconds',2701),('safety_margin_seconds',89)]:
   bad=dict(p);bad[key]=value
   with self.assertRaises(ValueError):C.profile({'cpu_budget_profile':bad})
 def test_full_math_inverse(self):
  f=json.loads((P/'FROZEN_TEST_INPUTS127R4.json').read_bytes())['original/run_consumer088.py'];raw=base64.b64decode(f['base64'])
  self.assertEqual(hashlib.sha256(raw).hexdigest(),f['ref']['sha256'])
  text=T.transform(raw);self.assertEqual(T.inverse(text),raw)
  for token in ['2*steps+31','2*steps+8',"transition['local_transition_pass']",'ledger[s],_=R.advance','memo.seal_initial','memo.finish()']:
   self.assertIn(token,text)
  with self.assertRaises(ValueError):T.transform(raw+b'\n')
 def test_fresh_isolated_entry(self):
  for script,args in [('run_recovery.py',['--phase','bind','--template-ref','{}']),('entry.py',['--stage','cpu-preflight','--source-ref','{}','--authority-ref','{}','--lifecycle-ref','{}','--output','unused'])]:
   r=subprocess.run([sys.executable,'-I','-B',str(P/script),'--execute',*args],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0)
   self.assertNotIn('ModuleNotFoundError',r.stderr)
 def test_all_body_inverse(self):
  edits=json.loads((P/'EDITS127R5.json').read_bytes())
  for n,pairs in edits.items():
   text=(P/n).read_text(encoding='utf8')
   for old,new in reversed(pairs):
    self.assertEqual(text.count(new),1,(n,new));text=text.replace(new,old)
   expected=json.loads((P/'PARENT_FILES127R5.json').read_bytes())[n]
   self.assertEqual(hashlib.sha256(text.encode('utf8')).hexdigest(),expected['sha256'],n)
 def test_host_clock_order(self):
  s=(P/'host.py').read_text(encoding='utf8');ast.parse(s)
  self.assertLess(s.index('started=time.monotonic();_WHOLE_DEADLINE'),s.index('root,m,C,refs,historical_root=target_closure'))
  self.assertIn("time.monotonic()-started<=CLOCK.PRE",s)
  self.assertIn("for r in refs:validate_ref_streamed(r)",s)
  self.assertIn("seal.final_verify(m['storage_seal_evidence_ref'])",s)
  self.assertIn('complete_final_fence=complete_final_fence',s)
  self.assertIn('registered_child_ceiling=2700',s)
  self.assertIn('started=a.whole_start;_WHOLE_DEADLINE=started+CLOCK.WHOLE',s)
  wrapper=(P/'run_recovery.py').read_text(encoding='utf8');self.assertLess(wrapper.index('whole_start=time.monotonic()'),wrapper.index('tr=json.loads'))
  self.assertIn("'--whole-start',str(whole_start)",wrapper)
  self.assertIn("budget_ref==t['files']['BUDGET_PROFILE127R5.json']and budget==t['cpu_budget_profile']",(P/'bind127.py').read_text(encoding='utf8'))
if __name__=='__main__':unittest.main()
