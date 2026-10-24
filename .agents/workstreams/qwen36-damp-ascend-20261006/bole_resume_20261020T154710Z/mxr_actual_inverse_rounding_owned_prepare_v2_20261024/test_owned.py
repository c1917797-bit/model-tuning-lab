"""Stdlib source/contract controls only; synthetic report is NOT Tensor evidence."""
import copy,importlib.util,json,subprocess,sys,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(n):
    s=importlib.util.spec_from_file_location('_actual_cast_'+n,HERE/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Controls(unittest.TestCase):
    def test_public_default_and_missing_review(self):
        for args,ok,needle in [([],True,'"enabled":false'),(['--execute'],False,'new exact MAIN CPU review required'),(['--plan','--review-ref','{}'],False,'unrecognized')]:
            # --plan with an extra review is handled by original parser's own no-ignored check.
            r=subprocess.run([sys.executable,'-I','-B',str(HERE/'owner.py'),*args],capture_output=True,text=True,timeout=20)
            self.assertEqual(r.returncode==0,ok)
            if len(args)<2:self.assertIn(needle,r.stdout+r.stderr)
    def test_whole_inverse_and_actual_review(self):
        M=load('owner');O=M.configured();text,pairs,original=O.derive_cpu(O.checked(O.PARENT_HOST).read_bytes());back=text
        for a,b in reversed(pairs):self.assertEqual(back.count(b),1);back=back.replace(b,a,1)
        self.assertEqual(back,original);self.assertEqual(M.execution_decision(O),'approve')
        expected=O.review_contract();self.assertEqual(expected['decision'],'PENDING_MAIN')
        self.assertEqual(len(expected['readonly_inputs']),17);self.assertEqual(expected['resources'],O.BUDGET)
        original_checked=O.checked
        try:
            for decision,accepted in [('approve',True),('APPROVED',False),('PENDING_MAIN',False)]:
                synthetic=copy.deepcopy(expected);synthetic['decision']=decision
                O.checked=lambda unused:types.SimpleNamespace(read_bytes=lambda:json.dumps(synthetic).encode())
                if accepted:self.assertEqual(O.require_review({'synthetic':True}),synthetic)
                else:
                    with self.assertRaises(ValueError):O.require_review({'synthetic':True})
        finally:O.checked=original_checked
    def test_complete_counts_and_strict_decision(self):
        A=load('analysis');plan=json.loads(Path(load('owner').PLAN['path']).read_bytes())
        total=2048*12*64;first=[0]*total;second=first.copy();second[0]=1;second[64*12*64+3*64+2]=1
        summary=A.aggregate(first,second,(1,2048,12,64));self.assertEqual(summary['mismatches'],2)
        self.assertEqual(summary['per_head'][0],1);self.assertEqual(summary['per_head'][3],1)
        residuals=[dict(sequence=0,start=n,rows=64,max_residual=0.)for n in range(0,2048,64)]
        ds={k:dict(shape=[1,2048,12,64],dtype=d,bytes=z,sha256=('1'if k=='library_B'else'0')*64)for k,d,z in [('A','torch.float32',6291456),('inverse','torch.float64',12582912),('saved_B','torch.bfloat16',3145728),('integer_RNE_B','torch.bfloat16',3145728),('library_B','torch.bfloat16',3145728)]}
        r=dict(schema=A.SCHEMA,input_plan=plan,direct_reference=A.DIRECT,diagnostic_complete=True,full_integer_RNE_B_anchor=True,same_inverse_object_for_two_casts=True,anchor_raw=plan['fixed_inputs']['arms'][2],case=plan['fixed_inputs']['case'],residuals=residuals,full_tensors=ds,**{k:False for k in A.FALSE},**summary)
        A.verify_report(r,plan)
        for mutate in [lambda x:x.update(full_integer_RNE_B_anchor=False),lambda x:x.update(qualification=True),lambda x:x.update(prefill_state_causation_proven=True),lambda x:x.update(next_action='PASS'),lambda x:x['per_head'].__setitem__(0,0),lambda x:x['residuals'][0].update(max_residual=1e-9),lambda x:x['full_tensors']['integer_RNE_B'].update(sha256='2'*64)]:
            bad=copy.deepcopy(r);mutate(bad)
            with self.assertRaises(ValueError):A.verify_report(bad,plan)
    def test_exact_original_FP64_math_namespace(self):
        # Synthetic shape/zero operations only: exercises actual function globals, NOT numerical evidence.
        A=load('analysis');plan=json.loads(Path(load('owner').PLAN['path']).read_bytes())
        O=A.load(plan['fixed_inputs']['metrics'],'_actual_original_FP64_namespace_control')
        class T:
            device=types.SimpleNamespace(type='cpu');dtype='f32';ndim=4;shape=(1,2048,12,64)
            def __getitem__(self,k):return self
            def __setitem__(self,k,v):pass
            def permute(self,*args):return self
            def double(self):return self
            def expand(self,*args):return self
            def all(self):return True
            def item(self):return 0.
            def __add__(self,x):return self
            def __sub__(self,x):return self
            def __matmul__(self,x):return self
        torch=types.SimpleNamespace(float32='f32',float64='f64',isfinite=lambda x:T(),zeros=lambda *a,**k:T(),eye=lambda *a,**k:T(),count_nonzero=lambda x:0,triu=lambda *a,**k:T(),abs=lambda x:T(),amax=lambda x:T(),linalg=types.SimpleNamespace(solve_triangular=lambda *a,**k:T()))
        actual,checks=O.fp64_reference(torch,T(),[0,2048])
        self.assertEqual(len(checks),32);self.assertTrue(all(x['max_residual']==0. for x in checks))
if __name__=='__main__':unittest.main()
