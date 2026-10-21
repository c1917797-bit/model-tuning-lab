"""Synthetic controlled-clock actual-main and genuine original leaf controls."""
import ast
import datetime
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import g2_cold_clock as K
import sourceio as C


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def original(name):
    review=P.parent.parent/'g1_review_v2'
    if review.is_dir():return review/name
    m=C.obj(C.ref(P/'SOURCE_BOUND.json'));return C.checked(m['files'][name])


class ClockControls(unittest.TestCase):
 def test_actual_main_first_clock_and_every_original_owner_use_same_start(self):
    self.assertTrue(K.validate((P/'host_service.py').read_text())['source_hashes_in_phase'])
 def test_late_start_joint_reset_controller_reset_and_elapsed_reset_rejected(self):
    text=(P/'host_service.py').read_text()
    bad=[text.replace('start=entry_start;','start=time.monotonic();'),text.replace('joint=H.Joint(start)','joint=H.Joint(time.monotonic())'),text.replace('output_dir=leaf),start)','output_dir=leaf),time.monotonic())'),text.replace('elapsed=time.monotonic()-start','elapsed=0'),text.replace(' entry_start=time.monotonic()\n',' pass\n entry_start=time.monotonic()\n')]
    for t in bad:
        with self.subTest(t=t[:50]),self.assertRaises(ValueError):K.validate(t)
 def execute_slow_source_main(self,delay):
    host=module(P/'host_service.py','_g2_clock_real_main');clock=NS(now=100.,wall=K.CUTOFF-10000.)
    fake=NS(monotonic=lambda:clock.now,time=lambda:clock.wall)
    touched=[]
    def source(sr):clock.now+=delay;touched.append('actual_source');return dict(service_experiment=host.G1.SCOPE,dependencies=[])
    def boundary(*args):touched.append('output_boundary');raise RuntimeError('PAST-COLD-ADMISSION')
    contract=NS(source=source,need=C.need,CUT=K.CUTOFF,output_argument=boundary)
    deps={'fault_receipt':NS(),'owned_ref131r7':NS(),'bind_model':NS(readset=lambda sr:[]),'command_contract':NS(validate=lambda *a:[])}
    with patch.object(host,'time',fake),patch.object(K,'time',fake),patch.object(host,'C',contract),patch.dict(sys.modules,deps),patch.object(sys,'argv',[str(P/'host_service.py'),'--execute','--source-ref','{}','--output','/not-created']):
        try:host.main()
        except BaseException as error:return touched,error
    raise AssertionError('controlled actual main must stop before owner creation')
 def test_actual_aggregate_slow_source_rejects_before_output_or_owner_without_reset(self):
    touched,error=self.execute_slow_source_main(3361.)
    self.assertEqual(touched,['actual_source']);self.assertIsInstance(error,ValueError);self.assertIn('cold source/readset',str(error))
 def test_actual_aggregate_pre_hash_with_sufficient_budget_crosses_same_gate(self):
    touched,error=self.execute_slow_source_main(100.)
    self.assertEqual(touched,['actual_source','output_boundary']);self.assertEqual(str(error),'PAST-COLD-ADMISSION')
 def test_cutoff_and_cleanup_create_boundaries_fail_without_phase_extension(self):
    contract=NS(CUT=K.CUTOFF,need=C.need)
    for now,wall,accepted in((100+3360,K.CUTOFF-10000,True),(100+3360.01,K.CUTOFF-10000,False),(100,K.CUTOFF-240,True),(100,K.CUTOFF-239.99,False)):
        with self.subTest(now=now,wall=wall),patch.object(K,'time',NS(monotonic=lambda:now,time=lambda:wall)):
            if accepted:self.assertGreaterEqual(K.phase_admission(contract,100),60)
            else:
                with self.assertRaises(ValueError):K.phase_admission(contract,100)
 def actual_remaining(self):
    tree=ast.parse(original('safety_host.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Controller');fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='remaining')
    scope=dict(time=NS(monotonic=lambda:100.),datetime=datetime,c=NS(require=C.need,CUT='2026-10-21T15:47:10+00:00'),utc=lambda:datetime.datetime.fromtimestamp(K.CUTOFF-10000,datetime.timezone.utc),CLEANUP=180)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(original('safety_host.py'))+'#exact-original-remaining','exec'),scope)
    return scope['remaining'],scope
 def test_actual_original_remaining_already_reserves180_once_and_allows_exact60(self):
    remaining,scope=self.actual_remaining();ctl=NS(created_monotonic=100.,deadline=100+3600,cleanup_deadline=None)
    ctl.remaining=lambda **k:remaining(ctl,**k)
    scope['time'].monotonic=lambda:100+3360
    K.controller_admission(C,NS(CUTOFF=K.CUTOFF),NS(PHASE=3600,CLEANUP=180),ctl,100.)
    self.assertEqual(ctl.remaining(cap=60),60)
    scope['time'].monotonic=lambda:100+3360.01
    with self.assertRaises(ValueError):K.controller_admission(C,NS(CUTOFF=K.CUTOFF),NS(PHASE=3600,CLEANUP=180),ctl,100.)
 def test_changed_actual_controller_clock_or_phase_cannot_create(self):
    for change in('deadline','created_monotonic','phase','cleanup','cutoff'):
        ctl=NS(created_monotonic=100.,deadline=3700.,remaining=lambda **k:60);s=NS(PHASE=3600,CLEANUP=180);c=NS(CUTOFF=K.CUTOFF)
        if change in('deadline','created_monotonic'):setattr(ctl,change,getattr(ctl,change)+1)
        elif change=='phase':s.PHASE+=1
        elif change=='cleanup':s.CLEANUP+=1
        else:c.CUTOFF+=1
        with self.subTest(change=change),self.assertRaises(ValueError):K.controller_admission(C,c,s,ctl,100.)
 def test_genuine_original_fresh_environment_prepare_accept_candidate_without_allowlist_change(self):
    ext=module(original('external025.py'),'_g2_original_external_leaf');safety=original('safety_host.py')
    with tempfile.TemporaryDirectory()as tmp,patch.dict(os.environ,{'DENSE090_EXTERNAL_OUTPUT_ENABLE':'1'}):
        root=Path(tmp);ext.OUT=root
        fake=NS(ordinary=lambda p:Path(p));controllers=type('Controller',(),{'resources':lambda *a,**k:None})
        S=NS(WORKSPACE=32*2**30,RESERVE=8*2**30,HOST_MEM=512*2**20,__file__=str(safety),Controller=controllers)
        H=NS(fresh_leaf=lambda p:None);ext.install(fake,S,H)
        leaf=H.fresh_leaf(root/'candidate');self.assertEqual(leaf,root/'candidate')
        env=ext.environment(dict(mounts={'/adakv-results':(str(leaf),True),str(leaf):(str(leaf),True)}));self.assertEqual(env['TMPDIR'],'/adakv-results')
        ext.prepare(leaf);self.assertTrue((leaf/'.runtime/home').is_dir())
        with self.assertRaises(ValueError):H.fresh_leaf(leaf)
        for name in('handoff-preflight','candidate-other','candidate/escape'):
            with self.subTest(name=name),self.assertRaises(ValueError):H.fresh_leaf(root/name)
        with self.assertRaises(ValueError):ext.environment(dict(mounts={'/adakv-results':(str(leaf),True),'escape':(str(root),True)}))
 def test_host_stages_candidate_then_original_cpu_arm_and_all_probe_paths_agree(self):
    text=(P/'host_service.py').read_text();self.assertIn("coldleaf=H.fresh_leaf(a.output/'candidate')",text);self.assertIn("cold=ctl_for('cpu-preflight',cpu=True,leaf=coldleaf)",text)
    create=(P/'owned_create.py').read_text();self.assertIn("role=='cpu-preflight'and leaf.name=='candidate'",create)
    handoff=(P/'g2_handoff.py').read_text();self.assertEqual(handoff.count("Path(m['output_root'])/'candidate'"),2);self.assertEqual(handoff.count("Path(m['output_root']+'-CPU')/'candidate'"),2)
    for body in(text,create,handoff):self.assertNotIn("'handoff-preflight'",body)


 def test_real_complete_saved_stage_and_host_verification_accept_only_candidate_root(self):
    import g2_handoff as T
    with tempfile.TemporaryDirectory()as tmp:
        root=Path(tmp);oldout=root/'old';oldout.mkdir();stream=oldout/'dense/receipts/STREAM';stream.mkdir(parents=True)
        old=C.write(root/'old-source.json',dict(output_root=str(oldout),stream_channel_root=str(stream)))
        refs={};declared={}
        for role in T.ROLES:
            folder=oldout/('cpu-consumer'if role.startswith('consumer')else'dense');folder.mkdir(exist_ok=True)
            refs[role]=C.write(folder/('OWNED.json'if role.endswith('owner_ref')else'inspect-1.json'),dict(synthetic=True,role=role))
            declared[role]={k:refs[role][k]for k in('path','sha256')}if role.endswith('inspect')else refs[role]
        channel=C.write(stream/'CHANNEL.json',dict(source=old,root=str(stream),**declared))
        output=root/'new';output.mkdir();candidate=output/'candidate';candidate.mkdir()
        source=C.write(root/'source.json',dict(default_enabled=False,output_root=str(output),files={'g2_handoff.py':C.ref(T.__file__)},g2_metadata_handoff_v8=dict(failed_source=old,failed_channel=channel,failed_four_full_refs=refs)))
        stage=T.stage_saved_probe(C,source,candidate);value=T.verify_saved_probe(C,source,stage,guest=False)
        self.assertEqual(value['actual_probe_root'],str(candidate));self.assertEqual(value['total_copy_bytes'],sum(r['bytes']for r in refs.values()));self.assertFalse(value['actual_live_identity_qualified'])
        for role,row in value['roles'].items():
            self.assertEqual(C.checked(row['copy_ref']).read_bytes(),C.checked(refs[role]).read_bytes());self.assertEqual(row['copy_host_stat'],T.host_stat(row['copy_ref']['path']))
        for name in('handoff-preflight','candidate-other'):
            wrong=output/name;wrong.mkdir()
            with self.subTest(name=name),self.assertRaises(ValueError):T.stage_saved_probe(C,source,wrong)


if __name__=='__main__':unittest.main()
