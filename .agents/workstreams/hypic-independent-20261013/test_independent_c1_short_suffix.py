import unittest
from types import SimpleNamespace as S
from unittest.mock import patch
import torch
from independent_c1_short_suffix import align_short_suffixes
from independent_recurrent_boundary import recurrent_boundary

class ShortSuffixTests(unittest.TestCase):
    def fixture(self,n):
        torch.manual_seed(22);total=3+n
        q=torch.randn(1,total,2,8,dtype=torch.bfloat16);k=torch.randn_like(q)
        v=torch.randn(1,total,6,8,dtype=torch.bfloat16)
        g=-torch.rand(1,total,6)*.05;beta=torch.rand(1,total,6)*.5
        seeds=torch.randn(2,6,8,8);y=torch.randn_like(v);h=torch.randn_like(seeds)
        windows=(S(request_id="r",packed_start=0,packed_end=3,source_start=0,source_end=3),
                 S(request_id="r",packed_start=3,packed_end=total,source_start=15467,source_end=15467+n))
        layout=S(request_ids=("r",),chains=((("live",0),("cached","b"),("live",1)),),windows=windows)
        return layout,q,k,v,g,beta,seeds,y,h

    def test_short_suffix_exact_canonical_output_and_terminal(self):
        for n in (1,28,56,63,64):
            with self.subTest(n=n):
                args=self.fixture(n);saved=[x.clone()for x in args[1:]]
                y,h,routes=align_short_suffixes(*args)
                ey,eh=recurrent_boundary(args[1][:,3:],args[2][:,3:],args[3][:,3:],
                    args[4][:,3:],args[5][:,3:],args[6][1:2])
                self.assertTrue(torch.equal(y[:,3:],ey))
                self.assertTrue(torch.equal(h[1],eh[0]))
                self.assertTrue(torch.equal(y[:,:3],args[-2][:,:3]))
                self.assertTrue(torch.equal(h[0],args[-1][0]))
                self.assertEqual(routes[0]["rows"],n)
                for a,b in zip(args[1:],saved):self.assertTrue(torch.equal(a,b))

    def test_actual_tp4_geometry_56(self):
        args=list(self.fixture(56));torch.manual_seed(27)
        total=59
        args[1]=torch.randn(1,total,4,128,dtype=torch.bfloat16);args[2]=torch.randn_like(args[1])
        args[3]=torch.randn(1,total,12,128,dtype=torch.bfloat16)
        args[4]=-torch.rand(1,total,12)*.05;args[5]=torch.rand(1,total,12)*.5
        args[6]=torch.randn(2,12,128,128);args[7]=torch.randn_like(args[3]);args[8]=torch.randn_like(args[6])
        y,h,r=align_short_suffixes(*args)
        ey,eh=recurrent_boundary(args[1][:,3:],args[2][:,3:],args[3][:,3:],args[4][:,3:],args[5][:,3:],args[6][1:2])
        self.assertTrue(torch.equal(y[:,3:],ey));self.assertTrue(torch.equal(h[1],eh[0]))

    def test_long_suffix_unchanged_no_recurrence(self):
        args=self.fixture(65)
        with patch("independent_c1_short_suffix.recurrent_boundary",side_effect=AssertionError):
            y,h,r=align_short_suffixes(*args)
        self.assertTrue(torch.equal(y,args[-2]));self.assertTrue(torch.equal(h,args[-1]));self.assertEqual(r,[])

    def test_bad_geometry_no_input_mutation(self):
        args=self.fixture(56);args[0].windows[1].source_end+=1
        y=args[-2].clone();h=args[-1].clone()
        with self.assertRaises(ValueError):align_short_suffixes(*args)
        self.assertTrue(torch.equal(args[-2],y));self.assertTrue(torch.equal(args[-1],h))

    def test_no_suffix_native_or_tail_unchanged(self):
        args=self.fixture(56);args[0].chains=((("live",0),("cached","b")),)
        y,h,r=align_short_suffixes(*args)
        self.assertTrue(torch.equal(y,args[-2]));self.assertTrue(torch.equal(h,args[-1]));self.assertEqual(r,[])

    def test_opt_in_route_and_validation(self):
        from independent_compact_activation import c1_install_route
        _,install,_=c1_install_route({})
        self.assertFalse(install.c1_short_suffix_recurrent)
        valid=dict(c1_packed_wave=True,native_decode_batch=True,c1_layer_completion_barrier=True,
                   c1_performance_mode=True,c1_short_prefix_terminal_policy="canonical_recurrent_le64",
                   c1_short_suffix_recurrent=True)
        config,install,_=c1_install_route(valid)
        self.assertTrue(install.c1_short_suffix_recurrent);self.assertNotIn("c1_short_suffix_recurrent",config)
        for bad in (1,"yes",None):
            with self.assertRaises(ValueError):c1_install_route(dict(valid,c1_short_suffix_recurrent=bad))
        with self.assertRaises(ValueError):c1_install_route(dict(valid,c1_short_prefix_terminal_policy="chunk64"))
        with self.assertRaises(ValueError):c1_install_route(dict(valid,c1_packed_wave=False))

if __name__=="__main__":unittest.main()
