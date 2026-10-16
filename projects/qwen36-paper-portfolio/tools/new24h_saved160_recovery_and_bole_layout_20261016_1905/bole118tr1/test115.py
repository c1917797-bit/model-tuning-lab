import ast,hashlib,json,subprocess,sys,tempfile,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import tree_fa115 as F,probe115 as G,consume115 as C


class Tests(unittest.TestCase):
    def test_mask_paths_padding_and_siblings(self):
        import torch as t
        mask=F.forbid_mask(t,[0,3],F.PARENTS,10)
        self.assertEqual(mask.shape,(2,1,7,10));self.assertTrue(mask.dtype==t.bool)
        self.assertFalse(mask[0,0,3,1]);self.assertTrue(mask[0,0,3,2]);self.assertTrue(mask[0,0,3,7])
        self.assertFalse(mask[1,0,3,0]);self.assertFalse(mask[1,0,3,6]);self.assertTrue(mask[1,0,3,5])

    def test_dense_attention_vs_independent_path(self):
        import torch as t
        t.set_num_threads(1)
        raw=F.recipe(t,16,[i%9 for i in range(16)])
        q,k,v=(raw[n].double()for n in('query','key','value'));k=k.repeat_interleave(6,1);v=v.repeat_interleave(6,1)
        scores=t.matmul(q,k.transpose(-1,-2))*raw['scale'];scores=scores.masked_fill(raw['mask'],-float('inf'))
        out=t.matmul(scores.softmax(-1),v)
        self.assertLess(float((out-F.path_reference(t,raw)).abs().max()),1e-12)

    def test_real_FIA_call_argument_contract(self):
        import torch as t
        raw=F.recipe(t,1,[7]);calls=[]
        op=types.SimpleNamespace(npu_fused_infer_attention_score=lambda **kw:calls.append(kw))
        F.call_fia(op,raw,sparse_mode=1);v=calls[0]
        self.assertIs(v['atten_mask'],raw['mask']);self.assertEqual(v['sparse_mode'],1);self.assertEqual(v['input_layout'],'BNSD');self.assertEqual((v['num_heads'],v['num_key_value_heads']),(6,1))
        self.assertEqual(set(v),set(G.REQUIRED))
        with self.assertRaises(ValueError):F.call_fia(op,raw,sparse_mode=3)

    def test_missing_actualABI_and_cold_OFF(self):
        with self.assertRaises(ValueError):G.require_abi(None)
        r=subprocess.run([sys.executable,'-I','-B',str(P/'probe115.py')],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertFalse(json.loads(r.stdout)['NPU'])

    def test_consumer_all_calls_and_wrong_mask(self):
        import torch as t
        t.set_num_threads(1)
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);sr={'software_only':True};rows=[]
            for case,(batch,prefixes,witness)in enumerate(((1,[0],True),(1,[7],False),(16,[i%9 for i in range(16)],False))):
                raw=F.recipe(t,batch,prefixes,witness)
                output=F.path_reference(t,raw).bfloat16()
                for mode in(1,0):
                    p=root/('case%dmode%d.pt'%(case,mode));t.save(dict(source=sr,case=case,mode=mode,inputs=raw,output=output,primary=None),p);rows.append(dict(raw=G.ref(p)))
            stage=dict(schema='bole.FIA-stage/v115',source=sr,rows=rows)
            result=C.consume(t,sr,stage);self.assertEqual(result['observed_mask_modes_supported_on_exact_test_matrix'],[0,1])
            p=Path(rows[0]['raw']['path']);raw=t.load(p,weights_only=True);raw['inputs']['mask'].zero_();t.save(raw,p);rows[0]['raw']=G.ref(p)
            with self.assertRaises(ValueError):C.consume(t,sr,stage)

    def test_sibling_leak_witness_rejects_no_mask(self):
        import torch as t
        raw=F.recipe(t,1,[0],True);truth=F.path_reference(t,raw)
        bad=raw['value'].repeat_interleave(6,1).mean(2,keepdim=True).expand_as(raw['query']).contiguous()
        self.assertFalse(F.score(t,bad,truth)['preregistered_allclose'])

if __name__=='__main__':unittest.main()
