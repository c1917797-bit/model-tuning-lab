"""Double-precision CPU equation checks; NOT the FP32 NPU gate."""
import math
import random
import unittest

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def mv(m,x):return [dot(row,x) for row in m]
def fold(xs):
    out=list(xs)
    while len(out)>1:
        n=len(out)//2
        out=[out[i]+out[i+n] for i in range(n)]
    return out[0]
def materialize(base,ks,us,lams,c):
    return [[math.exp(c)*x+fold([math.exp(c-lams[l])*us[l][v]*ks[l][k]
                                 if l<len(ks) else 0 for l in range(16)])
             for k,x in enumerate(row)] for v,row in enumerate(base)]

class EquationTests(unittest.TestCase):
    def test_deferred_parallel_contract_64_steps(self):
        rng=random.Random(519);dim=8
        base=[[rng.uniform(-.01,.01) for _ in range(dim)] for _ in range(dim)]
        dense=[row[:] for row in base];ks=[];us=[];lams=[];c=0.
        for step in range(64):
            k=[rng.uniform(-.2,.2) for _ in range(dim)]
            q=[rng.uniform(-.2,.2) for _ in range(dim)]
            v=[rng.uniform(-.2,.2) for _ in range(dim)]
            g=-rng.uniform(.002,.18);beta=rng.uniform(.1,.9)
            logical=materialize(base,ks,us,lams,c)
            e=math.exp(g)
            uk=[beta*(vv-e*rr) for vv,rr in zip(v,mv(logical,k))]
            output=[e*rr+u*dot(k,q) for rr,u in zip(mv(logical,q),uk)]
            old=[row[:] for row in base]
            ks.append(k);us.append(uk);c+=g;lams.append(c)
            if len(ks)==16:
                base=materialize(base,ks,us,lams,c);ks=[];us=[];lams=[];c=0.
            else:self.assertEqual(base,old)
            dpre=mv(dense,k)
            ud=[beta*(vv-e*rr) for vv,rr in zip(v,dpre)]
            dense=[[e*x+ud[r]*k[col] for col,x in enumerate(row)] for r,row in enumerate(dense)]
            actual=materialize(base,ks,us,lams,c)
            self.assertLess(max(abs(a-b) for ar,dr in zip(actual,dense) for a,b in zip(ar,dr)),2e-15)
            self.assertLess(max(abs(a-b) for a,b in zip(output,mv(dense,q))),2e-15)
    def test_fixed_four_level_tree(self):
        self.assertEqual(fold(list(range(16))),120)
        self.assertEqual(fold([0]*15+[1]),1)

if __name__=="__main__":unittest.main()
