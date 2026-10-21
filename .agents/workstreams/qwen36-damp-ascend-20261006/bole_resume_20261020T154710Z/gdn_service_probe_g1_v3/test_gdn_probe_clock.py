"""Source/callee timing controls only; no owner, lock or resource admission."""
import ast
import copy
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

P=Path(__file__).resolve().parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
B=module('_gdn_v3_pure_builder',P/'prepare_gdn_probe.py')
K=module('_gdn_v3_pure_clock',P/'gdn_probe_clock.py')
C=types.SimpleNamespace(need=B.need,CUT=K.CUTOFF)


def donor():
    W=P.parents[1]
    if(W/'g1_review_v2/qualification/SOURCE_BOUND.json').is_file():
        on=json.loads((W/'g1_review_v2/qualification/SOURCE_BOUND.json').read_bytes())
        paths={n:W/'bole_service_proposals/g1_multi_request'/n for n in('service_bridge.py','server090.py')}
        paths.update({'contract090.py':W/'g1_review_v2/contract090.py','host_service.py':W/'bole_service_proposals/g1_repair_v2/host_service.py',
            'command_contract.py':W/'bole_service_proposals/g1_repair_v2/command_contract.py'})
        on=copy.deepcopy(on)
        for n,p in paths.items():
            r=B.ref(p)
            if(r['bytes'],r['sha256'])!=(on['files'][n]['bytes'],on['files'][n]['sha256']):raise ValueError('whole actual G1 source copy')
            on['files'][n]=r
        return on
    m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())
    return B.obj(B.obj(m['gdn_service_extension']['source'])['prior_G1']['source'])


class Tests(unittest.TestCase):
    def test_actual_host_first_clock_shared_Joint_controller_and_elapsed_source(self):
        changed=B.overlays(donor(),Path('/opt/host/vnf/austinov/run-bole-gdn-g1-probe-CLOCK'))
        proof=K.validate(changed['host_service.py']);self.assertTrue(proof['one_main_entry_clock'])
        text=changed['host_service.py']
        self.assertLess(text.index('main_lock=held_main_lock(C)'),text.index('m=C.source(sr)'))
        self.assertLess(text.index('GP.host_readset'),text.index('phase_admission(C,entry_start)'))
        self.assertLess(text.index('phase_admission(C,entry_start)'),text.index('resource.setrlimit'))
        self.assertIn('MAIN_lock=main_lock,entry_clock_before_source_replay=True,deadline_renewed=False',text)
    def test_late_clock_or_controller_reset_or_early_profile_callee_is_rejected(self):
        text=B.overlays(donor(),Path('/opt/host/vnf/austinov/run-bole-gdn-g1-probe-CLOCK'))['host_service.py']
        for bad in(text.replace(' entry_start=time.monotonic()\n',''),text.replace('start=entry_start;','start=time.monotonic();'),
            text.replace('controller_admission(C,c,S,ctl,entry_start);',''),
            text.replace("ctl.observe(role+'-admission',initial=True);controller_admission(C,c,S,ctl,entry_start);",
                "controller_admission(C,c,S,ctl,entry_start);ctl.observe(role+'-admission',initial=True);")):
            with self.assertRaises((ValueError,StopIteration)):K.validate(bad)
    def test_phase_clock_budget_includes_prehash_and_cleanup_without_double_reserve(self):
        with patch.object(K,'time',types.SimpleNamespace(monotonic=lambda:1000,time=lambda:K.CUTOFF-10000)):
            self.assertEqual(K.phase_admission(C,900),3320)
            self.assertEqual(K.phase_admission(C,-2360),60)
            for start in(-2360.01,1000.01):
                with self.assertRaises(ValueError):K.phase_admission(C,start)
        with patch.object(K,'time',types.SimpleNamespace(monotonic=lambda:1000,time=lambda:K.CUTOFF-239.99)):
            with self.assertRaises(ValueError):K.phase_admission(C,900)
    def test_original025_real_init_and_remaining_callee_same_clock(self):
        W=P.parents[1];local=W/'g1_review_v2/safety_host.py'
        if local.is_file():text=local.read_text()
        else:
            on=donor();substrate=B.load('_gdn_clock_exact025_source_refs',B.checked(on['files']['owned_substrate.py']))
            text=B.checked(substrate.REFS['safety_host']).read_text()
        self.assertEqual((len(text.encode()),hashlib.sha256(text.encode()).hexdigest()),
            (22338,'20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30'))
        tree=ast.parse(text);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Controller')
        # Genuine complete __init__/remaining methods; only base constructor and
        # clocks are isolated offline seams. No controller observe/create runs.
        cls.body=[n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name in('__init__','remaining')]
        class Base:
            def __init__(self,a):self.out=a.output_dir;self.cpu=None;self.cleanup_deadline=None
        now=1000;utc=datetime.datetime.fromtimestamp(K.CUTOFF-10000,datetime.timezone.utc)
        namespace=dict(H=types.SimpleNamespace(Controller=Base),PHASE=3600,CLEANUP=180,
            c=types.SimpleNamespace(CUT=datetime.datetime.fromtimestamp(K.CUTOFF,datetime.timezone.utc).isoformat(),require=B.need),
            time=types.SimpleNamespace(monotonic=lambda:now),datetime=datetime,utc=lambda:utc)
        exec(compile(ast.Module(body=[cls],type_ignores=[]),'<exact-original025-init-remaining>','exec'),namespace)
        ctl=namespace['Controller'](types.SimpleNamespace(output_dir=Path('/offline/cpu-preflight')),900)
        self.assertIsNone(ctl.cpu);self.assertEqual(ctl.remaining(cap=60),60)
        K.controller_admission(C,types.SimpleNamespace(CUTOFF=K.CUTOFF),types.SimpleNamespace(PHASE=3600,CLEANUP=180),ctl,900)
        ctl.deadline+=1
        with self.assertRaises(ValueError):K.controller_admission(C,types.SimpleNamespace(CUTOFF=K.CUTOFF),types.SimpleNamespace(PHASE=3600,CLEANUP=180),ctl,900)
    def test_exact_inherited_MAIN_observer_function_AST_from_successful_AR_source(self):
        W=P.parents[1];p=W/'bole_service_proposals/native_ar_saved_requalification_repair_v4/saved_common.py'
        new=next(n for n in ast.parse((P/'gdn_probe_clock.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='held_main_lock')
        if p.is_file():
            text=p.read_text();old=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)and n.name=='held_main_lock')
            self.assertEqual(ast.dump(old),ast.dump(new))
        # Independent pinned canonical AST of the original successful observer;
        # does not compare a copied function against itself in the target image.
        self.assertEqual(hashlib.sha256(ast.dump(new).encode()).hexdigest(),'980ebf51bd88757a4545bedee2ef99347e68cfdbff529ca1e2baae8b73ca680a')
        calls=[ast.unparse(n.func)for n in ast.walk(new)if isinstance(n,ast.Call)]
        self.assertNotIn('open',calls);self.assertNotIn('os.open',calls);self.assertNotIn('flock',calls)
    def test_commands_wrap_both_execute_arms_with_exact_MAIN_and_bind_stays_unlocked(self):
        changed=B.overlays(donor(),Path('/opt/host/vnf/austinov/run-bole-gdn-g1-probe-CLOCK'))
        expected=next(n for n in ast.parse(changed['command_contract.py']).body if isinstance(n,ast.FunctionDef)and n.name=='expected')
        scope=dict(Path=Path,json=json);exec(compile(ast.Module(body=[expected],type_ignores=[]),'<actual-command-contract>','exec'),scope)
        commands=scope['expected']('/new','/out',{'source':1},{'template':1},{})
        for key in('CPU','model'):
            self.assertEqual(commands[key][:5],['/usr/bin/flock','--nonblock','--no-fork',K.LOCK,'/usr/bin/env'])
            self.assertIn('BOLE_GDN_PROBE_MAIN_ENABLE=1',commands[key])
        self.assertEqual(commands['bind'][0],'/usr/bin/python3')
    def test_new_clock_and_builder_cold_imports_without_tensor_runtimes(self):
        code='''import builtins,importlib.util,sys
old=builtins.__import__
def guarded(name,*a,**k):
 if name.split('.')[0]in('torch','torch_npu','triton'):raise RuntimeError('cold import')
 return old(name,*a,**k)
builtins.__import__=guarded
for i,p in enumerate(sys.argv[1:]):
 s=importlib.util.spec_from_file_location('_cold_'+str(i),p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
'''
        r=subprocess.run([sys.executable,'-I','-B','-c',code,str(P/'gdn_probe_clock.py'),str(P/'prepare_gdn_probe.py')],capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr)
    def test_new_clock_overlay_inverse_to_exact_original_G1_and_frozen_v2_unchanged(self):
        parent=donor();out=Path('/opt/host/vnf/austinov/run-bole-gdn-g1-probe-CLOCK');changed=B.overlays(parent,out)
        # Whole exact postimages are inverse operands in the existing V6/R14
        # ledger generator; all non-five changed donor files remain byteexact.
        self.assertEqual(set(changed),{'host_service.py','service_bridge.py','server090.py','command_contract.py','contract090.py'})
        proof=json.loads((P/'CLOCK_INVERSE_AUTHORITY.json').read_bytes());inverse=dict(changed)
        replacements=[(' entry_start=time.monotonic()\n',''),
            (' from gdn_probe_clock import held_main_lock,phase_admission,controller_admission\n main_lock=held_main_lock(C)if a.execute else None\n',''),
            (' phase_admission(C,entry_start)\n',''),('start=entry_start;','start=time.monotonic();'),
            ('controller_admission(C,c,S,ctl,entry_start);',''),
            ('MAIN_lock=main_lock,entry_clock_before_source_replay=True,deadline_renewed=False,','')]
        for a,b in replacements:
            self.assertEqual(inverse['host_service.py'].count(a),1);inverse['host_service.py']=inverse['host_service.py'].replace(a,b)
        outer="'/usr/bin/flock','--nonblock','--no-fork','"+K.LOCK+"',"
        self.assertEqual(inverse['command_contract.py'].count(outer),1)
        inverse['command_contract.py']=inverse['command_contract.py'].replace(outer,'')
        self.assertEqual({n:hashlib.sha256(text.encode()).hexdigest()for n,text in inverse.items()},proof['whole_v2_overlay_sha256'])
        W=P.parents[1];old=W/'bole_service_proposals/gdn_service_probe_g1_v2/ADVISORY_MANIFEST.json'
        if old.is_file():
            for r in json.loads(old.read_bytes())['files'].values():self.assertEqual(B.ref(r['path']),r)
        for name in('gdn_probe_runtime.py','gdn_probe_contract.py','gdn_service_gate.py','gdn_service_seam.py','consume_gdn_service.py',
            'test_gdn_probe_pure.py','test_gdn_service_pure.py'):
            original=W/'bole_service_proposals/gdn_service_probe_g1_v2'/name
            if original.is_file():self.assertEqual((P/name).read_bytes(),original.read_bytes())

if __name__=='__main__':unittest.main()
