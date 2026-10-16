import hashlib,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import independent_quality_compact_loader as target
class QualityLoaderTests(unittest.TestCase):
    def fixture(self,root,profile="quality-hot"):
        c={"public_segments":[list(range(128))],"scheduler_admission_enabled":True,"evidence_profile":profile,"evidence_limits":{"max_requests":1024}}
        p=root/"config.json";p.write_text(json.dumps(c))
        m=root/"manifest.json";m.write_text(json.dumps({"config":"config.json","source_sha256":{"config.json":hashlib.sha256(p.read_bytes()).hexdigest()}}))
        return {"INDEPENDENT_COMPACT_HYPIC":"1","INDEPENDENT_COMPACT_MANIFEST":str(m),"INDEPENDENT_COMPACT_RAW":str(root)}
    def load(self):
        class Original:
            def exec_module(self,module):module.loaded=True
        spec=types.SimpleNamespace(loader=Original())
        with patch.object(target.importlib.machinery.PathFinder,"find_spec",return_value=spec):
            spec=target._finder.find_spec("vllm_ascend.worker.model_runner_v1")
        spec.loader.exec_module(types.SimpleNamespace())
    def test_disabled(self):
        before=list(sys.meta_path)
        with patch.dict(os.environ,{},clear=True):target.enable();target.disable()
        self.assertEqual(sys.meta_path,before)
    def test_late_worker_import_rejected(self):
        with patch.dict(os.environ,{"INDEPENDENT_COMPACT_HYPIC":"1"}),patch.dict(sys.modules,{"vllm_ascend.worker.model_runner_v1":object()}):
            with self.assertRaises(RuntimeError):target.enable()
    def test_forward_profile_limit_and_owned_uninstall(self):
        before=list(sys.meta_path);capture={};stops=[]
        def scheduler(*args,**kw):capture["scheduler"]=kw;return lambda:stops.append("scheduler")
        def activate(config,**kw):
            capture["config"]=config;capture["worker"]=kw
            kw["emit"]({"event":"mixed_native_gdn_completed","rank":0,"step":1,"layer":"l","request_id":"n","slot":0})
            kw["emit"]({"event":"compact_gdn_body_composed","rank":0,"step":1,"layer":"l","request_id":"h"})
            return lambda:stops.append("worker")
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fake=types.SimpleNamespace(activate_compact_hypic=activate)
            with patch.dict(os.environ,self.fixture(root)),patch("independent_catalog_scheduler_loader.enable_scheduler",scheduler),patch.dict(sys.modules,{"independent_compact_activation":fake}):
                target.enable();self.load()
                records=[json.loads(x) for x in next(root.glob("compact-worker-*.jsonl")).read_text().splitlines()]
                self.assertEqual(records[0]["event"],"quality_evidence_policy_selected")
                self.assertEqual(records[-1]["omitted_nonhot_counts"],{"mixed_native_gdn_completed":1})
                self.assertNotIn("evidence_profile",capture["config"]);self.assertNotIn("evidence_limits",capture["config"])
                self.assertEqual(capture["worker"]["request_progress_limit"],1024)
                self.assertEqual(capture["scheduler"]["request_limit"],1024)
                target.disable();target.disable()
                with self.assertRaises(OSError):capture["worker"]["emit"]({"event":"compact_gdn_body_composed"})
        self.assertEqual(stops,["worker","scheduler"]);self.assertEqual(sys.meta_path,before)
    def test_failed_worker_rolls_back_pending_scheduler(self):
        before=list(sys.meta_path);stops=[]
        def scheduler(*args,**kw):return lambda:stops.append("scheduler")
        def activate(*args,**kw):raise RuntimeError("activation failed")
        with tempfile.TemporaryDirectory() as tmp:
            fake=types.SimpleNamespace(activate_compact_hypic=activate)
            with patch.dict(os.environ,self.fixture(Path(tmp))),patch("independent_catalog_scheduler_loader.enable_scheduler",scheduler),patch.dict(sys.modules,{"independent_compact_activation":fake}):
                target.enable()
                with self.assertRaises(RuntimeError):self.load()
        self.assertEqual(stops,["scheduler"]);self.assertEqual(sys.meta_path,before)
    def test_eligible_stage_probe_receives_bound_sink(self):
        import independent_c1_stage_probe as probe
        captured={};sentinel=object()
        def activate(config,**kw):
            emit=kw["emit"]
            layer=types.SimpleNamespace(prefix=probe.LAYER)
            layout=types.SimpleNamespace(rank=0,step=12,request_ids=("a","b"),
                chains=((("live",0),("live",1)),(("live",2),("live",3))),
                packed_tokens=100,windows=(None,)*4)
            plans=[types.SimpleNamespace(request_id=rid,scheduled_tokens=50,skipped_tokens=0)for rid in ("a","b")]
            with patch.object(probe,"C1StageProbe",return_value=sentinel)as ctor:
                self.assertIs(probe.make_probe(layer,layout,plans,{"a":object(),"b":object()},emit,head_policy="head0"),sentinel)
                captured.update(ctor.call_args.kwargs)
            return lambda:None
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);env=self.fixture(root)
            expected=hashlib.sha256((root/"manifest.json").read_bytes()).hexdigest()
            with patch.dict(os.environ,env),patch("independent_catalog_scheduler_loader.enable_scheduler",return_value=lambda:None),patch.dict(sys.modules,{"independent_compact_activation":types.SimpleNamespace(activate_compact_hypic=activate)}):
                try:target.enable();self.load()
                finally:target.disable()
            self.assertEqual(captured["manifest_sha256"],expected)
            self.assertEqual(captured["root"],root/"c1-stage-rank0-step12")
    def test_bad_profile_fails_before_hooks(self):
        before=list(sys.meta_path)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ,self.fixture(Path(tmp),profile="silent")):
                with self.assertRaises(ValueError):target.enable()
        self.assertEqual(sys.meta_path,before)
if __name__=="__main__":unittest.main()
