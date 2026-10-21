"""Private exact singleton delta over original025 and its readonly adapter.

No controller/resource/safety method is reimplemented or called on import.
Only one numbered NPU is exposed; the original seven-CPU and cap32 budgets,
protected0..3, FD/HBM/resource/observation/cleanup functions remain original.
"""
import ast
from contextlib import contextmanager
import hashlib
import marshal
from pathlib import Path
import sys
import types


def code_sha(code):return hashlib.sha256(marshal.dumps(code)).hexdigest()


def derive_external_singleton(E,body,filename,globals_):
    text,readonly_pairs=E.derive(body)  # Exact original22338 source + all four existing readonly deltas.
    pairs=[('len(dev)==(0 if cpu else 7)','len(dev)==(0 if cpu else 4)'),
        ('enumerate(PHYSICAL)','enumerate((4,))')]
    changed=text
    for before,after in pairs:
        if changed.count(before)!=1:raise ValueError('one exact singleton device-map/count operand')
        changed=changed.replace(before,after)
    inverse=changed
    for before,after in reversed(pairs):
        if inverse.count(after)!=1:raise ValueError('unique singleton device-map/count inverse')
        inverse=inverse.replace(after,before)
    if inverse!=text:raise ValueError('whole singleton inverse')
    def compile_functions(source,new):
        tree=ast.parse(source);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in('device_map','create_argv','validate_inspect')]
        if len(nodes)!=3:raise ValueError('exact original device_map plus two readonly safety functions')
        output={}
        for node in nodes:
            name=filename+('#AR-singleton-only'if new else ''if node.name=='device_map'else'#064-readonly-only')
            scope=dict(globals_);exec(compile(ast.Module(body=[node],type_ignores=[]),name,'exec'),scope)
            output[node.name]=scope[node.name]
        return output
    previous=compile_functions(text,False);next_=compile_functions(changed,True)
    return previous,next_,dict(readonly_pairs=[dict(before=a,after=b)for a,b in readonly_pairs],
        singleton_pairs=[dict(before=a,after=b)for a,b in pairs],whole_singleton_inverse=True,
        prior_readonly_source_sha256=hashlib.sha256(text.encode()).hexdigest(),
        singleton_source_sha256=hashlib.sha256(changed.encode()).hexdigest())


@contextmanager
def install(C,c,S,H,on):
    C.need('external025'in sys.modules and C.ref(sys.modules['external025'].__file__)==on['files']['external025.py'],
        'exact already-installed original readonly adapter')
    E=sys.modules['external025'];old={name:getattr(S,name)for name in('device_map','environment','create_argv','validate_inspect')}
    C.need(S.PHYSICAL==(4,5,6,7)and S.PHASE==3600 and S.CLEANUP==180 and S.MEM==32*2**30 and
        S.RESERVE==8*2**30 and S.HOST_MEM==512*2**20 and S.WORKSPACE==32*2**30,
        'actual original025 postcap32 private profile before singleton delta')
    previous,next_,delta=derive_external_singleton(E,Path(S.__file__).read_bytes(),S.__file__,dict(S.__dict__,_EXTERNAL=S._EXTERNAL))
    for name in('device_map','create_argv','validate_inspect'):
        C.need(getattr(S,name).__globals__ is vars(S)and marshal.dumps(getattr(S,name).__code__)==marshal.dumps(previous[name].__code__),
            'actual exact installed readonly function before singleton change '+name)
    original_controller=S.Controller;controller_methods={n:getattr(S.Controller,n)for n in('observe','resources','remaining','create_owned','inspect','cleanup')}
    def environment(cpu=False):
        value=old['environment'](cpu)
        C.need(value['ASCEND_RT_VISIBLE_DEVICES']==(''if cpu else'0,1,2,3'),'exact original CPU/TP4 visibility before singleton delta')
        value['ASCEND_RT_VISIBLE_DEVICES']=''if cpu else'0';return value
    new=dict(environment=environment,
        **{n:types.FunctionType(next_[n].__code__,S.__dict__,n)for n in('device_map','create_argv','validate_inspect')})
    try:
        for name,value in new.items():setattr(S,name,value)
        C.need(S.device_map()==dict([('/dev/davinci4','/dev/davinci0')]+[('/dev/'+n,'/dev/'+n)for n in('davinci_manager','devmm_svm','hisi_hdc')]),
            'physical4 only to logical0 plus original three aux nodes; never0..3/5..7')
        C.need(S.PHYSICAL==(4,5,6,7)and S.Controller is original_controller and all(getattr(S.Controller,n)is v for n,v in controller_methods.items()),
            'all original controller safety/FD/HBM/CPU/remaining/cleanup methods unchanged')
        proof=dict(schema='bole.native-AR-private-singleton025-profile/v1',adapter=C.ref(__file__),
            original025=C.ref(S.__file__),original_readonly_adapter=C.ref(E.__file__),**delta,
            globals_delta=dict(ASCEND_RT_VISIBLE_DEVICES=dict(before='0,1,2,3',after='0',CPU='')),
            resource_PHYSICAL_unchanged=[4,5,6,7],original_FD_HBM_idle_scope_preserved=True,
            physical=[4],logical=[0],protected=[0,1,2,3],phase_seconds=3600,cleanup_seconds=180,
            cap32_and_seven_CPU_budget_unchanged=True,original_Controller_and_resource_methods_unchanged=True,
            original_source_label_plus_explicit_adapter_delta=True,inverse_by_object_identity_required=True,NPU=False)
        yield proof
    finally:
        errors=[]
        for name,value in new.items():
            if getattr(S,name)is not value:errors.append('foreign singleton attribute '+name);continue
            setattr(S,name,old[name])
            if getattr(S,name)is not old[name]:errors.append('singleton inverse identity '+name)
        for name,value in controller_methods.items():
            if getattr(S.Controller,name)is not value:errors.append('foreign original controller method '+name)
        if errors:raise ValueError('; '.join(errors))
