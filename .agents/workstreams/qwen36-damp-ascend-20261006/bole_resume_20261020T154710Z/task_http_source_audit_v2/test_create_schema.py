"""Typed actual-create data controls. Never execute docker or a HE snippet."""
import copy
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import audit_common as A
import source_audit as S

IMAGE='sha256:'+'6'*64
CID='a'*64


class CreateSchema(unittest.TestCase):
    def fixture(self):
        argv=['/usr/bin/docker','create','--name','bole-he-example','--network','none',IMAGE,'-i','HOME=/tmp','python3','-I','-B','/source/he_worker.py','--controls','--capsule-sha256','b'*64]
        owned=dict(name='bole-he-example',cid=CID,image=IMAGE,guest_cpus=[145],arm='cpu-preflight',create_argv=argv.copy(),source={'actual':'bound-source'})
        created=dict(requested_argv=argv.copy(),exit_code=0,stdout=CID+'\n',stderr='',observed_utc='synthetic-software-control',argv=['/usr/bin/prlimit','--as=unlimited','--',*argv])
        return owned,created

    def test_create_real_string_list(self):
        owned,created=self.fixture()
        self.assertEqual(S.creation_argv(owned,created,IMAGE),created['requested_argv'])

    def test_argv_ref_tuple_scalar_nonstring_rejected(self):
        for value in ({'path':'/not/argv','sha256':'a'*64},('docker','create'),'docker create',None,[],['/usr/bin/docker',True,'name']):
            owned,created=self.fixture();created['requested_argv']=value
            with self.assertRaises(ValueError):S.creation_argv(owned,created,IMAGE)

    def test_duplicate_name_and_image_rejected(self):
        for tail in (['--name','another'],[IMAGE]):
            owned,created=self.fixture();created['requested_argv']+=tail
            with self.assertRaises(ValueError):S.creation_argv(owned,created,IMAGE)

    def test_failed_or_foreign_CID_rejected(self):
        for fields in (dict(exit_code=1),dict(exit_code=False),dict(stdout='b'*64+'\n')):
            owned,created=self.fixture();created.update(fields)
            with self.assertRaises(ValueError):S.creation_argv(owned,created,IMAGE)

    def test_changed_actual_wrapper_rejected(self):
        owned,created=self.fixture();created['argv']=created['requested_argv']
        with self.assertRaises(ValueError):S.creation_argv(owned,created,IMAGE)

    def test_mutated_name_and_CPU_rejected(self):
        for fields in (dict(name='other'),dict(guest_cpus=[0])):
            owned,created=self.fixture();owned.update(fields)
            with self.assertRaises(ValueError):S.creation_argv(owned,created,IMAGE)

    def HE_fixture(self):
        owned,created=self.fixture();argv=created['requested_argv']
        he=dict(schema='bole.actual-HE-sandbox-owner-evidence/v2',container_id=CID,name=owned['name'])
        stage=dict(source_ref=owned['source'],source_root='/public/source',suite_root='/public/suite',input_root='/public/inputs',capsule_ref={'sha256':'b'*64})
        binding=dict(container_id=CID,argv=argv[argv.index('python3'):],uid=65534,Devices=[])
        calls=[]
        policy=SimpleNamespace(argv=lambda *args:argv.copy(),inspect_actual=lambda *args,**kwargs:calls.append((args,kwargs)))
        return owned,created,he,argv.copy(),policy,stage,[{}],binding,(CID+'\n').encode(),IMAGE,calls

    def test_HE_list_file_receipt_policy_and_binding_join(self):
        args=self.HE_fixture();result=S.verify_HE_create(*args[:-1])
        self.assertTrue(result['actual_create_argv_list_verified']);self.assertEqual(len(args[-1]),1)

    def test_HE_owned_nonlist_is_not_treated_as_Ref(self):
        args=list(self.HE_fixture());args[0]['create_argv']={'path':'/fake','sha256':'0'*64}
        with self.assertRaises(ValueError):S.verify_HE_create(*args[:-1])

    def test_HE_actual_file_list_mismatch_rejected(self):
        args=list(self.HE_fixture());args[3]=args[3].copy();args[3][args[3].index('--network')+1]='host'
        with self.assertRaises(ValueError):S.verify_HE_create(*args[:-1])

    def test_HE_wrong_binding_or_stdout_rejected(self):
        for change in ('argv','uid','Devices','stdout'):
            args=list(self.HE_fixture())
            if change=='argv':args[7]['argv']=['different']
            elif change=='uid':args[7]['uid']=0
            elif change=='Devices':args[7]['Devices']=['NPU']
            else:args[8]=('b'*64+'\n').encode()
            with self.assertRaises(ValueError):S.verify_HE_create(*args[:-1])


if __name__=='__main__':unittest.main()
