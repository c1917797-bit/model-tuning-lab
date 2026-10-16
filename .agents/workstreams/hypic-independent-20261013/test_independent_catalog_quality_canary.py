import copy,itertools,unittest
from unittest.mock import patch
from independent_catalog_quality_canary import catalog_canary_plan,run_catalog_canary
from independent_segment_selection import token_digest
class Tests(unittest.TestCase):
    def fixture(self):
        public=[[100+i]*16 for i in range(127)]
        rows=[dict(index=i,sample_id="s"+str(i),token_ids=[1]*8+t+[2]*8,reference="A",
                   segment=dict(start=8,end=24,tokens_sha256=token_digest(t))) for i,t in enumerate(public)]
        rows[-1]["token_ids"]+=[3]*8
        inputs=dict(schema="hypic-quality-inputs/v1",requests=rows,repetitions=3,
                    generation=dict(max_tokens=1024,temperature=0,seed=0,ignore_eos=False,enable_thinking=False))
        catalog=dict(schema="hypic-public-catalog/v1",public_segments=public)
        plan=catalog_canary_plan(rows)
        spec=dict(inputs={"path":"i","sha256":"i"},catalog={"path":"c","sha256":"c"},
                  ruler_path="frozen",batch_samples=8,canary_indexes=list(plan["initial_indexes"]))
        return inputs,catalog,plan,spec
    def execute(self,*,change_spec=None,send_override=None,choose=None):
        inputs,catalog,plan,spec=self.fixture();events=[];sent=[];ready=[];ids=itertools.count()
        if change_spec:change_spec(spec)
        def send(p):
            sent.append(p)
            if send_override:return send_override(p)
            return dict(id="api"+str(next(ids)),choices=[dict(text="A",finish_reason="stop")],
                        usage=dict(prompt_tokens=len(p["prompt"]),completion_tokens=1 if p["max_tokens"]==1 else 2))
        with patch("independent_catalog_quality_canary.read_bound",side_effect=lambda s:inputs if s["path"]=="i" else catalog),patch("independent_catalog_quality_canary.load_ruler",return_value={"score_case":lambda b,t,r:(t,t==r)}):
            out=run_catalog_canary(spec,send=send,guard=lambda:None,record=events.append,
                require_material_ready=ready.append,choose_rebuild=choose or (lambda xs:xs[0]["index"]))
        return out,events,sent,ready
    def test_deterministic_longest_and_distinct(self):
        i,c,p,s=self.fixture()
        self.assertEqual(p["initial_indexes"][0],126)
        self.assertEqual(len(p["initial_indexes"]),16)
        self.assertEqual(len(set(i["requests"][x]["segment"]["tokens_sha256"] for x in p["initial_indexes"])),16)
    def test_complete8_8_1_not_fullquality(self):
        out,events,sent,ready=self.execute()
        self.assertEqual(out["requests"],17);self.assertFalse(out["full_quality"])
        self.assertEqual(len(out["results"]),17);self.assertEqual(len(sent),34)
        self.assertEqual(len(ready),34)
        self.assertEqual([len(e["indexes"]) for e in events if e["event"]=="catalog-canary-phase-start"],[8,8,1])
        self.assertTrue(all(e.get("scored")is False for e in events))
    def test_natural_eos_same_ruler(self):
        o,e,s,r=self.execute()
        self.assertTrue(all(x["ignore_eos"]is False for x in s))
        self.assertEqual(sum(x["max_tokens"]==1024 for x in s),17)
    def test_wrong_selection_rejected(self):
        with self.assertRaises(ValueError):self.execute(change_spec=lambda s:s.update(canary_indexes=[0]*16))
    def test_bad_rebuild_index(self):
        with self.assertRaises(ValueError):self.execute(choose=lambda xs:True)
    def test_wrong_batch_bound(self):
        with self.assertRaises(ValueError):self.execute(change_spec=lambda s:s.update(batch_samples=10))
    def test_producer_failure_stops(self):
        with self.assertRaises(ValueError):self.execute(send_override=lambda p:dict(id="x",usage=dict(prompt_tokens=0)))
    def test_private_failure_stops(self):
        def send(p):
            if p["max_tokens"]==1024:raise RuntimeError("retained failure")
            return dict(id="public",usage=dict(prompt_tokens=len(p["prompt"])))
        with self.assertRaises(ValueError):self.execute(send_override=send)
    def test_full_inventory_required(self):
        i,c,p,s=self.fixture()
        with self.assertRaises(ValueError):catalog_canary_plan(i["requests"][:-1])
    def test_distinct_segments_required(self):
        i,c,p,s=self.fixture()
        for r in i["requests"]:r["segment"]["tokens_sha256"]="same"
        with self.assertRaises(ValueError):catalog_canary_plan(i["requests"])
if __name__=="__main__":unittest.main()
