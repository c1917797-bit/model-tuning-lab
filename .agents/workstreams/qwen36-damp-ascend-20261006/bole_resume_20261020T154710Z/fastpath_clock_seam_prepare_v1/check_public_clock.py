"""Synthetic IN-MEMORY authority/source controls. No physical approval/bind or devices."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import time
import types
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import prepare_clock as BUILD


def data(value):return (json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
def reference(path,raw):return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def fixture():
    b=BUILD.render();root=Path(b['manifest']['root'])
    gate=types.ModuleType('clock_fixture_schema_only')
    exec(compile(b['files']['qualification_source_validate.py'],'actual gate constants','exec'),gate.__dict__)
    m=b['manifest'];review=dict(schema=gate.REVIEW_SCHEMA,approved=True,scope=gate.SCOPE,
        source_root=m['root'],output_root=m['output_root'],files=m['files'],
        parent_preparation_readset=m['qualification_parent_preparation_readset'],
        historical_short_source=m['qualification_historical_short_source'])
    rr=reference(root/'SYNTHETIC_MEMORY_REVIEW.json',data(review))
    now=int(time.time());authority=dict(schema=gate.AUTH_SCHEMA,approved=True,start_epoch=now-60,
        cutoff_epoch=now+7200,scope=gate.SCOPE,MAIN_review_ref=rr)
    ar=reference(root/'SYNTHETIC_MEMORY_AUTHORITY.json',data(authority))
    b=BUILD.render(authority_ref=ar);BUILD.inverse(b)
    template=b['manifest'];tr=reference(root/'SOURCE_TEMPLATE.json',data(template))
    m=copy.deepcopy(template);m.update(prepared_only=False,qualification_source_binding_pending=False,prepared_template=tr)
    sr=reference(root/'SOURCE_BOUND.json',data(m));b=dict(b,manifest=m)
    ns=dict(Path=Path,json=json)
    tree=ast.parse(b['files']['command_contract.py']);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='expected')
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual public command constructor','exec'),ns)
    commands=ns['expected'](m['root'],m['output_root'],sr,tr,m['component_refs'])
    historical=json.loads(Path(m['command_scope']['historical_ref']['path']).read_bytes())
    cv=dict(schema='bole.performance-actual-bound-commands/v1',source=tr,bound_source=sr,
        required_sameimage_software_cases=25,historical_required_sameimage_software_cases=historical['required_sameimage_software_cases'],
        G3_stream_protocol=False,actual_G3_execution_claimed=False,actual_G1_execution_claimed=False,
        legacy_entrypoints_retained_for_inverse_tests_only=True,**commands)
    cr=reference(root/'COMMANDS.json',data(cv));mirror=dict(source=sr,template=tr,commands=cr,
        model=cv['model'],CPU=cv['CPU'],required_sameimage_software_cases=25)
    extra={rr['path']:data(review),ar['path']:data(authority),str(root/'SOURCE_TEMPLATE.json'):data(template),
        str(root/'COMMANDS.json'):data(cv),str(root/m['command_scope']['compatibility_file']):data(mirror)}
    return b,extra,sr,authority


def main():
    if sys.argv[1:]!=['--check']:raise SystemExit('default OFF: synthetic in-memory --check only')
    b,extra,sr,authority=fixture();events=[]
    def run(virtual,bundle,root):
        import sourceio as C
        import followup_source_validate as V
        import g2_cold_clock as CLOCK
        import host_service as HOST
        import owned_substrate as OWNED
        import contract090 as CONTRACT
        proof=V.validate(sr) # ACTUAL full gate, not a stubbed validated=True row
        C.need(proof['source_validated']is True,'actual gate accepted synthetic bound fixture')
        events.append('actual-whole-source-validator-with-synthetic-memory-source')
        C.need(CONTRACT.source(sr)==bundle['manifest'],'actual public C.source/dependency/component readset')
        events.append('actual-contract090-source-component-readset')
        class BeforeOwnership(Exception):pass
        def stop(*a,**kw):raise BeforeOwnership('STOP before actual owned helper load / device operations')
        model=json.loads(virtual[str(root/'COMMANDS.json')])['model']
        index=model.index('/usr/bin/python3');python_argv=model[index:]
        virtual['/proc/self/cmdline']=b'\0'.join(x.encode()for x in python_argv)+b'\0'
        env=dict(BOLE_MODEL131_MAIN_ENABLE='1',DENSE090_EXTERNAL_OUTPUT_ENABLE='1',
            BOLE_PAIRED_PERFORMANCE_ENABLE='1',BOLE_SHORT_STATE_DIGEST_ENABLE='1',
            BOLE_FASTPATH_NUMERIC_QUALIFICATION_ENABLE='1')
        import resource
        argv=[str(root/'host_service.py'),'--execute','--source-ref',json.dumps(sr),'--output',bundle['manifest']['output_root']]
        with patch.object(sys,'argv',argv),patch.dict('os.environ',env),patch.object(OWNED,'load',stop),\
             patch('os.sched_setaffinity',lambda *a:None),patch.object(resource,'getrlimit',lambda *a:(resource.RLIM_INFINITY,resource.RLIM_INFINITY)),\
             patch.object(resource,'setrlimit',lambda *a:None):
            try:HOST.main()
            except BeforeOwnership:events.append('actual-public-model-CLI-passed-phase-before-ownership-stop')
            else:raise ValueError('public model must stop before any ownership/device action')
        entry=time.monotonic();S=types.SimpleNamespace(PHASE=3600,CLEANUP=180)
        ctl=types.SimpleNamespace(created_monotonic=entry,deadline=entry+3600,remaining=lambda cap:cap)
        CLOCK.controller_admission(CONTRACT,types.SimpleNamespace(CUTOFF=authority['cutoff_epoch']),S,ctl,entry)
        events.append('actual-controller-current-cutoff')
        def reject(action,label):
            try:action()
            except ValueError:events.append('rejected-'+label)
            else:raise ValueError('negative control accepted '+label)
        reject(lambda:CLOCK.controller_admission(CONTRACT,types.SimpleNamespace(CUTOFF=1792597630),S,ctl,entry),'old-controller-cutoff')
        reject(lambda:CLOCK.phase_admission(CONTRACT,time.monotonic()-3361),'insufficient-original-phase')
        with patch.object(time,'time',lambda:authority['cutoff_epoch']+1):
            reject(lambda:CONTRACT.source(sr),'expired-authority')
        with patch.object(time,'time',lambda:authority['cutoff_epoch']-3700):
            reject(lambda:CONTRACT.source(sr),'insufficient-full-phase-cleanup')
        # Additional real read_ref/authority_shape negatives; modified operands
        # are NEW virtual JSON/Refs, not a bypass of hash verification.
        original=bundle['manifest'];base_authority=copy.deepcopy(authority)
        for label,change in [('wrong-scope',lambda a:a['scope'].update(output_tokens=160)),
                             ('unapproved',lambda a:a.update(approved=False))]:
            value=copy.deepcopy(base_authority);change(value)
            path=root/('SYNTHETIC_NEGATIVE_'+label+'.json');raw=data(value);virtual[str(path)]=raw
            m=copy.deepcopy(original);m['qualification_authority_ref']=reference(path,raw)
            reject(lambda m=m:V.execution_window(m,clock=True,require_phase=True),label)
        m=copy.deepcopy(original);m['qualification_authority_ref']=None
        reject(lambda:V.execution_window(m,clock=True,require_phase=True),'unbound-authority')
    # Reuse the already reviewed read-only virtual source/import adapter. Do NOT
    # execute its25-test lane again. Only replace its explicit fixture payload
    # and the body INSIDE the existing Path/import sandbox with this new chain.
    path=HERE.parent/'fastpath_numeric_bridge_prepare_v1/check_source_imports.py'
    tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
    class Transform(ast.NodeTransformer):
        def visit_Assign(self,node):
            if any(isinstance(t,ast.Name)and t.id=='b'for t in node.targets):
                return ast.copy_location(ast.Assign(targets=node.targets,value=ast.Name(id='FIXTURE',ctx=ast.Load())),node)
            if any(isinstance(t,ast.Subscript)and isinstance(t.value,ast.Name)and t.value.id=='virtual'for t in node.targets):
                return [node,ast.Expr(ast.Call(func=ast.Attribute(value=ast.Name(id='virtual',ctx=ast.Load()),attr='update',ctx=ast.Load()),args=[ast.Name(id='EXTRA',ctx=ast.Load())],keywords=[]))]
            return self.generic_visit(node)
        def visit_Expr(self,node):
            if isinstance(node.value,ast.Call)and ast.unparse(node.value.func)=='Q.inverse':return None
            return self.generic_visit(node)
        def visit_With(self,node):
            if node.body and isinstance(node.body[0],ast.Import)and any(n.name=='qualification_source_validate'for n in node.body[0].names):
                node.body=ast.parse('RUN(virtual,b,root)').body
                return node
            return self.generic_visit(node)
    tree=Transform().visit(tree);ast.fix_missing_locations(tree)
    ns=dict(__name__='synthetic_public_clock_fixture',__file__=str(path),FIXTURE=b,EXTRA=extra,RUN=run)
    with patch.object(sys,'argv',[str(path),'--reconstruct-only']):
        exec(compile(tree,'source-derived-readonly-virtual-adapter','exec'),ns);ns['main']()
    print(json.dumps(dict(schema='bole.synthetic-public-clock-chain-controls/v1',events=events,
        physical_authority_created=False,physical_source_bound_created=False,actual_bound_validated=False,
        synthetic_whole_source_validation=True,scheduler_or_device_actions=False,NPU=False),sort_keys=True))


if __name__=='__main__':main()
