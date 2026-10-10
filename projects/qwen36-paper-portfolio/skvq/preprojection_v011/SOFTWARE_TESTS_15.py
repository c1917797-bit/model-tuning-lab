"""UNEXECUTED preparation tests. MAIN may run stdlib only; fixtures never native/model PASS."""
import importlib,os,subprocess,sys,tempfile,types,unittest
from pathlib import Path
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
sys.path.insert(0,str(Path(__file__).resolve().parent))
import current_contract as C
C.configure(os.environ["SKVQ_CURRENT_MANIFEST_SHA256"])
sys.path.insert(0,str(BASE))
from io_contract import publish_json,publish_bytes,safe_root,require,pack_ids
from build_inputs import select_windows,PLAN
from runtime_capture import Session
HERE=BASE # original default-OFF CLI remains source-qualified donor, not relocated copy
class AtomicTests(unittest.TestCase):
    def test_atomic_exclusive_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"done.json";publish_json(p,{"whole":[0]*1000})
            import json
            self.assertEqual(len(json.loads(p.read_text())["whole"]),1000)
            old=p.read_bytes()
            with self.assertRaises(FileExistsError):publish_json(p,{"wrong":True})
            self.assertEqual(p.read_bytes(),old)
            self.assertEqual(len(list(p.parent.glob(".*.pending"))),1) # failed owned temp retained
    def test_destination_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"raw";p.symlink_to(Path(d)/"other")
            with self.assertRaises(ValueError):publish_bytes(p,b"bad")
    def test_new_output_predicate(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"run-skvq-train-inputs-001-main-20261008-01"
            self.assertEqual(safe_root(p,"run-skvq-train-inputs-001-"),p)
            with self.assertRaises(ValueError):safe_root(p,"run-skvq-train-inputs-001-")
    def test_wrong_output_old_protocol(self):
        with tempfile.TemporaryDirectory() as d:
            for n in ("run-damp-full-36-1024","run-kivi-cpu-host-004-x","run-skvq-train-inputs-002-x"):
                with self.assertRaises(ValueError):safe_root(Path(d)/n,"run-skvq-train-inputs-001-")
    def test_dotdot_output(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):safe_root(Path(d)/"x"/".."/"run-skvq-train-inputs-001-x","run-skvq-train-inputs-001-")
    def test_parent_symlink_output(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"actual";a.mkdir();b=Path(d)/"link";b.symlink_to(a,target_is_directory=True)
            with self.assertRaises(ValueError):safe_root(b/"run-skvq-train-inputs-001-x","run-skvq-train-inputs-001-")
class InputTests(unittest.TestCase):
    def test_exact_nine_train_pins(self):
        self.assertEqual(len(PLAN["artifacts"]),9)
        self.assertTrue(all(a["split"]=="train" and len(a["sha256"])==64 for a in PLAN["artifacts"]))
        self.assertEqual({a["dataset"] for a in PLAN["artifacts"]},{"MATH","APPS","ARC-Challenge"})
        self.assertFalse(any("wikitext" in a["repository"].lower() for a in PLAN["artifacts"]))
    def test_full256_window_scheduler_fixture(self):
        pool=list(range(131072));records=[{"pool_start":0,"pool_stop":len(pool)}]
        raw,samples=select_windows(pool,records)
        self.assertEqual(len(raw),256*4096*4)
        self.assertEqual([s["sample_id"] for s in samples],list(range(256)))
        for i,s in enumerate(samples):
            self.assertEqual(raw[i*4096*4:(i+1)*4096*4],pack_ids(pool[s["pool_start"]:s["pool_start"]+4096]))
            self.assertEqual(s["source_records"],[0])
    def test_no_padding_small_pool(self):
        with self.assertRaises(ValueError):select_windows(list(range(4096)),[{"pool_start":0,"pool_stop":4096}])
    def test_vocab_negative(self):
        for ids in ([248320],[-1],[True]):
            with self.assertRaises(ValueError):pack_ids(ids)
class OwnedRestoreTests(unittest.TestCase):
    class Obj:
        def forward(self,x):return x+1
    def make(self):
        s=Session.__new__(Session);s.patches=[];s.linear=[];s.closed=False;s.secondary=[]
        return s
    def test_restore_exact_owned_no_global_patch(self):
        s=self.make();o=self.Obj();cls=type(o).forward
        def owned(this,x):return x+2
        s.bind(o,"forward",owned)
        self.assertEqual(o.forward(1),3);self.assertIs(type(o).forward,cls)
        self.assertEqual(s.restore(),[]);self.assertEqual(o.forward(1),2)
        self.assertNotIn("forward",o.__dict__)
    def test_foreign_mutation_not_overwritten(self):
        s=self.make();o=self.Obj()
        s.bind(o,"forward",lambda this,x:x)
        foreign=types.MethodType(lambda this,x:x+10,o);o.forward=foreign
        errors=s.restore()
        self.assertEqual(len(errors),1);self.assertIs(o.forward,foreign)
        self.assertEqual(s.secondary,errors)
    def test_overlapping_instance_patch_rejected(self):
        s=self.make();o=self.Obj()
        s.bind(o,"forward",lambda this,x:x)
        with self.assertRaises(ValueError):s.bind(o,"forward",lambda this,x:x)
        s.restore()
class DefaultOffTests(unittest.TestCase):
    def test_actual_default_off_cli_subprocess_no_torch(self):
        for name in ("build_inputs.py","capture_cli.py"):
            r=subprocess.run([sys.executable,"-B",str(HERE/name)],capture_output=True,text=True,timeout=5)
            self.assertEqual(r.returncode,0,r.stderr)
            import json
            v=json.loads(r.stdout);self.assertFalse(v["default_enabled"]);self.assertFalse(v["model_launched"])
    def test_import_no_torch(self):
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
if __name__=="__main__":unittest.main()
