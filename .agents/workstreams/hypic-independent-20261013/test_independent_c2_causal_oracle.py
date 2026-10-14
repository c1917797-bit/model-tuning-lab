"""Independent dense attention oracle for the two-window causal plan."""
import unittest
import torch
from independent_request_map import RequestSlice
from independent_segment_selection import SegmentSelection
from independent_c2_query_plan import plan_c2_queries


def dense_causal(q,k,v,positions):
    scores=q@k.T
    mask=torch.arange(k.shape[0])[None,:]>torch.tensor(positions)[:,None]
    return torch.softmax(scores.masked_fill(mask,float('-inf')),dim=-1)@v


class CausalOracleTests(unittest.TestCase):
    def test_two_windows_equal_full_causal_retained_queries(self):
        generator=torch.Generator().manual_seed(27)
        q=torch.randn(20,7,generator=generator,dtype=torch.float64)
        k=torch.randn(20,7,generator=generator,dtype=torch.float64)
        v=torch.randn(20,5,generator=generator,dtype=torch.float64)
        req=RequestSlice('r',0,2,0,20,0,0,20)
        p=plan_c2_queries(req,SegmentSelection(4,16,False,'x'),seam_tokens=3,public_length=12)
        reference=dense_causal(q,k,v,range(20))[list(p.retained_offsets)]
        pieces=[]
        for w in p.windows:
            pieces.append(dense_causal(q[w.query_start:w.query_end],
                k[:w.kv_end],v[:w.kv_end],range(w.kv_end-(w.query_end-w.query_start),w.kv_end)))
        torch.testing.assert_close(torch.cat(pieces),reference,rtol=1e-12,atol=1e-12)
        # Negative control: one compact bottom-right causal call exposes future
        # keys to prefix/seam queries, even though all tensor sizes are valid.
        bad=dense_causal(q[list(p.retained_offsets)],k,v,range(20-len(p.retained_offsets),20))
        self.assertGreater(float((bad-reference).abs().max()),0.1)


if __name__=='__main__':unittest.main()
