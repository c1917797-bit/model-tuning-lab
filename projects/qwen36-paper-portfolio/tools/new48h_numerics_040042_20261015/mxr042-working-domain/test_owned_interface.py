import ast,importlib.util,unittest,subprocess,sys,json
from pathlib import Path
P=Path(__file__).resolve().parent
class Owned(unittest.TestCase):
 def test_default_off_parent_cpu(self):
  for name in('mainhost.py','cpu_preflight.py'):
   v=subprocess.run([sys.executable,'-I','-B',str(P/name)],capture_output=True,text=True,check=True);self.assertEqual(json.loads(v.stdout),dict(enabled=False,NPU=False))
 def test_exact_handshake4_not6(self):
  s=importlib.util.spec_from_file_location('_match019',P/'handshake_poll.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  device=dict(pid=9,stat='9 (x) S '+'0 '*18+'123 0')
  row=dict(pid=99,namespace_pids=[99,9],physical=4,start_ticks=123,cgroup='/docker/abc',argv=['real'])
  self.assertIs(m.match_or_wait(device,[row],expected_argv=['real'],cid='abc',child_running=True,now=1,deadline=2),row)
  self.assertIsNone(m.match_or_wait(device,[],expected_argv=['real'],cid='abc',child_running=True,now=1,deadline=2))
  with self.assertRaises(ValueError):m.match_or_wait(device,[dict(row,physical=6)],expected_argv=['real'],cid='abc',child_running=True,now=1,deadline=2)
 def test_budget_and_input_tokens_not_synthetic(self):
  source=(P/'mainhost.py').read_text();ast.parse(source)
  self.assertIn('NPU_seconds=900,CPU_seconds=600,cleanup_seconds=90,setup_reserve_seconds=810',source)
  self.assertNotIn('shape_matrix',source);self.assertNotIn('a.matrix',source)
if __name__=='__main__':unittest.main()
