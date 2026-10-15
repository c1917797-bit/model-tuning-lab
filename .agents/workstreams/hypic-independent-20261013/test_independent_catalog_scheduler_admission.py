import json,tempfile,types,unittest
from pathlib import Path
from independent_catalog_scheduler_admission import RetainedMaterialIndex,CatalogWorkerMaterialReader,CatalogPICAdmissionCallback,make_scheduler_callback
def pub(rank=0,key="key",generation=1,pool="linear",layer="linear0",digest="d"):
 return {"event":"compact_public_state_published" if pool=="linear" else "compact_public_kv_published","manifest_sha256":"m","rank":rank,"pid":100+rank,"key":key,"pool":pool,"generation":generation,"layer":layer,"tokens_sha256":digest}
class Tests(unittest.TestCase):
 def test_catalog_factory_and_legacy_route(self):
  from independent_pic_scheduler_admission import PICAdmissionCallback
  with tempfile.TemporaryDirectory() as t:
   c=make_scheduler_callback({"public_segments":[list(range(128))]},t,"m",emit=lambda e:None,request_limit=1024)
   self.assertIsInstance(c,CatalogPICAdmissionCallback);self.assertEqual(c.limit,1024)
   legacy=make_scheduler_callback({"public_tokens":list(range(128))},t,"m",emit=lambda e:None)
   self.assertIsInstance(legacy,PICAdmissionCallback)
   with self.assertRaises(ValueError):make_scheduler_callback({"public_segments":[list(range(128))],"public_tokens":[1]},t,"m",emit=lambda e:None)
 def test_strict_bounds_and_publication_identity(self):
  with self.assertRaises(ValueError):RetainedMaterialIndex("m",max_active=True)
  x=RetainedMaterialIndex("m")
  with self.assertRaises(ValueError):x.accept(dict(pub(),tokens_sha256=None))
 def test_complete_fourrank_and_eviction(self):
  x=RetainedMaterialIndex("m")
  for rank in range(4):
   for pool,count in [("linear",48),("kv",16)]:
    for i in range(count):x.accept(pub(rank,pool+str(i),pool=pool,layer=pool+str(i)))
  self.assertTrue(x.ready("d"));e=pub(0,"linear0");x.accept(dict(e,event="compact_public_material_evicted"));self.assertFalse(x.ready("d"));x.accept(dict(e,generation=2));self.assertTrue(x.ready("d"))
 def test_long_valid_history_is_bounded_state_not_total_history(self):
  x=RetainedMaterialIndex("m")
  for i in range(2500):
   e=pub(i%4,generation=i+1);x.accept(e);x.accept(dict(e,event="compact_public_material_evicted"))
  self.assertFalse(x.ready("d"));self.assertEqual(len(x.alive),0);self.assertEqual(len(x.latest),4)
 def test_stale_eviction_generation_and_worker_fail(self):
  x=RetainedMaterialIndex("m");e=pub();x.accept(e)
  for bad in [dict(e,event="compact_public_material_evicted",generation=2),dict(e,event="compact_public_material_evicted",pid=999),dict(e,manifest_sha256="other")]:
   with self.assertRaises(ValueError):x.accept(bad)
  x.accept(dict(e,event="compact_public_material_evicted"))
  with self.assertRaises(ValueError):x.accept(e)
 def test_active_and_key_ceiling(self):
  x=RetainedMaterialIndex("m",max_active=1,max_keys=1);e=pub();x.accept(e)
  with self.assertRaises(ValueError):x.accept(pub(key="other"))
  x.accept(dict(e,event="compact_public_material_evicted"))
  with self.assertRaises(ValueError):x.accept(pub(key="other"))
 def test_reader_partial_line_then_truncation(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/"compact-worker-100.jsonl";p.write_text(json.dumps(pub()));r=CatalogWorkerMaterialReader(t,"m")
   self.assertFalse(r.ready(1,"d"));self.assertEqual(len(r.index.alive),0)
   with p.open("a") as f:f.write("\n")
   self.assertFalse(r.ready(2,"d"));self.assertEqual(len(r.index.alive),1)
   p.write_text("")
   with self.assertRaises(ValueError):r.ready(3,"d")
 def callback(self,ready=True,limit=1024):
  segments=[tuple(range(128)),tuple(range(128,256))];seen=[];emitted=[]
  class R:
   def ready(self,step,digest):seen.append(digest);return ready
  c=CatalogPICAdmissionCallback(segments,R(),emit=emitted.append,max_requests=limit)
  scheduler=types.SimpleNamespace(current_step=1,use_eagle=False,connector=None,need_mamba_block_aligned_split=False,cache_config=types.SimpleNamespace(block_size=1))
  return c,scheduler,segments,seen,emitted
 def test_full381_and_distinct_catalog_identity(self):
  c,s,segments,seen,emitted=self.callback()
  for i in range(381):
   r=types.SimpleNamespace(request_id=str(i),prompt_token_ids=[999]+list(segments[i%2])+[1000],has_encoder_inputs=False)
   self.assertEqual(c(s,r,0,10),1)
  self.assertEqual(len(c.cache),381);self.assertEqual(len(set(seen)),2);self.assertEqual(len(emitted),381)
 def test_no_ready_falls_back_native_without_fake_cap(self):
  c,s,segments,seen,emitted=self.callback(ready=False);r=types.SimpleNamespace(request_id="r",prompt_token_ids=[999]+list(segments[0])+[1000])
  self.assertEqual(c(s,r,0,10),10);self.assertEqual(emitted,[])
 def test_prompt_drift_and_request_ceiling(self):
  c,s,segments,seen,emitted=self.callback(limit=1);r=types.SimpleNamespace(request_id="r",prompt_token_ids=[999]+list(segments[0])+[1000]);c(s,r,0,10)
  r.prompt_token_ids[-1]=1001
  with self.assertRaises(ValueError):c(s,r,0,10)
  r.request_id="r2"
  with self.assertRaises(ValueError):c(s,r,0,10)
 def test_public_producer_not_counted_as_private(self):
  c,s,segments,seen,emitted=self.callback();r=types.SimpleNamespace(request_id="public",prompt_token_ids=list(segments[0]))
  self.assertEqual(c(s,r,0,10),10);self.assertEqual(c.cache,{})
if __name__=="__main__":unittest.main()
