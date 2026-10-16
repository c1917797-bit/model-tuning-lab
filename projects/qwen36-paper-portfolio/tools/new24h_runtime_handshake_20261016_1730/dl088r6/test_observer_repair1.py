"""Actual old/new classify functions; fixtures do not qualify real ownership."""
import hashlib,importlib.util,pathlib,sys,types,unittest
from unittest import mock
P=pathlib.Path(__file__).resolve().parent
def module(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
G=module(P/'top_guard.py','repair1guard')
OLD=P.parent/'deltalog-diagnostic-bridge-owned-new48h-20261015-031'
class Tests(unittest.TestCase):
 def run_classify(self,first,tail=None,forbidden=None,parent=10,top='10 1 python\n',module=G):
  saved=[];calls=[];items=iter([first]+(tail if tail is not None else [dict(status='missing')]*3))
  def next_read(pid):calls.append(pid);return next(items)
  m=types.SimpleNamespace(DOCKER='/usr/bin/docker',save=lambda p,v:saved.append(v))
  lane=types.SimpleNamespace(active='own',a=types.SimpleNamespace(run_root=P),call=lambda *a:dict(exit_code=0,stdout=top),h=types.SimpleNamespace(gate_process=lambda pid:dict(cgroup='own',start_ticks=1)))
  with mock.patch.object(module,'snapshot',side_effect=next_read),mock.patch.object(module.time,'sleep',lambda x:None):
   try:v=module.classify(lane,12,parent,10,{10},forbidden or set(),m);return None,saved,calls
   except Exception as e:return e,saved,calls
 def test_actual_old_function_no_confirmation(self):
  old=module(OLD/'top_guard.py','old031guard');e,s,c=self.run_classify(dict(status='present',state='R',start_ticks=1,cgroup=''),module=old)
  self.assertIn('live top PID wrong owned cgroup',str(e));self.assertEqual(len(c),1);self.assertEqual(s,[])
 def test_wrong_cgroup_then_actual_independent_absence(self):
  first=dict(status='present',state='R',start_ticks=1,cgroup='',proc_fields={'cgroup':{'text':''}})
  e,s,c=self.run_classify(first);self.assertIsNone(e);self.assertEqual(len(c),4)
  self.assertEqual(s[0]['first'],first);self.assertEqual(s[-1]['classification'],'original-top-child-confirmed-departed');self.assertFalse(s[-1]['resource_release_authority'])
 def test_partial_first_retained_not_exit_proof(self):
  first=dict(status='partial',proc_fields={'stat':None,'cgroup':{'text':''}})
  e,s,c=self.run_classify(first);self.assertIsNone(e);self.assertEqual(s[0]['first'],first)
  e,s,c=self.run_classify(first,tail=[dict(status='partial')]);self.assertIsNotNone(e)
 def test_still_present_wrong_owned_or_reused_reject(self):
  first=dict(status='present',state='R',start_ticks=1,cgroup='')
  for cgroup,start in[('',1),('own',1),('foreign',2)]:
   e,s,c=self.run_classify(first,tail=[dict(status='present',state='R',start_ticks=start,cgroup=cgroup)]);self.assertIsNotNone(e)
 def test_all_protected_and_unknown_parent_reject(self):
  first=dict(status='missing')
  for kw in[dict(forbidden={12}),dict(parent=999)]:
   e,s,c=self.run_classify(first,**kw);self.assertIsNotNone(e);self.assertEqual(len(c),1)
 def test_fresh_top_presence_and_final_reappearance_reject(self):
  e,s,c=self.run_classify(dict(status='missing'),top='10 1 python\n12 10 bisheng\n');self.assertIsNotNone(e)
  e,s,c=self.run_classify(dict(status='missing'),tail=[dict(status='missing'),dict(status='missing'),dict(status='present',start_ticks=99)]);self.assertIsNotNone(e)
 def test_permission_never_becomes_missing(self):
  with mock.patch.object(G,'snapshot',side_effect=PermissionError('denied')):
   with self.assertRaises(PermissionError):G.classify(None,12,10,10,{10},set(),None)
 def test_original_math_and_all_consumers_unchanged(self):
  for n in('domain_entry.py','oracle.py','consume.py','consume_increment.py','qwen36_deltalog_fresh/primitives.py'):
   self.assertEqual((P/n).read_bytes(),(OLD/n).read_bytes(),n)
if __name__=='__main__':unittest.main()
