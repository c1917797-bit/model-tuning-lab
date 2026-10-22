"""Pure software serialization/page-boundary controls, NOT actual NPU evidence."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import types
import unittest
import zlib

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import long_gate_primitives as L
WS=HERE.parent
STABLE=WS/'fastpath_numeric_bridge_prepare_v1'
ORIGINAL=WS/'bole_performance_profile_prepare_20261021/successor_layer/bound-bole-v2-r1'


def ref(path):
    p=Path(path);b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def fixture_report():
    # Evaluate the ACTUAL production consumer's final return AST. Inputs below
    # are explicitly synthetic schema operands, not tensors or a fabricated run.
    s=(STABLE/'fastpath_numeric_consumer.py').read_text()
    f=next(x for x in ast.parse(s).body if isinstance(x,ast.FunctionDef)and x.name=='consume_frame')
    node=f.body[-1]
    assert isinstance(node,ast.Return)
    rows=[]
    def digest(label,shape,dtype,element):
        size=element
        for n in shape:size*=n
        return dict(dtype=dtype,shape=shape,bytes=size,
            sha256=hashlib.sha256(label.encode()).hexdigest(),finite=True)
    for i in range(64):
        for kind in(('key','value')if i%4==3 else('state','conv')):
            shape=([1,1,256]if kind in('key','value')else
                   [12,128,128]if kind=='state'else[3,2560])
            dtype='torch.float32'if kind=='state'else'torch.bfloat16'
            element=4 if kind=='state'else 2
            row=dict(layer=i,kind=kind,after=digest('%d-%s-after'%(i,kind),shape,dtype,element))
            if kind in('state','conv'):row['before']=digest('%d-%s-before'%(i,kind),shape,dtype,element)
            rows.append(row)
    metrics=[]
    for i in range(64):
        row=dict(layer=i)
        if i%4!=3:
            # Exact return keys of unchanged independent_model.difference and
            # old112 plus conv_math. Zero is a lower serialization-bound fixture.
            for k in('FP32_output','U','P','selected_state'):
                row[k]=dict(peak_abs=0.,relative_l2=0.,reference_l2=0.,passed=True)
            row['conv']=dict(output_bound_pass=True,state_bitwise=True,peak_abs=0.)
        else:row['attention']={k:dict(pointwise_pass=True,peak_abs=0.)for k in('double','float')}
        metrics.append(row)
    mods=[types.SimpleNamespace(__file__=str(ORIGINAL/n))for n in
          ('g2_numeric.py','independent_model.py','oracle112.py')]
    mods.append(types.SimpleNamespace(__file__=str(WS/'bound-reduction-ON-v6-common_20261022T210000Z/short_state_digest.py')))
    ns=dict(source=ref(STABLE/'fastpath_numeric_consumer.py'),frame=dict(rank=0,generation=1,ordinal=0),
            metrics=metrics,selected_digests=rows,C=types.SimpleNamespace(ref=ref),N=mods[0],I=mods[1],O=mods[2],D=mods[3])
    report=eval(compile(ast.Expression(node.value),'ACTUAL-consumer-return-schema-fixture','eval'),ns)
    # Sink additions are exact keys in its actual report.update call.
    report.update(actual_frame=dict(path='/synthetic/schema-only/G1-O0.pt',bytes=1,sha256='0'*64),
                  logical_tensor_bytes=1,raw_retained_during_consumption=True)
    return report


def fixture_state(report):
    # Original STATE.emit wrapper + qualification_state_probe.capture record.
    return dict(schema='bole.two-generation-short-state-digest/v1',source=report['source'],
        profile=dict(schema='bole.two-generation-short-state-digest/v1',enabled=True,input_tokens=131,
                     output_tokens=1024,generations=2,observation='OFF',formal_performance=False),
        rank=0,generation=1,ordinal=0,kind='STEP',NPU_qualified=False,formal_performance=False,
        record=dict(request='r',length=131,version=0,tokens=[0,0,0],
            actual_collect_observation_only=False,processed_nodes=[0],emitted_tokens=[0],
            rows=sorted(report['selected_write_digests'],key=lambda r:(r['layer'],r['kind']))))


def equal(a,b,why):L.need(a==b,why)


def pages(values,ids=(7,9)):
    return dict(layer=3,physical_pages=list(ids),key=list(values),value=list(values),
        ownership=dict(schema='bole.service-live-FA-owner/v1',request='r',logical_owner_slot=0,generation=1,
            cache_identities=['actual-source-ABI-fixture'],blocks_per_phys_block=1,kernel_block_size=128,
            physical_block_size=128,use_hybrid_blocks=False,pcp_world_size=1,dcp_world_size=1))


class Controls(unittest.TestCase):
    def test_frame_domain(self):
        self.assertEqual(L.frame_domain(160)['maximum_total'],318)
        self.assertEqual(L.frame_domain(1024)['maximum_total'],2046)
        self.assertEqual(L.frame_domain(160)['maximum_allocated_pages'],3)
        self.assertEqual(L.frame_domain(1024)['maximum_allocated_pages'],10)

    def test_real_return_schema_and_known_budget_failure(self):
        r=fixture_report();s=fixture_state(r)
        self.assertEqual(len(r['metrics']),64)
        self.assertEqual(len(r['selected_write_digests']),128)
        self.assertEqual(sum('before'in d for d in r['selected_write_digests']),96)
        # Just the valid minimum-value fixture already exceeds current caps.
        self.assertGreater(len(L.canonical(r))*1024,L.METADATA_CAP)
        self.assertGreater(len(L.canonical(s))*318,L.STATE_CAP)

    def test_lossless_full_report_compaction(self):
        r=fixture_report();wire,identity=L.encode_report(r)
        self.assertEqual(L.decode_report(wire,identity),r)
        self.assertEqual(len(L.decode_report(wire,identity)['selected_write_digests']),128)

    def test_modified_wire_rejected(self):
        wire,i=L.encode_report(fixture_report())
        with self.assertRaises(ValueError):L.decode_report(wire[:-1]+b'x',i)

    def test_bool_bytes_rejected(self):
        wire,i=L.encode_report(fixture_report());i['wire_bytes']=True
        with self.assertRaises(ValueError):L.decode_report(wire,i)

    def test_render_exact_inverse(self):
        import render_page_delta as R
        self.assertTrue(R.check()['exact_inverse'])

    def test_full_reference_roundtrip_wrong_frame_rejected(self):
        r=fixture_report();wire,c=L.encode_report(r)
        wr=dict(path='/synthetic/schema-only/report.zjson',bytes=len(wire),sha256=c['wire_sha256'])
        reference=L.compact_rows_reference(r,wr,c)
        expected={k:r[k]for k in('source','rank','generation','ordinal')}
        rows,full=L.resolve_rows(reference,expected,read_exact_ref=lambda rr:wire)
        self.assertEqual(rows,r['selected_write_digests']);self.assertEqual(full,r)
        with self.assertRaises(ValueError):L.resolve_rows(reference,dict(expected,ordinal=1),read_exact_ref=lambda rr:wire)

    def make_reference(self,r):
        wire,c=L.encode_report(r);wr=dict(path='/synthetic/schema-only/report.zjson',bytes=len(wire),sha256=c['wire_sha256'])
        return wire,L.compact_rows_reference(r,wr,c),{k:r[k]for k in('source','rank','generation','ordinal')}

    def test_bool_layer_rejected_even_with_new_valid_wire_hash(self):
        r=fixture_report();r['selected_write_digests'][0]['layer']=False
        wire,reference,expected=self.make_reference(r)
        with self.assertRaises(ValueError):L.resolve_rows(reference,expected,read_exact_ref=lambda rr:wire)

    def test_wire_ref_codec_mismatch_rejected(self):
        wire,reference,expected=self.make_reference(fixture_report());reference['report']['sha256']='0'*64
        with self.assertRaises(ValueError):L.resolve_rows(reference,expected,read_exact_ref=lambda rr:wire)

    def test_cannot_promote_scope_flag_by_reencoding(self):
        r=fixture_report();r['numerical_qualified']=True
        wire,reference,expected=self.make_reference(r)
        with self.assertRaises(ValueError):L.resolve_rows(reference,expected,read_exact_ref=lambda rr:wire)

    def test_extra_stream_rejected(self):
        wire,i=L.encode_report(fixture_report());wire+=zlib.compress(b'{}')
        i.update(wire_bytes=len(wire),wire_sha256=hashlib.sha256(wire).hexdigest())
        with self.assertRaises(ValueError):L.decode_report(wire,i)

    def test_bomb_rejected(self):
        wire=zlib.compress(b'x'*(L.REPORT_DECODE_CAP+1));i=dict(codec='zlib-canonical-JSON/v1',
            wire_bytes=len(wire),wire_sha256=hashlib.sha256(wire).hexdigest(),
            decoded_bytes=L.REPORT_DECODE_CAP,decoded_sha256='0'*64)
        with self.assertRaises(ValueError):L.decode_report(wire,i)

    def test_shared_metadata_ledger(self):
        r=L.reservation160()
        self.assertLessEqual(r['total_reserved_bytes'],L.METADATA_CAP)
        with self.assertRaises(ValueError):L.metadata_reservation(1024,10*2**20)

    def test_first_plus_failed_raw_charged(self):
        self.assertLess(L.raw_reservation(50*2**20,100*2**20,110*2**20,60*2**20,64*2**20),L.RAW_CAP)
        # All operands are individually legal under old subcaps, jointly unsafe.
        with self.assertRaises(ValueError):L.raw_reservation(300*2**20,300*2**20,310*2**20,128*2**20,64*2**20)

    def transition(self,before,after,**kw):
        old=dict(request='r',generation=1,length=254,version=3)
        new=dict(request='r',generation=1,length=256,version=4);new.update(kw)
        return L.page_transition(before,after,old,new,256,4,equal_page=equal)

    def test_new_page_growth(self):
        r=self.transition(pages([11,22]),pages([11,22,33],(7,9,12)))
        self.assertEqual(r['newly_owned_pages'],[12])
        self.assertFalse(r['newly_owned_page_initialization_proven'])

    def test_existing_page_corruption(self):
        with self.assertRaises(ValueError):self.transition(pages([11,22]),pages([11,99,33],(7,9,12)))

    def test_alias_rejected(self):
        with self.assertRaises(ValueError):self.transition(pages([11,22]),pages([11,22,33],(7,9,9)))

    def test_reorder_rejected(self):
        with self.assertRaises(ValueError):self.transition(pages([11,22]),pages([22,11,33],(9,7,12)))

    def test_generation_reuse_rejected(self):
        with self.assertRaises(ValueError):self.transition(pages([11,22]),pages([11,22]),generation=2)

    def test_arena_identity_rejected(self):
        p=pages([11,22]);p['ownership']['cache_identities']=['different-arena']
        with self.assertRaises(ValueError):self.transition(pages([11,22]),p)


def main():
    if sys.argv[1:]!=['--check']:raise SystemExit('default OFF: explicit --check for pure software only')
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    r=fixture_report();s=fixture_state(r);wire,identity=L.encode_report(r)
    print(json.dumps(dict(schema='bole.long-gate-software-only/v1',tests=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),synthetic_schema_operands=True,
        actual_return_AST_source=ref(STABLE/'fastpath_numeric_consumer.py'),
        full_report_fixture_bytes=len(L.canonical(r)),state_fixture_bytes=len(L.canonical(s)),
        compressed_full_report_fixture_bytes=len(wire),
        fixed160=L.reservation160(),fixed1024='pending: original ALL4-rank STATE cap and complete raw ledger',
        numerical_qualified=False,NPU_executed=False,execution_ready=False),sort_keys=True))
    raise SystemExit(not result.wasSuccessful())


if __name__=='__main__':main()
