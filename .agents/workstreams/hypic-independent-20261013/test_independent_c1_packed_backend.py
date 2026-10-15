import unittest
from types import SimpleNamespace
from collections import Counter
import torch
import test_independent_c1_packed_wave as wave_fixture
from independent_c1_window_pack import pack_windows
from independent_c1_packed_metadata import PackedMetadataCache
from independent_c1_packed_backend import run_packed_c1

class PackedBackendTests(unittest.TestCase):
    def fixture(self,no_suffix=False):
        # Reuse data constructor only, not its test class/discovery.
        return wave_fixture.PackedWaveTests().fixture(no_suffix)

    def inputs(self,layout):
        gen=torch.Generator().manual_seed(46)
        total=max(w.source_end for w in layout.windows)+1
        projected=torch.randn(total,16,generator=gen,dtype=torch.float32).to(torch.bfloat16)*.1
        b=torch.zeros(total,2,dtype=torch.bfloat16);a=b.clone()
        tail=torch.randn(len(layout.request_ids),3,16,generator=gen)*.03
        for i,has in enumerate(layout.has_initial):
            if not has:tail[i].zero_()
        cached={"shared":torch.randn(3,16,generator=gen)*.02}
        return projected,b,a,tail,cached

    def test_window_rows_private_and_canonical_suffix(self):
        *_,layout,initial,cached,data,maps=self.fixture()
        x,b,a,tail,ct=self.inputs(layout)
        originals=[v.clone() for v in (x,tail,ct["shared"])]
        packed=pack_windows(layout,x,b,a,tail,ct)
        for j,w in enumerate(layout.windows):
            torch.testing.assert_close(packed.projected[w.packed_start:w.packed_end],
                                       x[w.source_start:w.source_end])
            action=layout.chains[w.request_row].index(("live",j))
            expected=tail[w.request_row] if action==0 else ct["shared"]
            torch.testing.assert_close(packed.conv[j],expected.to(x.dtype))
        packed.projected.zero_();packed.conv.zero_()
        for got,old in zip((x,tail,ct["shared"]),originals):self.assertTrue(torch.equal(got,old))
        with self.assertRaises(ValueError):pack_windows(layout,x,b,a,tail,{})
        with self.assertRaises(ValueError):pack_windows(layout,x,b[:1],a,tail,ct)

    def test_metadata_geometry_cache_bounded(self):
        calls=[]
        def build(builder,starts,device):
            calls.append((tuple(starts.tolist()),str(device)))
            return SimpleNamespace(cu_seqlens_host=tuple(starts.tolist()),chunk_indices_chunk64_host=())
        c=PackedMetadataCache(build,capacity=2)
        first=c.get((0,2,8),total_value_heads=48,tp_size=4,device="cpu")
        self.assertIs(first,c.get((0,2,8),total_value_heads=48,tp_size=4,device="cpu"))
        c.get((0,3),total_value_heads=48,tp_size=4,device="cpu")
        c.get((0,4),total_value_heads=48,tp_size=4,device="cpu")
        self.assertEqual(len(c.entries),2);self.assertEqual(len(calls),3)
        for starts in ((0,0,5),(1,5),(0,40961),(0,True,5)):
            with self.assertRaises(ValueError):c.get(starts,total_value_heads=48,tp_size=4,device="cpu")
        c.clear();self.assertFalse(c.entries)

    def full_private_backend_case(self,round_state=False,canonical=False):
        from independent_c1_reference import serial_dense_oracle
        for no_suffix in (False,True):
            plans,associations,layout,initial,cached,data,maps=self.fixture(no_suffix)
            initial=initial.float();cached={k:SimpleNamespace(
                transition=v.transition.float(),zero_state=v.zero_state.float()) for k,v in cached.items()}
            x,b,a,tail,ct=self.inputs(layout)
            material={k:SimpleNamespace(affine=cached[k],conv_tail=v) for k,v in ct.items()}
            calls=Counter()
            def convolution(values,seed):
                history=seed.to(values.dtype).clone();ys=[]
                for value in values:
                    y=(history.sum(0)+value)*.25
                    ys.append(y);history=torch.cat((history[1:],value[None]),0)
                return torch.stack(ys),history
            def conv_op(out,values,weight,**kw):
                calls["conv"]+=1
                starts=kw["query_start_loc_opt"].tolist()
                for j,(lo,hi) in enumerate(zip(starts,starts[1:])):
                    y,last=convolution(values[lo:hi],kw["conv_state"][j])
                    out[lo:hi].copy_(y);kw["conv_state"][j].copy_(last)
            def rearrange(values):
                return (values[:,:5].reshape(1,-1,1,5),
                        values[:,5:10].reshape(1,-1,1,5),
                        values[:,10:].reshape(1,-1,2,3))
            def gating(A,a,b,bias):
                calls["gating"]+=1
                return torch.full((1,len(a),2),-.03),torch.full((1,len(a),2),.1)
            def counted(name,fn):
                def call(*args,**kw):calls[name]+=1;return fn(*args,**kw)
                return call
            native=SimpleNamespace(l2norm_fwd=counted("norm",lambda z:z),
                chunk_local_cumsum=counted("cumsum",lambda z,**kw:z),
                chunk_scaled_dot_kkt_fwd=counted("kkt",lambda **kw:kw["k"]),
                solve_tril=counted("solve",lambda **kw:kw["A"]),
                recompute_w_u_fwd=counted("wy",lambda **kw:(
                    kw["k"].repeat_interleave(kw["v"].shape[2]//kw["k"].shape[2],2),kw["v"])))
            def state_op(k,w,u,**kw):
                calls["state"]+=1
                self.assertEqual(k.shape[1],1)
                self.assertEqual(w.shape[1],2)
                # Mathematical expansion is confined to the fake official op.
                k=k.repeat_interleave(u.shape[1]//k.shape[1],1)
                starts=kw["cu_seqlens"];h=kw["initial_state"].clone()
                states=torch.empty(1,k.shape[1],k.shape[2],k.shape[3],u.shape[-1])
                for row,(lo,hi) in enumerate(zip(starts,starts[1:])):
                    for token in range(lo,hi):
                        key=k[0,:,token].float();value=u[0,:,token].float()
                        decay=kw["g"][0,:,token].exp()
                        h[row]=serial_dense_oracle(key[None],value[None],
                            torch.full((1,k.shape[1]),.1),decay[None],h[row])
                        if round_state:h[row]=h[row].to(torch.bfloat16).float()
                        states[0,:,token]=h[row]
                return states,u,h
            def output_op(q,k,v,history,scale,**kw):
                calls["output"]+=1
                self.assertEqual(q.shape[1],1)
                q=q.repeat_interleave(v.shape[1]//q.shape[1],1)
                return (q.float().unsqueeze(-1)*history).sum(-2)*scale
            def metadata(builder,starts,device):
                calls["metadata"]+=1
                return SimpleNamespace(cu_seqlens_host=tuple(starts.tolist()),
                    chunk_indices_chunk64_host=(),chunk_indices_chunk64=None,
                    block_indices_cumsum=None,chunk_indices_large_block=None)
            layer=SimpleNamespace(conv1d=SimpleNamespace(weight=torch.ones(16,1,4),bias=None),
                activation=False,rearrange_mixed_qkv=rearrange,A_log=None,dt_bias=None,
                num_v_heads=8,tp_size=4)
            before=[v.clone() for v in (x,tail,ct["shared"],initial)]
            geometry=[]
            routes=[]
            policy_kwargs=dict(short_prefix_policy="canonical_recurrent_le64",
                prefix_route_observer=routes.append) if canonical else {}
            result=run_packed_c1(layer,layout,x,b,a,initial,tail,material,backends=(
                native,conv_op,gating,state_op,output_op,PackedMetadataCache(metadata)),
                geometry_observer=geometry.append,**policy_kwargs)
            self.assertEqual(geometry,[dict(key_heads=1,query_heads=1,value_heads=2,
                wy_heads=2,gate_heads=2,key_width=5,value_width=3,head_layout="native_grouped")])
            for row,chain in enumerate(layout.chains):
                if not chain:continue
                h=initial[row].clone() if layout.has_initial[row] else torch.zeros_like(initial[row])
                c=tail[row].clone();ys=[]
                for kind,key in chain:
                    if kind=="cached":
                        h=cached[key].transition@h+cached[key].zero_state;c=ct[key].clone()
                    else:
                        window=layout.windows[key]
                        values=x[window.source_start:window.source_end]
                        y,c=convolution(values,c);q,k,v=rearrange(y)
                        original_q,original_k=q,k
                        before_window=h.clone()
                        q=q.repeat_interleave(2,2).float();k=k.repeat_interleave(2,2).float()
                        for token in range(len(values)):
                            h=serial_dense_oracle(k[:,token],v[:,token].float(),
                                torch.full((1,2),.1),torch.full((1,2),-.03).exp(),h)
                            if round_state:h=h.to(torch.bfloat16).float()
                            ys.append((q[0,token].unsqueeze(-1)*h).sum(-2)*5**-.5)
                        if canonical and chain[0]==("live",key) and len(values)<=64:
                            from independent_recurrent_boundary import recurrent_boundary
                            _,canonical_state=recurrent_boundary(original_q,original_k,v,
                                torch.full((1,len(values),2),-.03),
                                torch.full((1,len(values),2),.1),before_window[None])
                            h=canonical_state[0]
                actual=result[layout.request_ids[row]]
                torch.testing.assert_close(actual[0].float(),torch.stack(ys).to(torch.bfloat16).float(),atol=.002,rtol=.003)
                torch.testing.assert_close(actual[1],h,atol=2e-5,rtol=.002)
                torch.testing.assert_close(actual[2].float(),c.float(),atol=.001,rtol=.002)
            self.assertEqual(calls["conv"],1);self.assertEqual(calls["metadata"],1)
            self.assertEqual(calls["wy"],1);self.assertEqual(calls["state"],2)
            self.assertEqual(calls["output"],1)
            if canonical:
                self.assertEqual(len(routes),sum(bool(c) and c[0][0]=="live" for c in layout.chains))
                self.assertTrue(all(r["policy"]=="canonical_recurrent_le64" for r in routes))
            for got,old in zip((x,tail,ct["shared"],initial),before):self.assertTrue(torch.equal(got,old))

    def test_full_private_backend_against_serial_recurrence(self):self.full_private_backend_case()
    def test_nonzero_rounding_backend_against_serial(self):self.full_private_backend_case(round_state=True)
    def test_canonical_prefix_terminal_actually_feeds_cached_body_and_suffix(self):
        self.full_private_backend_case(canonical=True)

if __name__=="__main__":unittest.main()
