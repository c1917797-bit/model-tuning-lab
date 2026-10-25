"""CPU producer-format controls using the unchanged official formatter class."""
import ast
import hashlib
import logging
import unittest
from pathlib import Path
from types import SimpleNamespace
from host_audits import r30_graph_formal_audit as old
from host_audits import r30b_graph_formal_audit as new

FP=Path("/cache/docker/overlay2/b29985e3b73a9859aaf544b23e18d4e39ea967a853185fb3a72ec46c3d0752bf/diff/vllm-workspace/vllm/vllm/logging_utils/formatter.py")
def completion(mode):
    raw=FP.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==new.FORMATTER_SHA
    tree=ast.parse(raw,filename=str(FP))
    cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=="NewLineFormatter")
    ns={"logging":logging,"Path":Path,"envs":SimpleNamespace(VLLM_LOGGING_LEVEL=mode),"__file__":str(FP)}
    exec(compile(ast.Module(body=[cls],type_ignores=[]),str(FP),"exec"),ns)
    f=ns["NewLineFormatter"]("%(levelname)s 10-25 11:27:11 [%(fileinfo)s:%(lineno)d] %(message)s")
    path=FP.parent.parent/"compilation"/"monitor.py"
    r=logging.LogRecord("vllm",logging.INFO,str(path),53,"torch.compile took %.2f s in total",(1.0,),None)
    return "(Worker_TP0 pid=58) "+f.format(r)

def rows(mode="INFO"):
    return [f"(Worker_TP{i} pid={58+i}) INFO 10-25 11:26:00 [model_runner_v1.py:3718] Starting to load model /model..."for i in range(4)]+[
        completion(mode),"(Worker_TP0 pid=58) INFO 10-25 11:28:00 [acl_graph.py:243] Replaying aclgraph"]
def blob(r):return ("\n".join(r)+"\n").encode()

class OfficialInfoProducerTests(unittest.TestCase):
    def test_actual_same_info_record_global_formatter_counterfactual(self):
        self.assertIn("[monitor.py:53]",completion("INFO"))
        self.assertIn("[compilation/monitor.py:53]",completion("DEBUG"))
    def test_frozen_observer_preserved_rejects_actual_info(self):
        with self.assertRaises(ValueError):old.parse_info_graph(blob(rows()))
        self.assertEqual(old.parse_info_graph(blob(rows("DEBUG")))["workers"],{i:58+i for i in range(4)})
    def test_successor_accepts_actual_info_only(self):
        self.assertEqual(new.parse_info_graph(blob(rows()))["workers"],{i:58+i for i in range(4)})
        with self.assertRaises(ValueError):new.parse_info_graph(blob(rows("DEBUG")))
    def test_missing_replay_rejected(self):
        with self.assertRaises(ValueError):new.parse_info_graph(blob(rows()[:-1]))
    def test_missing_worker_rejected(self):
        with self.assertRaises(ValueError):new.parse_info_graph(blob(rows()[1:]))
    def test_foreign_completion_pid_rejected(self):
        r=rows();r[-2]=r[-2].replace("pid=58","pid=99")
        with self.assertRaises(ValueError):new.parse_info_graph(blob(r))
    def test_completion_after_replay_rejected(self):
        r=rows();r[-2:]=r[-2:][::-1]
        with self.assertRaises(ValueError):new.parse_info_graph(blob(r))
    def test_extra_rank_completion_rejected(self):
        r=rows();r[-2]=r[-2].replace("Worker_TP0","Worker_TP1").replace("pid=58","pid=59")
        with self.assertRaises(ValueError):new.parse_info_graph(blob(r))
    def test_missing_completion_rejected(self):
        r=rows();del r[-2]
        with self.assertRaises(ValueError):new.parse_info_graph(blob(r))

if __name__=="__main__":unittest.main()
