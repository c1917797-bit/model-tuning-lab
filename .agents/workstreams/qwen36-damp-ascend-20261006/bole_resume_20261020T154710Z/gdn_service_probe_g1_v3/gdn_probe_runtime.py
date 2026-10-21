"""Source-bound default-OFF G1 glue; no device/container/process admission."""
import json
import os
from pathlib import Path
import types


def helper(C,m):
    r=m['files']['gdn_probe_contract.py'];C.checked(r)
    import importlib.util,sys
    name='_gdn_probe_exact_contract'
    if name not in sys.modules:
        s=importlib.util.spec_from_file_location(name,r['path']);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v)
    value=sys.modules[name];C.need(C.ref(value.__file__)==r,'exact private probe contract');return value


def collect(C,values,*,installed_refs=()):
    refs={}
    def walk(value):
        if type(value)is dict:
            if set(value)in({'path','bytes','sha256'},{'path','sha256'}):
                if any(value==r for r in installed_refs):return
                if value['path']in refs:
                    old=refs[value['path']]
                    C.need(old['sha256']==value['sha256']and('bytes'not in value or old['bytes']==value['bytes']),
                           'no conflicting Ref for one path')
                    return
                # This helper upgrades original025 Ref2 only after exact SHA.
                r=C.ref(value['path']);C.checked(r)
                C.need(r['sha256']==value['sha256']and('bytes'not in value or r['bytes']==value['bytes']),
                       'complete explicit readset bytes, no prefix/path-only exception')
                if r['path']in refs:C.need(refs[r['path']]==r,'no conflicting Ref for one path')
                refs[r['path']]=r
            else:
                for v in value.values():walk(v)
        elif type(value)in(list,tuple):
            for v in value:walk(v)
    walk(values);return list(refs.values())


def host_readset(C,sr,m):
    C.need(sr==C.ref(Path(m['root'])/'SOURCE_BOUND.json')and
           m['gdn_service_extension']['purpose']=='service_numerical_only',
           'actual current source file and bounded numerical-only host path')
    P=helper(C,m);x=C.obj(m['gdn_service_extension']['source'])
    on,_,_,_=P.prior(C,x['prior_G1'])
    G=P.load(C,m['files']['gdn_service_gate.py'],'_gdn_probe_host_gate')
    H,replay=G.replay_contract(C,x)
    objects=[m['gdn_service_extension']['source'],x,*x['prior_G1'].values(),list(on['files'].values())]
    owner=C.obj(x['prior_G1']['owner'])
    for k in('CPU_release','model_release','independent_release'):
        r=P.fullref(C,owner['summary'][k]);objects.extend([r,C.obj(r)])
    for k in('replay_result','replay_independent','replay_release','replay_manifest'):
        objects.extend([x[k],C.obj(x[k])])
    objects.extend([C.obj(replay['admission']),C.obj(replay['actual_source'])['files']['sourceio.py']])
    for rank in replay['receipts']:objects.extend([rank['receipt'],C.obj(rank['receipt'])])
    result=C.obj(x['replay_result'])
    for index in result['ranks']:objects.extend([index,C.obj(index)])
    # G1 common installed refs can occur inside original metadata receipts;
    # exact Ref3 identity only, never skip a path prefix or unknown Ref2.
    refs=collect(C,objects,installed_refs=tuple(m['runtime_sources'].values()))
    C.need(C.ref(__file__)==m['files']['gdn_probe_runtime.py'],'exact new host/source glue')
    return refs


def handoff_readset(C,sr,m,reference):
    P=helper(C,m);P.software(C,reference,sr,m);value=C.obj(reference)
    release=C.obj(value['release'])
    return collect(C,[reference,value,C.obj(value['child']),release],installed_refs=tuple(m['runtime_sources'].values()))


def server_environment(C,m,sr,base,reference):
    P=helper(C,m);C.need(m['gdn_service_extension']['purpose']=='service_numerical_only',
                       'this probe never admits capture-OFF or performance qualification')
    P.software(C,reference,sr,m)
    e=dict(base);e.update(BOLE_GDN_SERVICE_FUSION_ENABLE='1',BOLE_GDN3_TRITON_ENABLE='1',
        BOLE_GDN_SERVICE_SOFTWARE_REF=json.dumps(reference))
    return e


def install(bridge,live,C,m):
    if os.environ.get('BOLE_GDN_SERVICE_FUSION_ENABLE')!='1':return dict(enabled=False,NPU=False)
    P=helper(C,m);sr=C.ref(Path(m['root'])/'SOURCE_BOUND.json')
    C.need(C.obj(sr)==m==bridge.own_source and C.ref(__file__)==m['files']['gdn_probe_runtime.py'],
           'current exact source-owned G1 bridge and actual bound source file')
    reference=json.loads(os.environ['BOLE_GDN_SERVICE_SOFTWARE_REF']);P.software(C,reference,sr,m)
    S=P.load(C,m['files']['gdn_service_seam.py'],'_gdn_probe_service_seam')
    ctl=S.install(bridge,live,C,m,extension_ref=m['gdn_service_extension']['source'],service_source_ref=sr,
                  software_gate_ref=reference,arm_verified=True)
    C.need(type(ctl)is S.Controller,'enabled seam must install exact owned controller')
    original=bridge.restore;had='restore'in bridge.__dict__;prior=bridge.__dict__.get('restore')
    def restore(this):
        C.need(this is bridge and getattr(this.restore,'__func__',None)is restore,
               'only owned bridge restoration wrapper may remove seam')
        ctl.restore()
        if had:this.restore=prior
        else:delattr(this,'restore')
        return original()
    bridge.restore=types.MethodType(restore,bridge)
    return ctl


def abort(bridge,ctx,primary):
    ctl=getattr(bridge,'_bole_gdn_extension',None)
    if ctl is not None:
        try:ctl.abort(ctx)
        except BaseException as error:
            try:primary.add_note('GDN private abort failure: '+repr(error))
            except BaseException:pass
