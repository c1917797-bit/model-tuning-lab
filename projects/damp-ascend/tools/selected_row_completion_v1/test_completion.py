"""SYNTHETIC stdlib behavior only; never NPU/component PASS."""
import copy,hashlib,json,unittest
import validator as v
def meta(t,s):return [("bad",[0],[0])]
def good(t=1,k="adjacent",sr=v.VARS[0]):
    guards={"g":True}
    metric={"finite":True,"max_head_relative_l2":0.0}
    path={"passed":True,"guards":guards,"metrics":{x:metric.copy() for x in
        ("selected_state","complete_state","output")}}
    return {"batch":t,"shared_arena_layout":k,"variant":sr,"stage":"graph_restricted",
        "status":"passed","graph_numerical_status":"passed","warmups":3,"identical_repeats":8,
        "changed_replays":160,"steps":[{"step":i+1,"passed":True,"indices":list(range(t)),
            "guards":guards,"paths":[copy.deepcopy(path) for _ in range(3)]} for i in range(160)],
        "invalid_dynamic_cases":[{"name":"bad","passed":True,"paths":[{"passed":True,"guards":guards}
            for _ in range(3)]}],"actual_overlap_rejections":[{"label":str(i),"guards":guards,
            "rejection":"DATA byte intervals overlap"} for i in range(15)],
        "shared_arena_audit":{"layout":k,"arenas":[{}]*4,"guarded_observations":481},
        "shared_arena_audit_after_negatives":{"layout":k,"arenas":[{}]*5,"guarded_observations":496},
        "actual_token_metadata":{"tokens":t}}
class Tests(unittest.TestCase):
    def test_full_matrix(self):self.assertEqual(len(v.expected()),64)
    def test_whole_case(self):self.assertEqual(v.valid_case(good(),meta),(1,"adjacent",v.VARS[0]))
    def test_no_partial_159(self):
        c=good();c["steps"].pop()
        with self.assertRaises(ValueError):v.valid_case(c,meta)
    def test_graph160_not_overlap_complete(self):
        c=good();c["actual_overlap_rejections"]=[]
        with self.assertRaises(ValueError):v.valid_case(c,meta)
    def test_no_threshold_relax(self):
        for n,z in (("selected_state",1.00001e-5),("complete_state",1.00001e-5),("output",.00303001)):
            c=good();c["steps"][0]["paths"][0]["metrics"][n]["max_head_relative_l2"]=z
            with self.assertRaises(ValueError):v.valid_case(c,meta)
    def test_no_nonfinite_wrapper(self):
        c=good();c["steps"][0]["paths"][0]["metrics"]["output"]["max_head_relative_l2"]={"nonfinite":"nan"}
        with self.assertRaises(ValueError):v.valid_case(c,meta)
    def test_true_t_not_fake_pad(self):
        c=good(2);c["steps"][0]["indices"]=[0]
        with self.assertRaises(ValueError):v.valid_case(c,meta)
    def test_no_completed_retry(self):
        k=(1,"adjacent",v.VARS[0])
        with self.assertRaises(ValueError):v.selected_keys([list(k)],{"missing":[]},4)
    def test_no_duplicate_selector(self):
        k=(1,"adjacent",v.VARS[0])
        with self.assertRaises(ValueError):v.selected_keys([list(k),list(k)],{"missing":[k]},4)
    def test_checkpoint_original_failed_not_relabelled(self):
        event={"schema":"damp-selected-row-journal/v1","seq":0,"header_set":{"status":"running"},
            "header_remove":[],"checks_start":0,"checks_append":[],"cases":[]}
        raw=(json.dumps(event)+"\n").encode();path="/original/evidence.jsonl"
        report={"status":"running","checks":[],"cases":[],"evidence_journal":{
            "path":path,"sha256":v.digest(raw),"events":1,"schema":"damp-selected-row-journal/v1"}}
        extra=b'{"seq":1' # Killed incomplete tail remains raw, never repair it.
        result=v.checkpoint(report,raw+extra,path)
        self.assertEqual(report["status"],"running");self.assertEqual(result["extra_original_tail_bytes"],len(extra))
        altered=copy.deepcopy(report);altered["status"]="passed"
        with self.assertRaises(ValueError):v.checkpoint(altered,raw+extra,path)
    def test_checkpoint_drop_old_steps_reject(self):
        event={"schema":"damp-selected-row-journal/v1","seq":0,"header_set":{"status":"running"},
            "header_remove":[],"checks_start":0,"checks_append":[],"cases":[{"index":0,"meta":{"status":"passed"},
                "steps_start":1,"steps_append":[]}]}
        raw=(json.dumps(event)+"\n").encode();p="/original/evidence.jsonl"
        r={"status":"running","checks":[],"cases":[],"evidence_journal":{"path":p,"sha256":v.digest(raw),
            "events":1,"schema":"damp-selected-row-journal/v1"}}
        with self.assertRaises(ValueError):v.checkpoint(r,raw,p)
    def test_duplicate_json_reject(self):
        with self.assertRaises(ValueError):v.decode('{"a":1,"a":2}')
    def test_actual_outer_shape_synthetic(self):
        args=["-B","/synthetic/controller.py"]
        raw={"schema":"agentweb.operation/v1","kind":"exec","operationId":"new-op",
            "terminal":True,"status":"completed","error":None,"succeeded":True,
            "operation":{"routeDecision":"peer_direct","targetPeerId":v.PEER,"result":{
                "found":True,"ok":True,"state":"completed","lane":"job","record":{
                    "id":"new-op","state":"completed","lane":"job","cancelled":False,"timedOut":False,
                    "command":"/usr/bin/python3","cwd":str(v.REPO),"args":args,"exitCode":0,
                    "error":None,"stdout":"","stderr":""}}}}
        original=v.json_ref
        try:
            v.json_ref=lambda _:raw
            self.assertEqual(v.terminal({}, "new-op",args,success=True)["exitCode"],0)
            for field,value in (("timedOut",True),("cancelled",True),("exitCode",1)):
                bad=copy.deepcopy(raw);bad["operation"]["result"]["record"][field]=value
                v.json_ref=lambda _,bad=bad:bad
                with self.assertRaises(ValueError):v.terminal({}, "new-op",args,success=True)
            bad=copy.deepcopy(raw);bad["terminal"]=False;v.json_ref=lambda _:bad
            with self.assertRaises(ValueError):v.terminal({}, "new-op",args,success=True)
        finally:v.json_ref=original
if __name__=="__main__":unittest.main()
