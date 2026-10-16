import dataclasses
import os
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import torch as t
import adapter as A
import reference as R
import consume as C
from run_component import ref,write


def fixture(length=127):
    g = t.Generator().manual_seed(261016701)
    q = (t.randn((3, 6, 256), generator=g)*.1).bfloat16()
    k = (t.randn((3, 1, 256), generator=g)*.1).bfloat16()
    v = (t.randn((3, 1, 256), generator=g)*.1).bfloat16()
    kc = (t.randn((5, 128, 1, 256), generator=g)*.1).bfloat16()
    vc = (t.randn((5, 128, 1, 256), generator=g)*.1).bfloat16()
    return A.Owner('component-request', 1, 7, length, 0), q, k, v, kc, vc, (3, 1, 4)


def packed_cpu(trial):
    """Software packed-mask implementation, never labelled native FIA proof."""
    kk=trial['scratch_k'].view(-1, 256)[:trial['owner'].length+3].double()
    vv=trial['scratch_v'].view(-1, 256)[:trial['owner'].length+3].double()
    score=t.einsum('nhd,kd->nhk',trial['q'].double(),kk)*(256**-.5)
    score=score.masked_fill(trial['mask'][:,None,:],-float('inf'))
    return t.einsum('nhk,kd->nhd',score.softmax(-1),vv)


class Tests(unittest.TestCase):
    def test_paged_path_reference(self):
        for length in (0, 127, 128, 131):
            f=fixture(length);trial=A.prepare(t,*f)
            ref=R.sequential(t,f[1],f[2],f[3],f[4],f[5],f[6],length,dtype=t.double)
            self.assertTrue(t.allclose(packed_cpu(trial),ref,atol=1e-14,rtol=1e-13))
            self.assertTrue(A.bits(t,f[4],trial['anchor_k']))

    def test_sibling_isolation(self):
        f=fixture();a=A.prepare(t,*f);before=packed_cpu(a)
        a['scratch_v'].view(-1,256)[f[0].length+2].fill_(100)
        after=packed_cpu(a)
        self.assertTrue(t.equal(before[:2],after[:2]));self.assertFalse(t.equal(before[2],after[2]))
        # A wrong all-visible mask is detected by this same witness.
        a['mask'].zero_();self.assertFalse(t.allclose(packed_cpu(a)[0],before[0]))

    def test_commit_paths_cross_page_and_inactive(self):
        for child,path in ((None,[]),(-1,[0]),(1,[0,1]),(2,[0,2])):
            f=fixture();a=A.prepare(t,*f);a['status']='VERIFIED' # CPU-only state-machine fixture.
            ek=f[4].clone();ev=f[5].clone()
            for offset,node in enumerate(path):
                physical=f[6][(127+offset)//128];pos=(127+offset)%128
                ek[physical,pos]=f[2][node];ev[physical,pos]=f[3][node]
            new=A.commit(t,a,f[0],child)
            self.assertEqual(new.length,127+len(path))
            self.assertTrue(A.bits(t,ek,f[4]));self.assertTrue(A.bits(t,ev,f[5]))
            with self.assertRaises(ValueError):A.commit(t,a,f[0],child)

    def test_stale_generation_and_anchor(self):
        f=fixture();a=A.prepare(t,*f);a['status']='VERIFIED'
        with self.assertRaises(ValueError):A.commit(t,a,dataclasses.replace(f[0],generation=5),1)
        f[4][0,0,0,0]+=1
        with self.assertRaises(ValueError):A.commit(t,a,f[0],1)

    def test_layout_table_dtype_reject(self):
        for mutate in ('duplicate','short','dtype','shape'):
            f=list(fixture())
            if mutate=='duplicate':f[6]=(3,3,4)
            if mutate=='short':f[6]=(3,)
            if mutate=='dtype':f[1]=f[1].float()
            if mutate=='shape':f[1]=f[1][:2]
            with self.assertRaises(ValueError):A.prepare(t,*f)

    def test_default_off_and_unknown_accept(self):
        a=A.prepare(t,*fixture())
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'default OFF'):A.native(t,None,a,{},sparse_mode=0)
        a['status']='VERIFIED'
        for node in (0,3,True,'1'):
            with self.assertRaises(ValueError):A.commit(t,a,a['owner'],node)

    def test_reference_wrong_page_and_head_sensitive(self):
        f=fixture();good=R.sequential(t,*f[1:6],f[6],127,dtype=t.double)
        bad=R.sequential(t,*f[1:6],(1,3,4),127,dtype=t.double)
        self.assertFalse(t.allclose(good,bad))
        q=f[1].roll(1,1)
        self.assertFalse(t.allclose(good,R.sequential(t,q,*f[2:6],f[6],127,dtype=t.double)))

    def test_full_consumer_actual_fields_and_corruption(self):
        for case,(length,child) in enumerate(((0,None),(127,1),(128,-1),(131,2))):
            f=fixture(length);a=A.prepare(t,*f)
            output=packed_cpu(a).bfloat16()
            a['status']='VERIFIED';new=A.commit(t,a,f[0],child)
            raw=dict(schema='bole.paged-tree-raw/v1',primary=None,case=case,mode=0,owner=dataclasses.asdict(f[0]),
                     table=f[6],accepted_child=child,inputs=dict(q=f[1],k=f[2],v=f[3],
                         kc=a['anchor_k'],vc=a['anchor_v']),output=output,
                     scratch_k=a['scratch_k'],scratch_v=a['scratch_v'],actual_mask=a['mask'],
                     after_k=f[4],after_v=f[5],committed_owner=dataclasses.asdict(new))
            self.assertTrue(C.evaluate(t,raw)['component_pass'])
            raw['after_k']=raw['after_k'].clone();raw['after_k'][0,0,0,0]+=1
            self.assertFalse(C.evaluate(t,raw)['component_pass'])
            raw['output']=output.float()
            with self.assertRaises(ValueError):C.evaluate(t,raw)

    def test_actual_view_rebind_rejected(self):
        f=fixture();a=A.prepare(t,*f);a['status']='VERIFIED'
        f[4].set_(f[4].clone())
        with self.assertRaisesRegex(ValueError,'view rebound'):A.commit(t,a,f[0],1)

    def test_serialized_eight_row_receiver(self):
        with tempfile.TemporaryDirectory()as folder:
            root=Path(folder);source=root/'SOURCE.json';write(source,{'software_fixture':True});sr=ref(source)
            rows=[]
            for case,length in enumerate((0,127,128,131)):
                for mode in(0,1):
                    f=fixture(length);a=A.prepare(t,*f);child=(None,1,-1,2)[case]
                    inputs=dict(q=f[1],k=f[2],v=f[3],kc=a['anchor_k'],vc=a['anchor_v'])
                    raw=dict(schema='bole.paged-tree-raw/v1',source=sr,case=case,mode=mode,
                             primary=None,owner=dataclasses.asdict(f[0]),table=f[6],accepted_child=child,
                             inputs=inputs,output=None)
                    before=root/('before%d%d.pt'%(case,mode));t.save(raw,before)
                    raw['output']=packed_cpu(a).bfloat16();a['status']='VERIFIED'
                    new=A.commit(t,a,f[0],child)
                    raw.update(scratch_k=a['scratch_k'],scratch_v=a['scratch_v'],actual_mask=a['mask'],
                               after_k=f[4],after_v=f[5],committed_owner=dataclasses.asdict(new))
                    path=root/('raw%d%d.pt'%(case,mode));t.save(raw,path)
                    rows.append(dict(case=case,mode=mode,primary=None,raw=ref(path),before=ref(before)))
            stage=root/'STAGE.json';write(stage,dict(schema='bole.paged-tree-stage/v1',source=sr,
                        NPU=True,qualified=False,rows=rows)) # Serialized software fixture, not actual NPU evidence.
            report=C.run(t,sr,ref(stage),root/'CONSUMED.json')
            self.assertTrue(report['component_pass']);self.assertFalse(report['qualified'])
            import pipeline118t,common116,test_owned118t,adapter,reference,run_component,consume
            historical=root/'historical';historical.mkdir();m=test_owned118t.fixture(historical)
            m['files']={x.__name__+'.py':ref(x.__file__)for x in(adapter,reference,run_component,consume)}
            outer=dict(schema='bole.tree-stage/v118t',source=sr,primary=None,NPU=True,result=ref(stage))
            combined=pipeline118t.consume(t,common116,m,sr,outer)
            self.assertTrue(combined['pass_gate']);self.assertFalse(combined['model_ready'])

            bad=json.loads(stage.read_bytes());bad['rows']=bad['rows'][:-1]
            missing=root/'missing.json';write(missing,bad)
            with self.assertRaisesRegex(ValueError,'eight rows'):C.run(t,sr,ref(missing),root/'bad.json')


if __name__=='__main__':unittest.main()
