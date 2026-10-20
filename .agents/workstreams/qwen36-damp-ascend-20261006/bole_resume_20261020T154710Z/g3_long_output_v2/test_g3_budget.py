"""Worst-case full-evidence admission, never capture-disabled success."""
from pathlib import Path
import sys
import tempfile
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import g2_contract as G
import g3_budget as B

class BudgetTests(unittest.TestCase):
 def fixture(self):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);base=Path(td.name);channel=base/'STREAM';channel.mkdir()
  cal=base/'CONV-MODEL-CALIBRATION-RANK-0';cal.mkdir()
  return base,channel,cal,dict(model_receipt_root=str(base),stream_channel_root=str(channel))
 def sized(self,path,n):
  with path.open('wb')as f:f.truncate(n)
 def test_full_worst1023_steps_with_terminal_failure_fit_original64MiB_and1GiB(self):
  r=B.reservation();self.assertEqual(r['max_success_events'],1026);self.assertEqual(r['terminal_failure_events'],1)
  self.assertEqual(r['maximum_metadata_bytes'],(1026+1)*(2048+3072+1536+4000)+(16+8+3+16)*2**20)
  self.assertLess(r['maximum_metadata_bytes'],64*2**20);self.assertEqual(r['logical_plus_serialized_plus_checkpoint_plus_metadata'],1024*2**20)
  self.assertEqual(r['logical_plus_serialized_plus_checkpoint_plus_metadata'],2**30)
 def test_complete_current_actual_evidence_including_pending_metadata_is_charged(self):
  base,ch,cal,m=self.fixture()
  for path,size in((cal/'RAW.pt',15000000),(base/'IDENTITY-rank0-000001.json',100),(ch/'FRAME-RANK-0-000000.json',100),
    (ch/'ACK-RANK-0-000000.json.pending',70),(ch/'CHANNEL.json',120),(base/'worker-13-snapshot-1.json',80),
    (base/'MTP-LOAD-1.json',90),(base/'BOLE-TREE-RANK-0.pt',150)):
   self.sized(path,size)
  value=B.actual(C,m,0,references=True)
  self.assertEqual(value['bytes'],15000710);self.assertEqual(len(value['references']),8)
  self.assertEqual(value['charges']['events'],170);self.assertEqual(value['charges']['other'],170)
 def test_calibration_keeps_original_algorithm_but_explicit16MiB_stream_allocation_must_fit(self):
  base,ch,cal,m=self.fixture();path=cal/'RAW.pt';self.sized(path,16*2**20+1)
  with self.assertRaisesRegex(ValueError,'allocations'):B.actual(C,m,0)
  self.assertTrue(path.is_file())
 def test_oversized_oracle_report_never_silently_releases_the_failed_frame(self):
  base,ch,cal,m=self.fixture();report=ch/'REPORT-RANK-0-001000.json';raw=ch/'FRAME-RANK-0-001000.pt'
  self.sized(report,4001);self.sized(raw,1)
  with self.assertRaisesRegex(ValueError,'metadata allocation'):B.actual(C,m,0)
  self.assertTrue(raw.is_file());self.assertTrue(report.is_file())
 def test_final_global_exit_and_worker_summary_are_included_with_hard_cap(self):
  base,ch,cal,m=self.fixture();self.sized(ch/'STREAM_CONSUMER_EXIT.json',16*2**20);self.sized(base/'BOLE-TREE-RANK-0.pt',1)
  with self.assertRaisesRegex(ValueError,'allocations'):B.actual(C,m,0)
 def test_symlink_evidence_fails_closed(self):
  base,ch,cal,m=self.fixture();target=base/'REAL';target.write_text('actual');(cal/'RAW.pt').symlink_to(target)
  with self.assertRaisesRegex(ValueError,'ordinary'):B.actual(C,m,0)

if __name__=='__main__':unittest.main()
