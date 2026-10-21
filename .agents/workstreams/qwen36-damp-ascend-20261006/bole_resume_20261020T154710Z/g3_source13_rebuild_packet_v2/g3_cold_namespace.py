
"""Isolated original saved-v7 metadata namespace; no resource/backend calls."""
import importlib.util
import sys
from pathlib import Path

_ORDER=('sourceio.py','g2_contract.py','g1_contract.py','g2_channel.py','g2_finalize.py')


def replay(C,m,old,originals,evidence_source,channel_ref):
    C.need(C.ref(__file__)==m['files']['g3_cold_namespace.py'],
           'exact source-bound G3 cold namespace implementation')
    C.need(set(originals)==set(_ORDER) and all(originals[n]==old['files'][n]for n in _ORDER),
           'only the complete original saved-v7 five-module closure')
    before_path=list(sys.path);path_object=sys.path
    old_root=str(Path(old['root']))
    missing=object();previous={};installed={};modules={};private_names={}
    for filename in _ORDER:
        name=filename[:-3];private='_g3_cold_exact_saved_v7_'+name
        C.need(private not in sys.modules,'fresh private original module '+private)
        private_names[name]=private
        existing=sys.modules.get(name,missing)
        if existing is not missing:
            C.need(existing is not None and getattr(existing,'__file__',None)
                   and C.ref(existing.__file__)==m['files'][filename],
                   'only current source-owned preexisting module, never foreign '+name)
        previous[name]=existing;previous[private]=missing
        C.checked(originals[filename]);C.checked(m['files'][filename])
    proof=dict(schema='bole.explicit-G3-saved-v7-metadata-namespace/v1',
        evidence_source=evidence_source,current_support_sources={n:m['files'][n]for n in _ORDER},
        original_support_sources=originals,load_order=list(_ORDER),
        current_namespace_before={n:(None if previous[n]is missing else C.ref(previous[n].__file__))
                                  for n in private_names},
        current_namespace_restored_by_identity=False,sys_path_restored_by_identity=False,
        original_functions_whole_sources=True,current_G3_contract_not_used_as_old_v7=True,
        actual_live_identity_qualified=False,model_ready=False,NPU=False)
    answer=None
    try:
        for filename in _ORDER:
            name=filename[:-3];private=private_names[name]
            C.need(sys.modules.get(name,missing)is previous[name],
                   'canonical slot still owned by original current namespace before replacement '+name)
            C.need(private not in sys.modules,'private slot remained absent before own load')
            path=C.checked(originals[filename])
            spec=importlib.util.spec_from_file_location(private,path)
            value=importlib.util.module_from_spec(spec)
            sys.modules[private]=value;installed[private]=value
            spec.loader.exec_module(value)
            C.need(C.ref(value.__file__)==originals[filename],
                   'whole actual original module loaded '+name)
            C.need(sys.modules.get(private)is value and sys.modules.get(name,missing)is previous[name],
                   'loader retained only its owned private slot '+name)
            sys.modules[name]=value;installed[name]=value;modules[name]=value
        C.need(sys.path is path_object and sys.path==[old_root]+before_path,
               'original finalizer inserted exactly one declared old-root lookup prefix')
        for name,value in installed.items():
            C.need(sys.modules.get(name)is value,'all isolated module slots remain exactly owned '+name)
        first=modules['g2_channel'].contract(C,evidence_source,channel_ref)
        second=modules['g2_finalize'].owned_channel(old,evidence_source,channel_ref)
        C.need(sys.path is path_object and sys.path==[old_root]+before_path,
               'original metadata functions did not change lookup namespace')
        for filename in _ORDER:C.checked(originals[filename])
        answer=(first,second)
    finally:
        failures=[]
        for name,value in reversed(list(installed.items())):
            if sys.modules.get(name,missing)is not value:
                failures.append('foreign module slot '+name);continue
            prior=previous[name]
            if prior is missing:sys.modules.pop(name,None)
            else:sys.modules[name]=prior
        for name,prior in previous.items():
            if sys.modules.get(name,missing)is not prior:
                failures.append('original module identity not restored '+name)
        if sys.path is not path_object:
            failures.append('foreign sys.path object')
        elif sys.path==before_path or sys.path==[old_root]+before_path:
            sys.path[:]=before_path
        else:
            failures.append('unowned sys.path change')
        if sys.path is not path_object or sys.path!=before_path:
            failures.append('lookup namespace not restored')
        C.need(not failures,'exact cold namespace restoration: '+repr(failures))
        proof['current_namespace_restored_by_identity']=True
        proof['sys_path_restored_by_identity']=True
    C.need(answer is not None,'original saved-v7 verifier pair actually completed')
    return answer[0],answer[1],proof


if __name__=='__main__':
    print('{"enabled":false,"NPU":false}')
