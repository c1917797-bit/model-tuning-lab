import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from independent_pic_scheduler_admission import WorkerMaterialReader,PICAdmissionCallback
from independent_segment_selection import token_digest

class Admission(unittest.TestCase):
    def test_callback_cold_hot_decode_and_drift(self):
        reader=NS(ready=lambda step,digest:False);events=[]
        cap=PICAdmissionCallback([9,8,7,6],reader,emit=events.append)
        scheduler=NS(current_step=1,need_mamba_block_aligned_split=False,connector=None,use_eagle=False)
        req=NS(request_id="x",prompt_token_ids=[1]*10+[9,8,7,6]+[2]*6,has_encoder_inputs=False)
        self.assertEqual(cap(scheduler,req,0,12),12)
        reader.ready=lambda step,digest:True
        self.assertEqual(cap(scheduler,req,0,12),10)
        self.assertEqual(cap(scheduler,req,10,4),0)
        self.assertEqual(cap(scheduler,req,10,5),5)
        self.assertEqual(cap(scheduler,req,20,1),1)
        req.prompt_token_ids[0]=3
        with self.assertRaises(ValueError):cap(scheduler,req,0,12)
    def publication(self,rank,pool,i):
        return {"event":"compact_public_state_published" if pool=="linear" else "compact_public_kv_published",
            "rank":rank,"pid":100+rank,"pool":pool,"key":pool+str(i),"generation":1,
            "layer":pool+str(i),"tokens_sha256":"d","manifest_sha256":"m"}
    def test_current_fourrank_incremental_eviction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);reader=WorkerMaterialReader(root,"m")
            for rank in range(3):
                rows=[self.publication(rank,pool,i) for pool,n in [("linear",48),("kv",16)] for i in range(n)]
                (root/("compact-worker-"+str(100+rank)+".jsonl")).write_text("".join(json.dumps(x)+"\n" for x in rows))
            self.assertFalse(reader.ready(1,"d"))
            rows=[self.publication(3,pool,i) for pool,n in [("linear",48),("kv",16)] for i in range(n)]
            path=root/"compact-worker-103.jsonl";path.write_text("".join(json.dumps(x)+"\n" for x in rows))
            self.assertTrue(reader.ready(2,"d"))
            ev=dict(rows[0],event="compact_public_material_evicted")
            with path.open("a") as stream:stream.write(json.dumps(ev)+"\n")
            self.assertFalse(reader.ready(3,"d"))
    def test_partial_record_not_certified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/"compact-worker-100.jsonl"
            path.write_bytes(b'{"event":"compact_public_state_published"')
            reader=WorkerMaterialReader(root,"m")
            self.assertFalse(reader.ready(1,"d"));self.assertEqual(reader.cursors[str(path)][0],0)
    def test_unsafe_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/"compact-worker-1.jsonl").symlink_to("/etc/passwd")
            with self.assertRaises(ValueError):WorkerMaterialReader(root,"m").ready(1,"d")
if __name__=="__main__":unittest.main()
