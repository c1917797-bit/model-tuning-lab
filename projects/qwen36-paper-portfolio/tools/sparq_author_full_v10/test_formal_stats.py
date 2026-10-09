"""Stdlib protocol/source regressions only, UNRUN until MAIN CPU lease."""
import ast,unittest
from pathlib import Path
class FormalProtocol(unittest.TestCase):
 def test_final_snapshot_after_client_timer_only(self):
  s=Path(__file__).with_name("host_run.py").read_text()
  self.assertLess(s.index('ctl.client.returncode==0'),s.index('ctl.call("formal-finalization"'))
  b=Path(__file__).with_name("bridge.py").read_text()
  self.assertIn('require(len(self.replay_calls)==1',b)
  self.assertIn('self.formal_replays+=len(self.replay_calls)',b)
 def test_no_dynamic_CPU_time_equal_identity_gate(self):
  s=Path(__file__).with_name("formal_stats.py").read_text()
  self.assertIn('("pid","start_ticks","cgroup","cmdline_sha256","argv")',s)
  self.assertNotIn('start["process"]==proc',s)
 def test_no_signal_reuse_or_global_handler_overwrite(self):
  s=Path(__file__).with_name("formal_stats.py").read_text()
  self.assertIn('signal.getsignal(signal.SIGUSR1)==signal.SIG_DFL',s)
  self.assertIn('not finalized and state.current is None',s)
  self.assertIn('not (root/("FORMAL_FINAL-r%d.json"%rank)).exists()',s)
 def test_original_nul_argv_protocol_and_AST(self):
  for n in ("bridge.py","formal_stats.py"):
   text=Path(__file__).with_name(n).read_text();ast.parse(text)
   self.assertNotIn('split("\\\\0")',text)
if __name__=="__main__":unittest.main()
