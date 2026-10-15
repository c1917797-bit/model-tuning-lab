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

    def test_native_tp4_grouped_head_abi(self):
        seen={}
        def kkt(**kw):
            seen['kkt']=(kw['k'].shape,kw['beta'].shape)
            return kw['k']
        def wy(**kw):
            seen['wy']=(kw['k'].shape,kw['v'].shape)
            return kw['k'].repeat_interleave(3,2),kw['v']
        native=SimpleNamespace(l2norm_fwd=lambda x:x,
            chunk_local_cumsum=lambda x,**kw:x,chunk_scaled_dot_kkt_fwd=kkt,
            solve_tril=lambda **kw:kw['A'],recompute_w_u_fwd=wy)
        q=torch.ones(1,7,4,128,dtype=torch.bfloat16)
        v=torch.ones(1,7,12,96,dtype=torch.bfloat16)
        g=torch.zeros(1,7,12)
        meta=SimpleNamespace(cu_seqlens_host=(0,2,7),chunk_indices_chunk64_host=(),
            block_indices_cumsum=None,chunk_indices_chunk64=None,chunk_indices_large_block=None)
        def state(k,w,u,**kw):
            self.assertEqual(k.shape,(1,4,7,128))
            self.assertEqual(w.shape,(1,12,7,128))
            self.assertEqual(u.shape,(1,12,7,96))
            self.assertEqual(kw['initial_state'].shape,(2,12,128,96))
            return None,u,kw['initial_state'].clone()
        def output(q,k,v,h,scale,**kw):
            self.assertEqual(q.shape,(1,4,7,128));return v
        shared=prepare_shared_wy(q,q.clone(),v,g,g,meta=meta,native=native,
                                state_op=state,output_op=output)
        out,final=shared.render(torch.zeros(2,12,128,96))
        self.assertEqual(out.shape,(1,7,12,96))
        self.assertEqual(final.shape,(2,12,128,96))
        self.assertEqual(seen['kkt'],(q.shape,g.shape))
        self.assertEqual(seen['wy'],(q.shape,v.shape))
        # Malformed grouping/gates must fail before any official primitive.
        for bad_v,bad_g in ((v[:,:,:11],g[:,:,:11]),(v,g[:,:,:4]),
                            (v[:,:6],g[:,:6]),(v[:,:,:0],g[:,:,:0])):
            with self.assertRaises(ValueError):
                prepare_shared_wy(q,q,bad_v,bad_g,bad_g,meta=meta,native=None,
                                  state_op=None,output_op=None)

    def test_geometry_rejects_before_primitives(self):
        q=torch.zeros(1,7,2,3,dtype=torch.bfloat16);v=torch.zeros(1,7,2,5,dtype=torch.bfloat16)
        g=torch.zeros(1,7,2)
        for starts in [(0,2,2,7),(0,6),(1,7),(0,True,7)]:
            meta=SimpleNamespace(cu_seqlens_host=starts)
            with self.assertRaises(ValueError):
                prepare_shared_wy(q,q,v,g,g,meta=meta,native=None,state_op=None,output_op=None)

if __name__=='__main__':unittest.main()
