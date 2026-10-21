"""Synthetic diagnostic/schema/source tests. No network/device/container/eval run."""
import ast
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import probe_evidence as E
import main_quiescence as Q
import diagnostic_host as D
import he_policy as H
import he_runtime_probe as Probe


def observation():
    return dict(schema='bole.actual-HE-runtime-isolation-diagnostic/v1',capsule_sha256='c'*64,
        environment=dict(ASCEND_VISIBLE_DEVICES='',HOME='/tmp'),conditions=dict(ASCEND_VISIBLE_DEVICES_empty=True,
            HOME_tmp=True,sys_class_interfaces_loopback_only=False),sys_class_net_names=['eth0','lo'],
        proc_self_net_dev='Inter-| Receive | Transmit\n lo: 0 0\n',net_namespace_link='net:[123]',
        original_runtime_guard=dict(called=True,passed=False,error='ValueError: actual no-network namespace'),
        diagnostic_only=True,evaluator_executed=False,generated_code_executed=False,task_score_produced=False,
        full_software_qualification_accepted=False,network_safety_accepted=False,NPU=False)


class Diagnostics(unittest.TestCase):
    def parse(self,v):return E.parse_probe(E.MARKER+json.dumps(v),'c'*64)
    def test_guard_failure_is_an_observation_never_network_or_full_qualification(self):
        v=self.parse(observation());self.assertIs(v['original_runtime_guard']['passed'],False)
        self.assertIs(v['network_safety_accepted'],False);self.assertIs(v['full_software_qualification_accepted'],False)
    def test_each_of_three_actual_condition_values_independently_checked(self):
        for key in('ASCEND_VISIBLE_DEVICES_empty','HOME_tmp','sys_class_interfaces_loopback_only'):
            v=observation();v['conditions'][key]=not v['conditions'][key]
            with self.assertRaises(ValueError,msg=key):self.parse(v)
    def test_extra_environment_or_qualification_claim_rejected(self):
        for key,value in(('environment',dict(ASCEND_VISIBLE_DEVICES='',HOME='/tmp',UNRELATED='forbidden-output')),
                           ('network_safety_accepted',True),('evaluator_executed',True)):
            v=observation();v[key]=value
            with self.assertRaises(ValueError):self.parse(v)
    def test_missing_duplicate_or_wrong_source_observation_rejected(self):
        text=E.MARKER+json.dumps(observation())
        with self.assertRaises(ValueError):E.parse_probe('', 'c'*64)
        with self.assertRaises(ValueError):E.parse_probe(text+'\n'+text,'c'*64)
        with self.assertRaises(ValueError):E.parse_probe(text,'d'*64)
    def test_probe_calls_only_original_runtime_never_evaluator_or_worker_run(self):
        tree=ast.parse((P/'he_runtime_probe.py').read_bytes())
        attrs=[n.func.attr for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)]
        self.assertIn('runtime',attrs);self.assertNotIn('run',attrs);self.assertNotIn('evaluate_functional_correctness',attrs)
        names=[n.func.id for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)]
        self.assertFalse({'eval','exec'}&set(names))
    def test_original_resource_helpers_and_guard_files_frozen(self):
        expected=C.obj(C.ref(P/'PREVIOUS_CPU_EXPECTED.json'));self.assertEqual(C.ref(P/'PREVIOUS_CPU_EXPECTED.json')['sha256'],C.PREVIOUS_EXPECTED_SHA)
        for name,key in(('task_contract.py','original_task_contract'),('he_policy.py','original_he_policy')):
            a=C.ref(P/name);self.assertEqual((a['bytes'],a['sha256']),(expected[key]['bytes'],expected[key]['sha256']))
        old=P.parent/'task_cpu_owner_qualification_v10'
        if old.is_dir():
            for name in('owner_namespace.py','he_owned.py'):self.assertEqual((P/name).read_bytes(),(old/name).read_bytes())
    def test_actual_CPU3_records_are_explicit_data_not_admission_flags(self):
        v=C.obj(C.ref(P/'CPU3_ACTUAL_ENTRIES.json'));self.assertEqual(len(v['entries']),2)
        self.assertIs(v['actual_runtime_success_inferred'],False)
        self.assertEqual([e['owned_ref']['bytes']for e in v['entries']],[209038,266560])
        for e in v['entries']:
            self.assertEqual(set(e),{'owned_ref','source_ref','cid','profile'});self.assertEqual(e['profile'],Q.CPU3_PROFILE)
    def test_loaded_runtime_guard_source_pin_rejects_mutated_code(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp)/'runtime_fixture.py';source='def runtime():\n    return True\n';p.write_text(source)
            scope={};exec(compile(source,str(p),'exec'),scope);f=scope['runtime']
            Probe.original_guard(f,p,'runtime')
            f.__code__=f.__code__.replace(co_consts=(None,False))
            with self.assertRaises(ValueError):Probe.original_guard(f,p,'runtime')

    def test_diagnostic_subclass_changes_only_the_actual_entry_token(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);stage=C.write(root/'stage',dict(source_root='/public/source',suite_root='/public/suite',
                input_root='/public/inputs',capsule_ref=dict(sha256='c'*64)))
            class Base:
                def __init__(self,a,start):self.out=a.output_dir;self.cid=None
            fakeH=types.SimpleNamespace(controller=lambda *args:Base)
            fakeC=types.SimpleNamespace(sha=lambda path:C.ref(path)['sha256'])
            fakeS=types.SimpleNamespace(__file__=str(P/'he_owned.py'),DOCKER='/usr/bin/docker')
            cls=D.diagnostic_class(fakeC,fakeS,fakeH,None)
            out=root/'run-bole-task-cpu-probe'/'he-runtime-diagnostic';out.mkdir(parents=True)
            actor=cls(types.SimpleNamespace(output_dir=out),0,stage,dict(synthetic=True))
            original=H.argv(actor.name,C.IMAGE,'/public/source','/public/suite','/public/inputs','c'*64,'controls')
            self.assertEqual([(a,b)for a,b in zip(original,actor.command)if a!=b],
                             [('/source/he_worker.py','/source/he_runtime_probe.py')])
            self.assertEqual(len(original),len(actor.command));self.assertIs(actor.expected['create_argv'],actor.command)

    def test_all_five_diagnostic_CLIs_default_OFF_and_help(self):
        for n in('prepare_diagnostic','prepare_registry','diagnostic_host','probe_evidence','he_runtime_probe'):
            for args in([],['--help']):
                r=subprocess.run([sys.executable,'-I','-B',str(P/(n+'.py')),*args],capture_output=True,text=True,timeout=10)
                self.assertEqual(r.returncode,0,(n,r.stderr))
                if not args:self.assertIs(json.loads(r.stdout)['enabled'],False)


if __name__=='__main__':unittest.main()
