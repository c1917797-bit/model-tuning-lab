import unittest
from types import SimpleNamespace as S
import torch
from independent_c1_short_prefix import align_short_prefix_terminals
from independent_recurrent_boundary import recurrent_boundary

class ShortPrefixTests(unittest.TestCase):
    def fixture(self,length,has_initial=True):
        torch.manual_seed(18)
        n=length+3;q=torch.randn(1,n,4,128,dtype=torch.bfloat16)
        k=torch.randn_like(q);v=torch.randn(1,n,12,128,dtype=torch.bfloat16)
        g=-torch.rand(1,n,12)*.05;beta=torch.rand(1,n,12)*.5
        initial=torch.randn(2,12,128,128) if has_initial else torch.zeros(2,12,128,128)
        terminals=torch.randn_like(initial)
        windows=(S(request_id="r",packed_start=0,packed_end=length,source_start=0,source_end=length),
                 S(request_id="r",packed_start=length,packed_end=n,source_start=length,source_end=n))
        layout=S(request_ids=("r",),chains=((("live",0),("cached","body"),("live",1)),),windows=windows)
        return layout,q,k,v,g,beta,initial,terminals

    def test_lengths_one_eight_sixtyfour_and_actual_geometry(self):
        for n in (1,8,64):
            for has_initial in (False,True):
                args=self.fixture(n,has_initial);before=[x.clone() for x in args[1:]]
                result,routes=align_short_prefix_terminals(*args)
                _,expected=recurrent_boundary(args[1][:,:n],args[2][:,:n],args[3][:,:n],
                    args[4][:,:n],args[5][:,:n],args[6][:1])
                self.assertTrue(torch.equal(result[0],expected[0]))
                self.assertTrue(torch.equal(result[1],args[-1][1]))
                self.assertEqual(routes[0]["branch"],"independent_recurrent_le64")
                self.assertEqual(routes[0]["rows"],n)
                for original,saved in zip(args[1:],before):self.assertTrue(torch.equal(original,saved))

    def test_long_sixtyfive_unchanged(self):
        args=self.fixture(65);calls=[]
        result,routes=align_short_prefix_terminals(*args,input_observer=lambda *a,**k:calls.append(k))
        self.assertTrue(torch.equal(result,args[-1]));self.assertFalse(calls)
        self.assertEqual(routes[0]["branch"],"official_chunk64")

    def test_actual_observer_input_and_exception_no_source_mutation(self):
        args=self.fixture(8);seen=[];saved=args[-1].clone()
        def observe(j,**values):
            seen.append((j,values))
            self.assertEqual(values["branch"],"independent_recurrent_le64")
            self.assertEqual(tuple(values["q"].shape),(1,8,12,128))
        align_short_prefix_terminals(*args,input_observer=observe)
        self.assertEqual(len(seen),1);self.assertEqual(seen[0][0],0)
        def fail(*a,**k):raise RuntimeError("observer failed")
        with self.assertRaises(RuntimeError):align_short_prefix_terminals(*args,input_observer=fail)
        self.assertTrue(torch.equal(args[-1],saved))

    def test_source_window_reject(self):
        args=self.fixture(8);args[0].windows[0].source_end=9
        with self.assertRaises(ValueError):align_short_prefix_terminals(*args)

    def test_multiple_distinct_prefix_lengths(self):
        args=list(self.fixture(8));layout=args[0]
        layout.request_ids=("a","b");layout.chains=((("live",0),),(("live",1),))
        layout.windows=(S(request_id="a",packed_start=0,packed_end=8,source_start=0,source_end=8),
                        S(request_id="b",packed_start=8,packed_end=11,source_start=23,source_end=26))
        result,routes=align_short_prefix_terminals(*args)
        self.assertEqual([r["rows"] for r in routes],[8,3])
        _,expected=recurrent_boundary(args[1][:,8:11],args[2][:,8:11],args[3][:,8:11],
                                     args[4][:,8:11],args[5][:,8:11],args[6][1:2])
        self.assertTrue(torch.equal(result[1],expected[0]))

if __name__=="__main__":unittest.main()
