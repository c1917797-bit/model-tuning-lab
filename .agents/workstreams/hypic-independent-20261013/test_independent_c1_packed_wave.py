import unittest
from types import SimpleNamespace
import torch
from independent_c1_packed_wave import build_wave_layout,propagate_window_seeds,execute_packed_c1
from independent_request_map import RequestSlice
from independent_segment_selection import SegmentSelection
from independent_c2_query_plan import plan_c2_queries
from independent_mixed_query_plan import NativeQueryPlan
from independent_linear_map import LinearSlice
from independent_c1_reference import accumulate_segment,serial_dense_oracle,SegmentAffine


class PackedWaveTests(unittest.TestCase):
    def fixture(self,no_suffix=False):
        lengths=[12 if no_suffix else 16,18,3,1]
        plans=[];associations=[];cursor=0
        for row,length in enumerate(lengths):
            rid=str(row);computed=0 if row==0 else 2
            req=RequestSlice(rid,0,7,computed,length,row,cursor,cursor+length)
            if row<2:
                start=computed+2;end=computed+12
                plan=plan_c2_queries(req,SegmentSelection(start,end,False,"shared"),seam_tokens=3,public_length=10)
            else:plan=NativeQueryPlan(rid,0,7,cursor,computed,length,"decode" if length==1 else "prefill")
            plans.append(plan);associations.append(LinearSlice(rid,0,7,row,row,cursor,cursor+length,computed>0))
            cursor+=length
        layout=build_wave_layout(plans,associations)
        gen=torch.Generator().manual_seed(921)
        initial=torch.randn(4,2,5,3,generator=gen,dtype=torch.float64)
        # Shared body maps, arbitrary unequal K/V dimensions.
        bk=torch.randn(7,2,5,generator=gen,dtype=torch.float64)*.1
        bv=torch.randn(7,2,3,generator=gen,dtype=torch.float64)
        beta=torch.full((7,2),.2,dtype=torch.float64);decay=torch.full((7,2),.9,dtype=torch.float64)
        cached={"shared":accumulate_segment(bk,bv,beta,decay)}
        data=[];maps=[]
        for window in layout.windows:
            count=window.packed_end-window.packed_start
            k=torch.randn(count,2,5,generator=gen,dtype=torch.float64)*.1
            v=torch.randn(count,2,3,generator=gen,dtype=torch.float64)
            b=torch.full((count,2),.2,dtype=torch.float64);g=torch.full((count,2),.9,dtype=torch.float64)
            data.append((k,v,b,g));maps.append(accumulate_segment(k,v,b,g))
        return plans,associations,layout,initial,cached,data,maps

    def test_packed_state_and_outputs_match_serial_chain(self):
        for no_suffix in (False,True):
            plans,assoc,layout,initial,cached,data,maps=self.fixture(no_suffix)
            original=initial.clone();calls=[]
            def prepare(given):self.assertIs(given,layout);calls.append("prepare");return data
            def derive(given):self.assertIs(given,data);calls.append("derive-all");return maps
            def render(given,seeds):
                calls.append("render-all");pieces=[]
                for index,(k,v,b,g) in enumerate(given):
                    h=seeds[index];outputs=[]
                    for token in range(k.shape[0]):
                        h=serial_dense_oracle(k[token:token+1],v[token:token+1],b[token:token+1],g[token:token+1],h)
                        outputs.append(h.sum(-2))
                    pieces.append(torch.stack(outputs))
                return torch.cat(pieces)
            result=execute_packed_c1(layout,initial,cached,prepare=prepare,derive=derive,render=render)
            self.assertEqual(calls,["prepare","derive-all","render-all"])
            for row,chain in enumerate(layout.chains):
                if not chain:continue
                h=initial[row].clone() if assoc[row].has_initial_state else torch.zeros_like(initial[row])
                pieces=[]
                for kind,key in chain:
                    if kind=="cached":h=cached[key].transition@h+cached[key].zero_state
                    else:
                        k,v,b,g=data[key];ys=[]
                        for token in range(k.shape[0]):
                            h=serial_dense_oracle(k[token:token+1],v[token:token+1],b[token:token+1],g[token:token+1],h)
                            ys.append(h.sum(-2))
                        pieces.append(torch.stack(ys))
                torch.testing.assert_close(result[str(row)][1],h,atol=1e-12,rtol=1e-12)
                torch.testing.assert_close(result[str(row)][0],torch.cat(pieces),atol=1e-12,rtol=1e-12)
            self.assertTrue(torch.equal(initial,original))
            self.assertNotIn("3",result)

    def test_exact_private_membership_and_native1_separation(self):
        plans,assoc,layout,*_=self.fixture()
        self.assertEqual(layout.native_one_rows,(3,))
        self.assertEqual(layout.state_slots,(0,1,2,3))
        self.assertEqual(len(layout.windows),5)
        self.assertEqual(layout.packed_tokens,sum(len(p.retained_offsets) for p in plans[:-1]))
        with self.assertRaises(ValueError):build_wave_layout(plans,assoc[:-1])
        alias=list(assoc);alias[1]=SimpleNamespace(**{**vars(alias[1]),"state_slot":0})
        with self.assertRaises(ValueError):build_wave_layout(plans,alias)
        with self.assertRaises(ValueError):build_wave_layout(plans,assoc,separate_native_one="true")

    def test_map_shape_dtype_and_coverage_fail_closed(self):
        *_,layout,initial,cached,data,maps=self.fixture()
        with self.assertRaises(ValueError):propagate_window_seeds(layout,initial,maps[:-1],cached)
        with self.assertRaises(ValueError):propagate_window_seeds(layout,initial,maps,{})
        bad=list(maps);bad[0]=SegmentAffine(torch.eye(4,dtype=torch.float64)[None].expand(2,-1,-1),maps[0].zero_state)
        with self.assertRaises(ValueError):propagate_window_seeds(layout,initial,bad,cached)
        with self.assertRaises(ValueError):propagate_window_seeds(layout,initial.float(),maps,cached)

    def test_wrong_order_is_numerically_detectable(self):
        plans,assoc,layout,initial,cached,data,maps=self.fixture()
        seeds,final=propagate_window_seeds(layout,initial,maps,cached)
        h=initial[0]*0
        wrong=cached["shared"].transition@h+cached["shared"].zero_state
        wrong=maps[0].transition@wrong+maps[0].zero_state
        wrong=maps[1].transition@wrong+maps[1].zero_state
        self.assertGreater(float((wrong-final["0"]).abs().max()),1e-5)

if __name__=="__main__":unittest.main()
