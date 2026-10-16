import unittest
from types import SimpleNamespace as NS
import torch
from independent_c1_shared_wy import SharedWY
from independent_c1_prefix_seeds import prefix_initial_seeds,suffix_seeds_from_terminals
from experimental_c1_partitioned_render import render_partitioned

class Metadata:
    def get(self,starts,**kw):
        return NS(cu_seqlens_host=starts,chunk_indices_chunk64_host=tuple(
            x for j in range(len(starts)-1) for x in (j,0)))

class PartitionTests(unittest.TestCase):
    def fixture(self,tail_only=False,lengths=None):
        lengths=lengths or ([2,3,1] if not tail_only else [2,3])
        starts=[0]
        for x in lengths:starts.append(starts[-1]+x)
        chains=((("live",0),("cached","b"),("live",1)),(("live",2),)) if not tail_only else (
            (("live",0),("cached","b")),(("live",1),))
        windows=[]
        for j in range(len(lengths)):
            row=0 if j==0 or (not tail_only and j==1) else 1
            windows.append(NS(request_row=row,packed_start=starts[j],packed_end=starts[j+1]))
        layout=NS(request_ids=("a","b"),has_initial=(True,False),chains=chains,
                  windows=windows,packed_tokens=starts[-1])
        calls=[]
        def state(k,w,u,**kw):
            s=kw["cu_seqlens"];h=kw["initial_state"].clone();v=u.float().clone()
            calls.append((tuple(s),h.clone()))
            for j,(lo,hi) in enumerate(zip(s,s[1:])):
                for p in range(lo,hi):
                    h[j]+=u[0,:,p,:].float().unsqueeze(-2)
                    v[0,:,p,:]=h[j].squeeze(-2)
            return None,v,h
        u=torch.arange(1,starts[-1]*2+1,dtype=torch.float32).reshape(1,2,starts[-1],1)
        q=torch.zeros(1,1,starts[-1],1)
        shared=SharedWY(q,q.clone(),u.clone(),u,torch.zeros(1,2,starts[-1]),
                        tuple(starts),(),state,lambda q,k,v,h,scale,**kw:v,1.)
        initial=torch.ones(2,2,1,1)
        maps={"b":NS(transition=torch.full((2,1,1),2.),zero_state=torch.full((2,1,1),3.))}
        return layout,shared,initial,maps,calls
    def compare(self,tail_only=False,align=False,lengths=None):
        layout,shared,initial,maps,calls=self.fixture(tail_only,lengths)
        seeds0=prefix_initial_seeds(layout,initial)
        _,_,p=shared.state(seeds0.clone())
        def alignment(i,p):
            p=p.clone()
            for chain in layout.chains:
                j=chain[0][1]
                if shared.starts[j+1]-shared.starts[j]<=64:p[j]+=7
            return p
        if align:p=alignment(seeds0,p)
        seeds=suffix_seeds_from_terminals(layout,seeds0,p,maps)
        expected,final=shared.render(seeds)
        if align:
            for chain in layout.chains:
                live=[j for kind,j in chain if kind=="live"]
                j=live[0]
                if len(live)==1 and shared.starts[j+1]-shared.starts[j]<=64:final[j]=p[j]
        initial_before=initial.clone();u_before=shared.u.clone();calls.clear()
        result=render_partitioned(shared,layout,initial,maps,metadata_cache=Metadata(),
            total_value_heads=8,tp_size=4,align_prefix=alignment if align else None)
        self.assertTrue(torch.equal(expected,result.output))
        self.assertTrue(torch.equal(final,result.terminal))
        self.assertEqual(result.state_window_visits,len(layout.windows))
        self.assertEqual(result.state_token_visits,layout.packed_tokens)
        self.assertEqual(sum(x[0][-1] for x in calls),layout.packed_tokens)
        self.assertTrue(torch.equal(initial,initial_before))
        self.assertTrue(torch.equal(shared.u,u_before))
    def test_prefix_suffix_native_interleave(self):self.compare()
    def test_cached_tail_no_suffix(self):self.compare(tail_only=True)
    def test_aligned_prefix_feeds_suffix(self):self.compare(align=True)
    def test_aligned_prefix_terminal_without_suffix(self):self.compare(tail_only=True,align=True)
    def test_chunk_boundaries(self):
        for n in (1,63,64,65,127,128,129):
            with self.subTest(n=n):self.compare(lengths=[n,129,65],align=True)
    def test_long_cached_tail_and_long_native_window(self):
        self.compare(tail_only=True,align=True,lengths=[129,65])
    def test_seeded_window_geometries(self):
        import random
        rng=random.Random(2607)
        for _ in range(17):
            lengths=[rng.randint(1,256) for _ in range(3)]
            with self.subTest(lengths=lengths):self.compare(lengths=lengths,align=True)
    def test_bad_geometry_rejected(self):
        l,s,i,m,_=self.fixture();l.windows[1].packed_end+=1
        with self.assertRaises(ValueError):
            render_partitioned(s,l,i,m,metadata_cache=Metadata(),total_value_heads=8,tp_size=4)
    def test_duplicate_window_rejected(self):
        l,s,i,m,_=self.fixture();l.chains=(l.chains[0],(("live",0),))
        with self.assertRaises(ValueError):
            render_partitioned(s,l,i,m,metadata_cache=Metadata(),total_value_heads=8,tp_size=4)
    def test_alignment_cannot_change_suffix(self):
        l,s,i,m,_=self.fixture()
        with self.assertRaises(ValueError):
            render_partitioned(s,l,i,m,metadata_cache=Metadata(),total_value_heads=8,tp_size=4,
                               align_prefix=lambda i,p:p+1)
    def test_bad_metadata_rejected(self):
        l,s,i,m,_=self.fixture()
        class Bad:
            def get(self,*a,**kw):return NS(cu_seqlens_host=(0,999),chunk_indices_chunk64_host=())
        with self.assertRaises(ValueError):
            render_partitioned(s,l,i,m,metadata_cache=Bad(),total_value_heads=8,tp_size=4)

if __name__=="__main__":unittest.main()
