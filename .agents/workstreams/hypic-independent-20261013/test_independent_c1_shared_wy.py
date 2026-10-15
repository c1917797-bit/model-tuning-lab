import unittest
from types import SimpleNamespace
from collections import Counter
import torch
from independent_c1_shared_wy import prepare_shared_wy

class SharedWYTests(unittest.TestCase):
    def test_shared_once_and_three_passes(self):
        calls=Counter();seen=[]
        def record(name,result):
            def f(*args,**kwargs):
                calls[name]+=1
                return result(*args,**kwargs)
            return f
        native=SimpleNamespace(
            l2norm_fwd=record('norm',lambda x:x),
            chunk_local_cumsum=record('cumsum',lambda x,**kw:x),
            chunk_scaled_dot_kkt_fwd=record('kkt',lambda **kw:kw['k']),
            solve_tril=record('solve',lambda **kw:kw['A']),
            recompute_w_u_fwd=record('wy',lambda **kw:(kw['k'],kw['v'])))
        def state(k,w,u,**kw):
            seen.append((k,w,u,kw))
            h=kw['initial_state']
            # This is only an ABI/lifetime control, not numerical NPU proof.
            return h,u,h.clone()
        def output(q,k,v,h,scale,**kw):return v
        q=torch.ones(1,7,2,3,dtype=torch.bfloat16)
        v=torch.ones(1,7,2,5,dtype=torch.bfloat16)
        g=torch.zeros(1,7,2);beta=torch.ones_like(g)
        meta=SimpleNamespace(cu_seqlens_host=(0,2,7),chunk_indices_chunk64_host=(0,0,1,0),
            block_indices_cumsum=None,chunk_indices_chunk64=None,chunk_indices_large_block=None)
        packed=prepare_shared_wy(q,q.clone(),v,g,beta,meta=meta,native=native,
                                 state_op=state,output_op=output)
        t,s=packed.affine_maps()
        self.assertEqual(tuple(t.shape),(2,2,3,3))
        self.assertEqual(tuple(s.shape),(2,2,3,5))
        out,final=packed.render(torch.zeros(2,2,3,5))
        self.assertEqual(tuple(out.shape),(1,7,2,5))
        self.assertEqual(calls,Counter(norm=2,cumsum=1,kkt=1,solve=1,wy=1))
        self.assertEqual(len(seen),3)
        self.assertTrue(all(x[0] is packed.k and x[1] is packed.w for x in seen))
        self.assertEqual(torch.count_nonzero(seen[1][2]).item(),0)
        self.assertTrue(torch.equal(seen[0][2],seen[2][2]))
        self.assertEqual(seen[0][3]['cu_seqlens'],(0,2,7))
        self.assertTrue(all(not x[3]['transpose_state_layout'] for x in seen))

    def test_geometry_rejects_before_primitives(self):
        q=torch.zeros(1,7,2,3,dtype=torch.bfloat16);v=torch.zeros(1,7,2,5,dtype=torch.bfloat16)
        g=torch.zeros(1,7,2)
        for starts in [(0,2,2,7),(0,6),(1,7),(0,True,7)]:
            meta=SimpleNamespace(cu_seqlens_host=starts)
            with self.assertRaises(ValueError):
                prepare_shared_wy(q,q,v,g,g,meta=meta,native=None,state_op=None,output_op=None)

if __name__=='__main__':unittest.main()
