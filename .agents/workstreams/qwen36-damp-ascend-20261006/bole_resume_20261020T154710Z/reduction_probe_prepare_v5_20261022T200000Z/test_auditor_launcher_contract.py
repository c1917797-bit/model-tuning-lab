"""Exercise the actual auditor payload expression against actual launcher source_inputs."""
import ast
import copy
import importlib.util
import json
import pathlib
import sys
import time
import types
import unittest

HERE=pathlib.Path(__file__).resolve().parent
WS=HERE.parent
ACTUAL=WS/'boundary_source_audit_v5_textonly_20261022T171000Z/audit_boundary_source_v5.py'
LAUNCHER=HERE/'admission_contract_snapshot.py'


class ReachedOriginalSourceGate(Exception):pass


class Tests(unittest.TestCase):
    def test_whole_actual_auditor_inverse(self):
        old=ACTUAL.read_text()
        for arm in ('ON','OFF'):
            new=(HERE/arm/'audit_boundary_source.py').read_text()
            expected=old.replace("PREP = WS/'boundary_source_audit_v5_textonly_20261022T171000Z'",
                'PREP = Path('+json.dumps(str(HERE/arm))+')')
            expected=expected.replace("ROOT = WS/'bound-boundary-ON-v4-textonly_20261022T171000Z'",
                'ROOT = Path('+json.dumps(str(WS/('bound-reduction-%s-v5_20261022T200000Z'%arm)))+')')
            expected=expected.replace("OUT = Path('/opt/host/vnf/austinov/run-bole-boundary-source-audit-v5-textonly_20261022T171000Z')",
                'OUT = Path('+json.dumps('/opt/host/vnf/austinov/run-bole-reduction-%s-v5_20261022T200000Z-SOURCE-AUDIT'%arm)+')')
            expected=expected.replace("PREP/'audit_boundary_source_v5.py'","PREP/'audit_boundary_source.py'")
            self.assertEqual(new,expected)
            # Exact whole-file inverse protects every original actual check.
            self.assertIn('actual==seen',new)
            self.assertIn('recorded_argument==actual_argument',new)
            self.assertIn("C.checked(args.audit_program_ref)",new)

    def fixture(self):
        source_root=WS/'bound-reduction-ON-v5_20261022T200000Z'
        output=pathlib.Path('/opt/host/vnf/austinov/run-bole-reduction-ON-v5_20261022T200000Z')
        def ref(name):return dict(path=str(source_root/name),bytes=1,sha256='a'*64)
        sr,commands_ref,authority_ref=map(ref,('SOURCE_BOUND.json','COMMANDS.json','SHORT_AUTHORITY.json'))
        authorization_ref,document_ref,build_ref=map(ref,('AUTH.json','AUTH.md','BUILD.json'))
        audit_ref,program_ref,original_ref=map(ref,('AUDIT.json','auditor.py','original-auditor.py'))
        review_ref,parent_ref,contract_ref=map(ref,('REVIEW.json','PARENT.json','contract090.py'))
        config=dict(source_ref=sr,commands_ref=commands_ref,source_audit_ref=audit_ref,
            source_audit_program_ref=program_ref,build_record_ref=build_ref,authorization_ref=authorization_ref)
        manifest=dict(root=str(source_root),output_root=str(output),default_enabled=False,prepared_only=False,
            text_only_config=dict(language_model_only=True,skip_mm_profiling=False,enable_mm_embeds=False,limit_mm_per_prompt={}),
            authority_ref=authority_ref,files={'contract090.py':contract_ref},dependencies=[authorization_ref,document_ref])
        authority=dict(start_epoch=1792689000,cutoff_epoch=1792710600,cutoff_iso='2026-10-22T23:10:00+00:00',
            phase_seconds=3600,cleanup_seconds=180,user_authorization_ref=authorization_ref)
        authorization=dict(old_window_extended=False,old_hard_report_deadline_utc='2026-10-22T12:38:41+00:00',
            internal_batch_start_epoch=1792689000,internal_batch_cutoff_epoch=1792710600,
            whole_prepare_admission_seconds=3780,document=document_ref)
        build=dict(schema='bole.boundary-probe-source-freeze/v1',source=sr,commands=commands_ref,source_only=True,
            original_inputs_unchanged=True,fixed_cutoff=1792710600,historical_report_cutoff=1792672721,
            old_window_extended=False,phase_seconds=3600,cleanup_seconds=180,parent=parent_ref,
            review=review_ref,original_readset=[],**{k:False for k in ('owner_created','NPU','paired_gate_pass','performance_admitted','formal_performance')})
        references=[sr,commands_ref,authority_ref,contract_ref,authorization_ref,document_ref]
        tree=ast.parse((HERE/'ON'/'audit_boundary_source.py').read_text())
        writes=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
            and n.func.id=='write' and n.args and isinstance(n.args[0],ast.BinOp)
            and isinstance(n.args[0].right,ast.Constant) and n.args[0].right.value=='SOURCE_AUDIT.json']
        self.assertEqual(len(writes),1)
        namespace=dict(args=types.SimpleNamespace(source_ref=sr,audit_program_ref=program_ref),
            seen={r['path']:r for r in references},original_auditor=original_ref,recorded_argument=json.dumps(sr),
            proof={'tests':list(range(20))},time=time,started=time.monotonic())
        audit=eval(compile(ast.Expression(writes[0].args[1]),'<actual SOURCE_AUDIT payload>','eval'),namespace)
        objects={r['path']:v for r,v in [(sr,manifest),(audit_ref,audit),(commands_ref,dict(bound_source=sr,model=['model'])),
            (authority_ref,authority),(authorization_ref,authorization),(build_ref,build)]}
        source_inputs=next(n for n in ast.parse(LAUNCHER.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='source_inputs')
        reached=[]
        def need(v,m):
            if not v:raise ValueError(m)
        def load_exact(*args):
            reached.append(True)
            raise ReachedOriginalSourceGate()
        globs=dict(SOURCE=source_root,OUTPUT=output,TEXT_ONLY_CONFIG=manifest['text_only_config'],
            CUT=1792710600,OLD_REPORT_CUT=1792672721,START=1792689000,PHASE=3600,CLEANUP=180,PREPARE=3780,
            typed_ref=lambda r:pathlib.Path(r['path']),need=need,sys=sys,load_exact=load_exact)
        exec(compile(ast.Module(body=[source_inputs],type_ignores=[]),'<actual launcher source_inputs>','exec'),globs)
        class Readset:
            def obj(self,r):return objects[r['path']]
            def read(self,r,**kwargs):return b''
        return globs['source_inputs'],Readset(),config,audit,reached

    def test_actual_payload_reaches_original_source_gate(self):
        function,rs,config,audit,reached=self.fixture()
        # Execute the actual launcher body through every metadata/readset predicate.
        # Stop before the real source loader; this fixture cannot grant source/NPU admission.
        before=list(sys.path)
        try:
            with self.assertRaises(ReachedOriginalSourceGate):function(rs,config)
        finally:sys.path[:]=before
        self.assertEqual(reached,[True])
        self.assertEqual(audit['historical_report_cutoff'],1792672721)
        self.assertFalse(audit['old_window_extended'])

    def test_actual_launcher_rejects_each_missing_or_wrong_audit_field(self):
        keys=('historical_report_cutoff','old_window_extended','audit_program_ref','original_audit_source',
              'host_readset_exact','audit_program_unchanged','readset','recorded_source_argument')
        for key in keys:
            function,rs,config,audit,reached=self.fixture()
            # recorded_source_argument is enforced by the actual producer itself;
            # the launcher does not read it. Preserve that boundary explicitly.
            if key=='recorded_source_argument':
                self.assertIn('recorded_argument==actual_argument',(HERE/'ON'/'audit_boundary_source.py').read_text())
                continue
            del audit[key]
            with self.assertRaises((KeyError,ValueError)):function(rs,config)
            self.assertEqual(reached,[])
        for key,value in [('historical_report_cutoff',1792710600),('old_window_extended',True),
                          ('audit_program_unchanged',False),('source_validated',False)]:
            function,rs,config,audit,reached=self.fixture();audit[key]=value
            with self.assertRaises(ValueError):function(rs,config)
            self.assertEqual(reached,[])

if __name__=='__main__':
    unittest.main()
