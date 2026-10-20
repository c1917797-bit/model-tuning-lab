"""Synthetic MAIN lifecycle checks only; no actual systemctl/Docker/device calls."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import main_quiescence as Q
import cpu_host as O


class Quiescence(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.auth=C.write(self.root/'authority',dict(start_epoch=0,cutoff_epoch=9999999999))
        self.controller=C.write(self.root/'controller',dict(synthetic=True))
        self.source=C.write(self.root/'source',dict(synthetic_source=True))
        self.cid='c'*64
        self.owner='synthetic-original-owner'
        self.creation_argv=['/usr/bin/docker','create','--name','synthetic-MAIN-owned']
        labels={'owner':self.owner,'run':'synthetic-MAIN-owned','arm':'candidate','source-manifest-sha256':self.source['sha256'],'controller-sha256':'a'*64}
        for k,v in labels.items():self.creation_argv.extend(['--label','model-tuning-lab.'+k+'='+v])
        self.creation_argv.extend([C.IMAGE,'-c','exec /bin/sleep infinity'])
        self.creation=C.write(self.root/'create',dict(exit_code=0,stdout=self.cid+'\n',requested_argv=self.creation_argv))
        self.e=dict(cid=self.cid,image=C.IMAGE,name='synthetic-MAIN-owned',arm='candidate',guest_cpus=[145,146,147,148],
                    source=self.source,host_sha256='a'*64,create_receipt=self.creation)
        self.owned=C.write(self.root/'OWNED',self.e)
        self.unit='bole-main-synthetic.service'
        self.value=dict(schema=Q.SCHEMA,authority_ref=self.auth,declared_complete_MAIN_NPU_inventory=True,
             units=[dict(unit=self.unit,controller_ref=self.controller)],owned_refs=[self.owned],
             serial_schedule=dict(no_MAIN_NPU_start_during_CPU_owner=True,external_lock_path=str(self.root/'MAIN_ADMISSION.lock'),
                external_lock_argv_prefix=['/usr/bin/flock','--nonblock','--no-fork',str(self.root/'MAIN_ADMISSION.lock')],
                lock_lifetime='entire-owner',lock_verification_owner='MAIN-submitter'))
        self.policy=C.write(self.root/'POLICY',self.value)
        self.unit_fields=dict(Id=self.unit,LoadState='loaded',ActiveState='inactive',SubState='dead',MainPID='0',ControlPID='0',
                              Job='',ControlGroup='',ExecStart='synthetic retained old unit command',FragmentPath='',RemainAfterExit='yes',TasksCurrent='0')
        labels={'model-tuning-lab.owner':self.owner,'model-tuning-lab.run':self.e['name'],'model-tuning-lab.arm':self.e['arm'],
          'model-tuning-lab.source-manifest-sha256':self.source['sha256'],'model-tuning-lab.controller-sha256':'a'*64}
        self.inspect=dict(Id=self.cid,Name='/'+self.e['name'],Image=C.IMAGE,Config=dict(Image=C.IMAGE,Labels=labels),
                          HostConfig=dict(RestartPolicy=dict(Name='no',MaximumRetryCount=0)),
                          State=dict(Running=False,Pid=0,Restarting=False),ExecIDs=None)

    def tearDown(self):self.tmp.cleanup()

    def text(self):return '\n'.join(k+'='+v for k,v in self.unit_fields.items())+'\n'

    def ctl(self,foreign):
        obs=C.write(self.root/'observation',dict(declared_only_containers=foreign,actual_compute=[],actual_device_fd_holders=[]))
        calls=[]
        def call(label,argv,**kw):
            calls.append(argv)
            stdout=self.text()if argv[0]==Q.SYSTEMCTL else json.dumps([self.inspect])
            raw=dict(stdout=stdout,exit_code=0,requested_argv=argv)
            return raw,C.write(self.root/('call-'+str(len(calls))),raw)
        ctl=types.SimpleNamespace(out=self.root,call=call,_main_quiescence_ref=self.policy,observe=lambda *a,**kw:obs)
        return ctl,obs,calls

    def test_foreign_static_declarations_preserved_not_actual_overlap(self):
        foreign=[dict(cid='f'*64,devices=['/dev/davinci0','/dev/davinci_manager']),dict(cid='e'*64,devices=['/dev/davinci4'])]
        ctl,obs,calls=self.ctl(foreign);r=O.observe_cpu(ctl,'synthetic',initial=True);v=C.obj(r)
        self.assertEqual(v['foreign_static_device_declarations'],foreign)
        self.assertEqual(v['original025_observation_ref'],obs)
        self.assertIs(v['known_MAIN_lifecycles_quiescent'],True)
        self.assertIs(v['external_lock_verified_by_this_reader'],False)
        self.assertEqual(len(calls),2)
        self.assertEqual(calls[1],[Q.DOCKER,'inspect',self.cid])
        self.assertTrue(all(a[1]not in{'stop','kill','rm','restart','start'}for a in calls))

    def test_active_MAIN_unit_is_rejected(self):
        ctl,_,_=self.ctl([]);self.unit_fields.update(ActiveState='active',SubState='running',MainPID='123')
        with self.assertRaisesRegex(ValueError,'exited/inactive'):O.observe_cpu(ctl,'synthetic')

    def test_control_or_pending_job_is_rejected(self):
        for key,value in(('ControlPID','8'),('Job','182')):
            fields=dict(self.unit_fields);fields[key]=value
            with self.assertRaises(ValueError):Q.unit_state('\n'.join(k+'='+v for k,v in fields.items()),self.unit)

    def test_collected_or_failed_unit_with_zero_pids_is_quiescent(self):
        self.unit_fields.update(LoadState='not-found')
        self.assertEqual(Q.unit_state(self.text(),self.unit)['LoadState'],'not-found')
        self.unit_fields.update(LoadState='loaded',ActiveState='failed',SubState='failed')
        Q.unit_state(self.text(),self.unit)

    def test_RemainAfterExit_active_exited_zero_tasks_is_quiescent(self):
        self.unit_fields.update(ActiveState='active',SubState='exited')
        Q.unit_state(self.text(),self.unit)
        self.unit_fields['TasksCurrent']='4'
        with self.assertRaises(ValueError):Q.unit_state(self.text(),self.unit)
        self.unit_fields.update(TasksCurrent='[not set]',ControlGroup='')
        Q.unit_state(self.text(),self.unit)
        self.unit_fields['ControlGroup']='/system.slice/synthetic.service'
        with self.assertRaises(ValueError):Q.unit_state(self.text(),self.unit)

    def test_running_MAIN_owned_container_is_rejected(self):
        ctl,_,_=self.ctl([]);self.inspect['State'].update(Running=True,Pid=999)
        with self.assertRaisesRegex(ValueError,'stopped'):O.observe_cpu(ctl,'synthetic')

    def test_exec_or_restart_lifecycle_rejected(self):
        self.inspect['ExecIDs']=['actual-unfinished-exec']
        with self.assertRaises(ValueError):Q.stopped_owned([self.inspect],self.e)
        self.inspect['ExecIDs']=None;self.inspect['HostConfig']['RestartPolicy']['Name']='always'
        with self.assertRaises(ValueError):Q.stopped_owned([self.inspect],self.e)

    def test_foreign_or_wrong_source_never_accepted_as_MAIN(self):
        for mutate in('cid','name','image','source','controller','owner'):
            x=copy.deepcopy(self.inspect)
            if mutate=='cid':x['Id']='f'*64
            elif mutate=='name':x['Name']='/foreign'
            elif mutate=='image':x['Image']='sha256:'+'f'*64
            else:
                suffix={'source':'source-manifest-sha256','controller':'controller-sha256','owner':'owner'}[mutate]
                x['Config']['Labels']['model-tuning-lab.'+suffix]='foreign'
            with self.assertRaises(ValueError,msg=mutate):Q.stopped_owned([x],self.e)

    def test_owner_label_is_from_immutable_original_create_not_inspect(self):
        self.assertEqual(Q.create_owner(self.e),self.owner)
        x=copy.deepcopy(self.inspect);x['Config']['Labels']['model-tuning-lab.owner']='different-observed-owner'
        with self.assertRaises(ValueError):Q.stopped_owned([x],self.e)

    def test_duplicate_owner_or_wrong_create_identity_rejected(self):
        cases=[self.creation_argv+['--label','model-tuning-lab.owner=duplicate'],
               [x if x!='model-tuning-lab.source-manifest-sha256='+self.source['sha256']else'model-tuning-lab.source-manifest-sha256='+'d'*64 for x in self.creation_argv],
               [x if x!='--name'else'--wrong-name-flag'for x in self.creation_argv]]
        for n,argv in enumerate(cases):
            e=dict(self.e,create_receipt=C.write(self.root/('bad-create-'+str(n)),dict(exit_code=0,stdout=self.cid+'\n',requested_argv=argv)))
            with self.assertRaises(ValueError):Q.create_owner(e)

    def test_duplicate_or_wildcard_unit_rejected(self):
        for units in([self.value['units'][0]]*2,[dict(unit='bole-main-*.service',controller_ref=self.controller)]):
            v=copy.deepcopy(self.value);v['units']=units;r=C.write(self.root/('bad-'+str(len(units))),v)
            with self.assertRaises(ValueError):Q.policy(r)

    def test_exact_historical_bole_unit_name_allowed_without_main_prefix(self):
        v=copy.deepcopy(self.value);v['units'][0]['unit']='bole-native-ar-20261020t154710z-v3.service'
        r=C.write(self.root/'historical-name',v)
        self.assertEqual(Q.policy(r)['units'][0]['unit'],v['units'][0]['unit'])

    def test_same_authority_and_explicit_serial_lock_required(self):
        with self.assertRaises(ValueError):Q.policy(self.policy,authority_ref=self.source)
        v=copy.deepcopy(self.value);v['serial_schedule']['no_MAIN_NPU_start_during_CPU_owner']=False
        r=C.write(self.root/'bad-serial',v)
        with self.assertRaises(ValueError):Q.policy(r)

    def test_policy_source_and_creation_refs_reopened(self):
        refs=Q.readset(self.policy,authority_ref=self.auth)
        self.assertEqual({r['path']for r in refs},{r['path']for r in(self.policy,self.auth,self.controller,self.owned,self.source,self.creation)})
        Path(self.creation['path']).write_text('changed')
        with self.assertRaises(ValueError):Q.policy(self.policy)


if __name__=='__main__':unittest.main()
