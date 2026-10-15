import unittest
from dataclasses import replace
from types import SimpleNamespace
import torch
import test_independent_c1_packed_wave as fixture
from independent_c1_prefix_seeds import prefix_initial_seeds,suffix_seeds_from_terminals
from independent_c1_packed_wave import propagate_window_seeds
from independent_c1_reference import SegmentAffine

class PrefixSeedTests(unittest.TestCase):
    def test_actual_prefix_matches_serial_even_for_nonlinear_rounding(self):
        for no_suffix in (False,True):
            _,_,layout,initial,cached,_,_=fixture.PackedWaveTests().fixture(no_suffix)
            original=initial.clone()
            gen=torch.Generator().manual_seed(744)
            matrices=[torch.randn(2,5,5,generator=gen,dtype=torch.float64)*.13 for _ in layout.windows]
            offsets=[torch.randn(2,5,3,generator=gen,dtype=torch.float64)*.2 for _ in layout.windows]
            def rounded(job,state):
                return (matrices[job]@state+offsets[job]).to(torch.bfloat16).to(torch.float64)
            seeds=prefix_initial_seeds(layout,initial)
            prefix=torch.stack([rounded(j,seeds[j]) for j in range(len(layout.windows))])
            actual=suffix_seeds_from_terminals(layout,seeds,prefix,cached)
            finals=torch.stack([rounded(j,actual[j]) for j in range(len(layout.windows))])
            maps=[SegmentAffine(a.to(torch.bfloat16).double(),s.to(torch.bfloat16).double())
                  for a,s in zip(matrices,offsets)]
            old_seeds,_=propagate_window_seeds(layout,initial,maps,cached)
            difference=0.
            for row,chain in enumerate(layout.chains):
                if not chain:continue
                h=initial[row].clone() if layout.has_initial[row] else torch.zeros_like(initial[row])
                for kind,key in chain:
                    if kind=='live':
                        torch.testing.assert_close(actual[key],h,atol=1e-12,rtol=1e-12)
                        h=rounded(key,h)
                    else:h=cached[key].transition@h+cached[key].zero_state
                last=chain[-1]
                got=finals[last[1]] if last[0]=='live' else (
                    cached[last[1]].transition@finals[chain[0][1]]+cached[last[1]].zero_state)
                torch.testing.assert_close(got,h,atol=1e-12,rtol=1e-12)
                if len(chain)==3:
                    j=chain[2][1];difference=max(difference,float((actual[j]-old_seeds[j]).abs().max()))
            self.assertGreater(difference,1e-4)
            self.assertTrue(torch.equal(initial,original))

    def test_reset_suffix_dummy_and_input_ownership(self):
        _,_,layout,initial,cached,_,_=fixture.PackedWaveTests().fixture()
        seeds=prefix_initial_seeds(layout,initial)
        self.assertEqual(float(seeds[layout.chains[0][0][1]].abs().sum()),0.)
        for chain in layout.chains:
            if len(chain)==3:self.assertEqual(float(seeds[chain[2][1]].abs().sum()),0.)
        original=seeds.clone();terminal=torch.ones_like(seeds)
        suffix_seeds_from_terminals(layout,seeds,terminal,cached).zero_()
        self.assertTrue(torch.equal(seeds,original))

    def test_missing_maps_bad_shape_and_geometry_reject(self):
        _,_,layout,initial,cached,_,_=fixture.PackedWaveTests().fixture()
        seeds=prefix_initial_seeds(layout,initial)
        with self.assertRaises(ValueError):suffix_seeds_from_terminals(layout,seeds,seeds,{})
        with self.assertRaises(ValueError):suffix_seeds_from_terminals(layout,seeds,seeds[:-1],cached)
        with self.assertRaises(ValueError):prefix_initial_seeds(layout,initial[:1])
        broken=replace(layout,chains=(('cached','shared'),)+layout.chains[1:])
        with self.assertRaises(ValueError):prefix_initial_seeds(broken,initial)

if __name__=='__main__':unittest.main()
