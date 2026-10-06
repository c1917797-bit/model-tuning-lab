import importlib.util
from pathlib import Path
import random
import sys
import unittest
BASE=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,BASE/(name+".py"))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
model=load("float_div_model")
gold=load("independent_float_div")
class FloatDivContract(unittest.TestCase):
    def assert_row(self,x,c):
        expected=gold.oracle(x,c)
        self.assertEqual(model.exact_div(x,c),expected,(hex(x),hex(c)))
        q=expected[2]&0x7fffffff
        if expected[0] and expected[1]:
            proposals={q}
            if q:proposals.add(q-1)
            if q<gold.MAX:proposals.add(q+1)
            for p in proposals:
                self.assertEqual(model.certifies(x,c,p),gold.oracle_certificate(x,c,p),
                                 (hex(x),hex(c),hex(p)))
    def test_raw_extremes_cross_scales(self):
        xs=[0,1,2,0x003fffff,0x007fffff,0x00800000,0x00800001,0x00ffffff,
            0x3eaaaaab,0x3f000000,0x3f7fffff,0x3f800000,0x3f800001,
            0x40000000,0x7e800000,0x7f000000,gold.MAX]
        cs=[1,2,0x007fffff,0x00800000,0x00800001,0x3f000000,0x3f7fffff,
            0x3f800000,0x3f800001,0x3f8ccccd,0x40000000,gold.MAX]
        for x in xs:
            for c in cs:
                for sign in (0,0x80000000):self.assert_row(x|sign,c)
    def test_midpoint_preimages(self):
        qs=[0,1,2,0x007ffffe,0x007fffff,0x00800000,0x00800001,
            0x01000000,0x3effffff,0x3f000000,0x3f7fffff,0x3f800000,
            0x3f800001,0x40000000,gold.MAX-1,gold.MAX]
        cs=[1,2,0x007fffff,0x00800000,0x00800001,0x3f800000,0x3f8ccccd,gold.MAX]
        for q in qs:
            for c in cs:
                for upper in (False,True):
                    if q==0 and not upper:continue
                    product=gold.midpoint(q,upper)*gold.value(c)
                    seed=gold.rounded_fraction(product)
                    if seed==gold.INF:seed=gold.MAX
                    for x in (seed-1,seed,seed+1):
                        if 0<=x<=gold.MAX:
                            for sign in (0,0x80000000):self.assert_row(x|sign,c)
    def test_deterministic_random_bits(self):
        rng=random.Random(20261007)
        for _ in range(6000):
            x=rng.randrange(gold.MAX+1)|(rng.randrange(2)<<31)
            c=rng.randrange(1,gold.MAX+1)
            self.assert_row(x,c)
    def test_invalid(self):
        for x,c in [(0x7f800000,0x3f800000),(0xff800000,1),(0x7fc00001,1),
                    (0,0),(1,0x80000000),(1,0xbf800000),(1,0x7f800000),(1,0x7fc00000)]:
            self.assertEqual(model.exact_div(x,c),(False,False,0))
            self.assertFalse(model.certifies(x,c,0))
        for q in (-1,0x80000000,gold.INF,0x7fc00000):
            self.assertFalse(model.certifies(1,0x3f800000,q))
    def test_software_scope_and_source(self):
        header=(BASE/"exact_float_div_bits.h").read_text()
        self.assertIn("for (int32_t bit = 24; bit >= 0; --bit)",header)
        self.assertIn("rawExponent > 1",header)
        self.assertIn('include "../quantizer/exact_quantizer_bits.h"',header)
        self.assertNotIn("float ",header)
        self.assertNotIn("double ",header)
        self.assertNotIn("torch",sys.modules)
if __name__=="__main__":unittest.main()
