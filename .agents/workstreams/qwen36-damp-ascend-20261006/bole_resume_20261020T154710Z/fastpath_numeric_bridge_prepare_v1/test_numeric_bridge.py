"""Source/negative controls only. Does not simulate actual NPU numerical qualification."""
import ast
import hashlib
import importlib.util
from pathlib import Path
import os
import sys
import types
import unittest
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import fastpath_numeric_observer as O
import fastpath_numeric_consumer as N
import qualification_tap_delta as Q
BASE=HERE.parent/'performance_followup_prepare_20261022T203100Z'
sys.path.insert(0,str(BASE))
import performance_followup_delta as D


class Huge:
    called=False
    def numel(self):return 384*2**20
    def element_size(self):return 4
    def detach(self):self.called=True;raise AssertionError('budget checked too late')


class Tests(unittest.TestCase):
    def test_selected_conv_rejects_self_consistent_wrong_legal_tail(self):
        class Exact:
            @staticmethod
            def equal(t,a,b,s):
                if a!=b:raise ValueError(s)
        tails=[('root-history',),('left-history',),('right-history',)]
        for terminal in range(3):
            N.selected_conv_write(None,Exact,{'after':tails[terminal]},
                                  {'actual_conv_tail':tails},terminal)
            for other in set(range(3))-{terminal}:
                # Even if proposal/observed arena/next before all agree on
                # this wrong but mathematically valid node's tail, reject it.
                with self.assertRaisesRegex(ValueError,'accepted terminal'):
                    N.selected_conv_write(None,Exact,{'after':tails[other]},
                                          {'actual_conv_tail':tails},terminal)

    def test_CPU_digest_exact_inverse_no_spoofed_NPU(self):
        source=(HERE.parent/'bound-reduction-ON-v6-common_20261022T210000Z'/'short_state_digest.py').read_text()
        node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name=='tensor_digest')
        original=ast.get_source_segment(source,node);derived=N.cpu_digest_source(original)
        self.assertEqual(derived.replace("value.device.type == 'cpu'","value.device.type == 'npu'"),original)
        self.assertIn('hashlib.sha256(raw).hexdigest()',derived)
        self.assertIn('bool(t.isfinite(value).all())',derived)
        with self.assertRaises(ValueError):N.cpu_digest_source(original.replace("'npu'","'cuda'"))

    def test_budget_before_export_and_durable_report_before_release(self):
        s=(HERE/'fastpath_numeric_sink.py').read_text()
        self.assertLess(s.index('logical=logical_bytes(t,frame)'),s.index('raw=X.export'))
        self.assertLess(s.index('<=2**30'),s.index('raw=X.export'))
        self.assertLess(s.index('report_ref=metadata('),s.index('path.unlink()'))
        self.assertIn('os.fsync(fd)',s)
        self.assertIn('outside_table_FA_arena_pending=True',(HERE/'fastpath_numeric_consumer.py').read_text())

    def test_actual_renderer_compiles_only_readonly_taps(self):
        old=D.render(D.original_sources())
        changed=Q.render(old)
        self.assertEqual(set(changed),set(old))
        self.assertEqual({n for n in old if old[n]!=changed[n]},
                         {'model_entry.py','service_bridge.py','service_runner.py'})
        for n,s in changed.items():compile(s,n,'exec')
        for s in('value,factors=self.K.verify(t,qh,kh,vh,bh,gamma,state,ancestor,1)',
                  "after=self.K.commit(t,row['state'],row['keys'],row['factors'],inclusive,terminal)[0].transpose(-1,-2).contiguous()"):
            self.assertIn(s,changed['model_entry.py'])
        self.assertEqual(changed['transaction.py'],old['transaction.py'])
        self.assertEqual(changed['tp_consensus.py'],old['tp_consensus.py'])
        self.assertIn('qualifier.publication(state.bridge,proposal,publication)',changed['service_runner.py'])

    def test_default_OFF_and_budget_before_clone(self):
        prior=os.environ.pop(O.FLAG,None)
        try:self.assertIsNone(O.install(None,None,None,{},0,snapshot=None,sink=None))
        finally:
            if prior is not None:os.environ[O.FLAG]=prior
        obj=O.Observer.__new__(O.Observer);obj.t=types.SimpleNamespace(Tensor=Huge);obj.used=0
        huge=Huge()
        with self.assertRaisesRegex(ValueError,'before allocation'):obj._capture({'huge':huge})
        self.assertFalse(huge.called)
        with self.assertRaisesRegex(ValueError,'requires explicit'):
            O.install(None,None,None,{'fastpath_numeric_qualification':{}},0,snapshot=None,sink=None)

    def test_attention_derivation_keeps_original_formula_and_bounds(self):
        original=(D.PARENT.parent/'independent_model.py').read_text()
        node=next(n for n in ast.parse(original).body if isinstance(n,ast.FunctionDef)and n.name=='attention')
        body=ast.get_source_segment(original,node);derived=N.generalized_attention(body)
        restored=derived.replace('def attention(t,row,anchor,length):','def attention(t,row,anchor):')
        restored=restored.replace("need(len(table)>=(length+2+127)//128 and len(set(table))==len(table),'actual owned physical prefix pages')",
              "need(len(table)==2 and len(set(table))==2,'actual131token physical prefix pages')")
        restored=restored.replace('for p in range(length)','for p in range(131)')
        self.assertEqual(restored,body)
        self.assertIn('.001+.01*ref.double().abs()',derived)
        with self.assertRaises(ValueError):N.generalized_attention(body.replace('def attention(','def unknown('))

    def test_sink_is_bounded_short_and_report_precedes_owned_release(self):
        text=(HERE/'fastpath_numeric_sink.py').read_text()
        compile(text,'sink','exec')
        self.assertIn("['output_tokens']==8",text)
        self.assertIn('weights_only=True',text)
        self.assertIn('2*logical+128*2**20+64*2**20<=2**30',text)
        self.assertLess(text.index("report_ref=metadata"),text.index('path.unlink()'))
        self.assertLess(text.index("C.checked(report_ref);C.checked(ref)"),text.index('path.unlink()'))
        self.assertIn("path.parent==c['root']and path.name==stem+'.pt'",text)
        self.assertIn("TP_raw_collective_receipts_pending=True",(HERE/'fastpath_numeric_consumer.py').read_text())
        self.assertIn('numerical_qualified=False', (HERE/'qualification_smoke_join.py').read_text())


if __name__=='__main__':unittest.main()
