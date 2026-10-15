import unittest
from types import SimpleNamespace
import torch
from independent_native_decode_pack import DecodeRow,pack_native_decode
from independent_native_decode_backend import run_private_native_decode
from independent_recurrent_boundary import recurrent_boundary

class BackendTests(unittest.TestCase):
    def setup_case(self):
        torch.manual_seed(471)
        n=3;hk=2;hv=4;dk=5;dv=3;c=2*hk*dk+hv*dv
        projected=torch.randn(n,c);b=torch.rand(n,hv)*.2;a=-torch.rand(n,hv)*.1
        conv=torch.randn(n,3,c)*.01
        state=torch.randn(n,hv,dv,dk)*.01
        rows=[DecodeRow(str(i),i,i,True) for i in range(n)]
        packed=pack_native_decode(rows,projected,b,a,conv,state)
        def split(x):
            q,k,v=x.split([hk*dk,hk*dk,hv*dv],dim=-1)
            return q.reshape(1,-1,hk,dk),k.reshape(1,-1,hk,dk),v.reshape(1,-1,hv,dv)
        layer=SimpleNamespace(conv1d=SimpleNamespace(weight=torch.ones(c,4),bias=None),
            activation=True,rearrange_mixed_qkv=split,A_log=None,dt_bias=None)
        return layer,packed
    def test_full_path_batch_vs_independent_single_rows(self):
        layer,p=self.setup_case();calls=[]
        def conv(output,x,weights,**kw):
            n=x.shape[0];self.assertEqual(kw["query_start_loc_opt"].tolist(),list(range(n+1)))
            self.assertEqual(kw["cache_indices_opt"].tolist(),list(range(n)))
            tail=kw["conv_state"]
            output.copy_(torch.nn.functional.silu(x+tail.sum(1)))
            tail.copy_(torch.cat((tail[:,1:].clone(),x[:,None]),dim=1))
        def norm(x):
            return x*torch.rsqrt(x.square().sum(-1,keepdim=True)+1e-6)
        def gating(A,a,b,dt):return a[None],b[None]
        def rec(**kw):
            n=kw["query"].shape[0];calls.append(n)
            self.assertEqual(kw["actual_seq_lengths"].tolist(),[0]+[1]*n)
            self.assertEqual(kw["ssm_state_indices"].tolist(),list(range(n)))
            outs=[]
            for i in range(n):
                q=kw["query"][i];k=kw["key"][i];v=kw["value"][i]
                q=q.repeat_interleave(v.shape[0]//q.shape[0],dim=0)
                k=k.repeat_interleave(v.shape[0]//k.shape[0],dim=0)
                h=kw["state"][i].transpose(-1,-2)
                beta=kw["beta"][i,:,None,None]
                h=kw["g"][i,:,None,None].exp()*(h-beta*k[:,:,None]*(k[:,None,:]@h))
                h=h+beta*k[:,:,None]*v[:,None,:]
                kw["state"][i].copy_(h.transpose(-1,-2))
                outs.append((q[:,None,:]@h).squeeze(1)*kw["scale"])
            return torch.stack(outs)
        initial=[p.projected.clone(),p.conv.clone(),p.state.clone()]
        result=run_private_native_decode(layer,p,ssm_index_dtype=torch.int32,backends=(conv,rec,norm,gating))
        self.assertEqual(calls,[3])
        for i,row in enumerate(p.rows):
            x=torch.nn.functional.silu(p.projected[i]+p.conv[i].sum(0))
            q,k,v=layer.rearrange_mixed_qkv(x[None])
            out,state=recurrent_boundary(q,k,v,p.a[i][None,None],p.b[i][None,None],
                p.state[i].transpose(-1,-2)[None].contiguous())
            torch.testing.assert_close(result[row.request_id][0],out[0,0],atol=1e-7,rtol=1e-6)
            torch.testing.assert_close(result[row.request_id][1],state[0],atol=1e-7,rtol=1e-6)
        for before,after in zip(initial,(p.projected,p.conv,p.state)):self.assertTrue(torch.equal(before,after))
    def test_requires_live_index_dtype(self):
        layer,p=self.setup_case()
        with self.assertRaises(ValueError):run_private_native_decode(layer,p,ssm_index_dtype=torch.float32,backends=(None,)*4)

if __name__=="__main__":unittest.main()
