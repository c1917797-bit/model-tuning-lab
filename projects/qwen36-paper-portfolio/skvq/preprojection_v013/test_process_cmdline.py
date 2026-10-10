"""Exact original proc primitive + real 011 hash counterexample; software, no device authority."""
import argparse,ast,copy,hashlib,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import current_contract as C
import process_cmdline as P
REVIEW=None
OBS_REF={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-skvq-current72h-projection-011-main-20261010-001/OWNED_NPU_OBSERVATION-1791665614952592140.json","bytes":6896,"sha256":"92c76325d28dfa8e51343c4f88f0053736a57b6ec3715cc19c6724adf1a11d47"}
def actual_file(ref,name):
    p=Path(ref["path"])if REVIEW is None else REVIEW/name
    raw=p.read_bytes()
    C.require(len(raw)==ref["bytes"] and hashlib.sha256(raw).hexdigest()==ref["sha256"],
        "whole actual source/original bytes; not synthetic original")
    return p,raw
def original(proc):
    path,raw=actual_file(P.GATE_REF,"full_matrix_host.py")
    nodes={x.name:x for x in ast.parse(raw) .body if isinstance(x,ast.FunctionDef)}
    ns=dict(Path=lambda p:proc if str(p)=="/proc"else Path(p),hashlib=hashlib,require=C.require)
    for name in("start_ticks","process_identity","gate_process"):
        exec(compile(ast.Module(body=[nodes[name]],type_ignores=[]),str(path),"exec"),ns)
    h=types.SimpleNamespace(__file__=str(path),process_identity=ns["process_identity"],gate_process=ns["gate_process"])
    return h,C.reference(path.absolute())
class ExactProc(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.proc=self.root/"proc";leaf=self.proc/"123";leaf.mkdir(parents=True)
        (leaf/"stat").write_text("123 (actual software worker) S "+"0 "*18+"456 0 0\n")
        (leaf/"cgroup").write_text("0::/docker/"+"a"*64+"\n")
        (leaf/"status").write_text("NSpid:\t123\t7\n")
        (leaf/"cmdline").write_bytes(b"VLLM::Worker_TP0"+bytes([0])*138)
        self.h,self.gate_ref=original(self.proc)
        sp=self.root/"SOURCE.json";sp.write_text('{"software":true}\n');self.source=C.reference(sp.absolute())
        self.saved=[]
        def writer(label,value):
            p=self.root/(label+"-"+str(len(self.saved))+".json")
            p.write_text(json.dumps(value,sort_keys=True)+"\n");r=C.reference(p.absolute())
            self.saved.append((value,r));return r
        self.writer=writer
    def tearDown(self):self.tmp.cleanup()
    def capture(self):
        with patch.object(P,"GATE_REF",self.gate_ref),patch.object(P,"Path",lambda p:self.proc if str(p)=="/proc"else Path(p)):
            proof=P.capture(self.h,123,self.source,self.writer)
            return proof,self.saved[-1][0]
    def consume(self,value,proof):
        with patch.object(P,"GATE_REF",self.gate_ref):return P.consume(value,proof,self.source)
    def test01_actual011_single_nul_counterexample_all4_not_promoted(self):
        _,raw=actual_file(OBS_REF,"OWNED_NPU_OBSERVATION-1791665614952592140.json")
        rows=json.loads(raw)["proofs"];self.assertEqual(len(rows),4)
        for p in rows:
            one=bytes([0]).join(s.encode()for s in p["argv"])+bytes([0])
            self.assertNotEqual(hashlib.sha256(one).hexdigest(),p["cmdline_sha256"])
            # This reconstruction demonstrates the reported padding ONLY; it is not an original raw Ref.
            known=bytes([0]).join(s.encode()for s in p["argv"])+bytes([0])*138
            self.assertEqual(hashlib.sha256(known).hexdigest(),p["cmdline_sha256"])
            self.assertNotIn("actual_cmdline_raw_ref",p)
    def test02_original_gate_body_filters_empty_but_keeps_entire_digest(self):
        proof=self.h.gate_process(123)
        self.assertEqual(proof["argv"],["VLLM::Worker_TP0"])
        self.assertEqual(proof["cmdline_sha256"],hashlib.sha256((self.proc/"123/cmdline").read_bytes()).hexdigest())
        self.assertEqual(proof["namespace_pids"],[123,7])
    def test03_production_capture_real_source_original_gate_and_independent_replay(self):
        proof,value=self.capture()
        self.assertEqual(self.consume(value,proof),value["original_gate"])
        self.assertEqual(C.checked(proof["actual_cmdline_raw_ref"]),proof["actual_cmdline_raw_ref"])
        self.assertEqual(value["raw_bytes"],len(b"VLLM::Worker_TP0")+138)
        self.assertEqual(value["before"],value["after"])
    def test04_arbitrary_recorded_padding_and_internal_empty_segments_not_policy(self):
        for raw in(b"worker\0",b"worker"+bytes([0])*141,b"worker\0\0argument\0\0"):
            (self.proc/"123/cmdline").write_bytes(raw)
            proof,value=self.capture();self.assertEqual(self.consume(value,proof)["argv"],[x.decode()for x in raw.split(b"\0")if x])
    def test05_truncation_extra_nul_and_interior_change_refused(self):
        proof,value=self.capture()
        raw=bytes.fromhex(value["raw_hex"])
        for changed in(raw[:-1],raw+b"\0",b"VLLM\0"+raw[5:]):
            bad=copy.deepcopy(value);bad.update(raw_hex=changed.hex(),raw_bytes=len(changed),raw_sha256=hashlib.sha256(changed).hexdigest())
            with self.assertRaises(ValueError):self.consume(bad,proof)
    def test06_pid_reuse_start_and_cgroup_drift_refused(self):
        proof,value=self.capture()
        for key,changed in(("pid",124),("start_ticks",457),("cgroup","0::/foreign")):
            bad=copy.deepcopy(value);bad["after"][key]=changed
            with self.assertRaises(ValueError):self.consume(bad,proof)
    def test07_original_proof_argv_or_namespace_tamper_refused(self):
        proof,value=self.capture()
        for key,changed in(("argv",["foreign"]),("namespace_pids",[124,7]),("cmdline_sha256","b"*64)):
            bad=dict(proof);bad[key]=changed
            with self.assertRaises(ValueError):self.consume(value,bad)
    def test08_raw_hex_size_bool_unknown_keys_refused(self):
        proof,value=self.capture()
        for bad in(dict(value,raw_bytes=True),dict(value,raw_bytes=value["raw_bytes"]+1),dict(value,origin="unknown"),
                    dict(value,raw_hex=value["raw_hex"].upper()),dict(value,raw_hex="zz"*value["raw_bytes"])):
            with self.assertRaises(ValueError):self.consume(bad,proof)
    def test09_wrong_current_source_or_primitive_refused(self):
        proof,value=self.capture()
        for field in("source_ref","primitive_ref"):
            bad=copy.deepcopy(value);bad[field]["sha256"]="b"*64
            with self.assertRaises(ValueError):self.consume(bad,proof)
    def test10_false_single_nul_reconstruction_never_accepted(self):
        proof,value=self.capture();raw=b"VLLM::Worker_TP0\0"
        bad=dict(value,raw_hex=raw.hex(),raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest())
        with self.assertRaises(ValueError):self.consume(bad,proof)
    def test11_unknown_empty_missing_live_cmdline_failclosed_preserved(self):
        (self.proc/"123/cmdline").write_bytes(b"")
        with self.assertRaises(ValueError):self.capture()
        self.assertEqual(self.saved[-1][0]["raw_bytes"],0) # Raw persisted before rejection.
        (self.proc/"123/cmdline").unlink()
        with self.assertRaises(FileNotFoundError):self.capture()
    def test12_actual_read_permission_failure_propagates(self):
        class DeniedProc:
            def __truediv__(self,value):return self
            def read_text(self):raise PermissionError("actual software permission refusal")
        with patch.dict(self.h.process_identity.__globals__,{"Path":lambda p:DeniedProc()}):
            with self.assertRaises(PermissionError):self.capture()
        self.assertEqual(self.saved,[])
    def test13_oversize_live_cmdline_saved_then_refused(self):
        (self.proc/"123/cmdline").write_bytes(b"w"*P.LIMIT+b"\0")
        with self.assertRaises(ValueError):self.capture()
        self.assertEqual(self.saved[-1][0]["raw_bytes"],P.LIMIT+1)
    def test14_original_primitive_foreign_source_refused(self):
        self.h.__file__=str(HERE/"process_cmdline.py")
        with self.assertRaises(ValueError):self.capture()
        self.assertEqual(self.saved,[])
    def test15_actual_Control_observe_and_whole_call_same_raw_consumer(self):
        tree=ast.parse((HERE/"MAIN_HOST.py").read_text())
        ctl=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=="Control")
        observe=next(n for n in ctl.body if isinstance(n,ast.FunctionDef)and n.name=="observe")
        ns=dict(C=C,require=C.require,SMI="/usr/local/sbin/npu-smi",
            R=types.SimpleNamespace(helper=lambda:types.SimpleNamespace(frozen=lambda:self.h)),
            actual_hbm=lambda raw,n:dict(physical=n,used_mib=100),os=__import__("os"))
        exec(compile(ast.Module(body=[observe],type_ignores=[]),"actual-original-Control.observe","exec"),ns)
        c=types.SimpleNamespace(call=lambda *a:(dict(stdout="software source-qualified snapshot"),self.source),
            protected=[],owned=[dict(cid="a"*64,phase="tp4-capture")],current=dict(cid="a"*64,phase="tp4-capture"),
            save=self.writer,observations=[])
        self.h.protected=lambda raw:[]
        self.h.legacy=lambda:types.SimpleNamespace(process_rows=lambda raw:[(4,0,123)])
        self.h.idle_one=lambda raw,n:None
        with patch.object(C,"source",return_value=self.source),patch.object(C,"protected_module",return_value=types.SimpleNamespace(protected_boundary=lambda *a:{})),patch.object(P,"GATE_REF",self.gate_ref),patch.object(P,"Path",lambda p:self.proc if str(p)=="/proc"else Path(p)):
            ns["closure"]=lambda:self.source
            ns["observe"](c,active=True)
        observation=self.saved[-1][0];proof=observation["proofs"][0]
        self.consume(json.loads(Path(proof["actual_cmdline_raw_ref"]["path"]).read_bytes()),proof)
        consume_tree=ast.parse((HERE/"consume_host.py").read_text())
        calls=[ast.unparse(n)for n in ast.walk(consume_tree)if isinstance(n,ast.Call)]
        expected=ast.dump(ast.parse("PC.consume(read(p['actual_cmdline_raw_ref']), p, source)").body[0].value)
        self.assertIn(expected,[ast.dump(n)for n in ast.walk(consume_tree)if isinstance(n,ast.Call)])
        self.assertNotIn("actual original proc NUL argv digest",(HERE/"consume_host.py").read_text())
    def test16_qualified_primitive_source_compile_and_all_adjacent_identity_readers(self):
        _,raw=actual_file(P.GATE_REF,"full_matrix_host.py");compile(raw,"actual-frozen-host","exec")
        for name in("n1_check.py","tp_provider_current.py"):
            tree=ast.parse((HERE/name).read_text())
            self.assertTrue(any(isinstance(n,ast.Call)and ast.unparse(n.func)=="hashlib.sha256"for n in ast.walk(tree)))
        for p in HERE.glob("*.py"):compile(p.read_bytes(),str(p),"exec")
def main(argv=None):
    global REVIEW
    ap=argparse.ArgumentParser();ap.add_argument("--review-root",type=Path);a=ap.parse_args(argv);REVIEW=a.review_root
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ExactProc))
    return 0 if result.wasSuccessful()else 1
if __name__=="__main__":sys.exit(main())
