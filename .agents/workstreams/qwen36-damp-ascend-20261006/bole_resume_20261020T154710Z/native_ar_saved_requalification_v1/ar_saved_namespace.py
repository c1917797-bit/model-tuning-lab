"""Private fresh-process output namespace over unchanged source-bound025 helpers.

No source file is edited. The ONLY additional output deltas are the explicit
four contract090 path globals, restored by object identity after owned cleanup.
The original owned_substrate's documented source/window/budget/provider deltas
remain its own exact code; this adapter does not replace a safety function.
"""
from contextlib import contextmanager
from pathlib import Path
import sys

NAMES=('sourceio','contract090','external025','cap48_provider','owned_substrate',
       'output_scan131r8','observer_race_repair','frontend_namespace131r18','identity_owner',
       'owned_create','owned_ref131r7','fault_receipt')


@contextmanager
def open_namespace(C,inputs,on):
    C.need(not any(n in sys.modules for n in (*NAMES,'model_contract','safety_host','_mxr_actual025_host_once')),
           'fresh private host CLI; never replace a live/foreign namespace')
    files=on['files'];old_path=list(sys.path);deltas=[];old_external=None;E=None
    required=(*NAMES,)
    for name in required:C.checked(files[name+'.py'])
    output=Path(inputs['output_root'])
    producer=C.obj(inputs['saved_producer_result'])
    C.need(output.is_absolute() and output.is_dir() and not output.is_symlink() and
           producer['inputs']==inputs['original_owner_inputs'] and
           producer['source']==inputs['AR_source'] and producer['primary'] is not None and
           producer['secondary']==[] and producer['source_before']==producer['source_after'] and
           not(output/'cpu-consumer').exists() and
           Path(inputs['host_record_root']).parent==output and not Path(inputs['host_record_root']).exists(),
           'exact stopped saved producer root; fresh declared CPU leaf and new host record leaf')
    C.need(Path(inputs['output_root']).parent==Path('/opt/host/vnf/austinov')and
           Path(inputs['output_root']).name.startswith('run-bole-native-ar-'),
           'one source-bound native AR output leaf, no broad output escape')
    try:
        sys.path.insert(0,on['root'])
        C.load(files['sourceio.py'],'sourceio')
        D=C.load(files['contract090.py'],'contract090')
        original={k:getattr(D,k)for k in('OUT','CPU_OUT','OUTPUT_POSIX','CPU_OUTPUT_POSIX')}
        output=Path(inputs['output_root']);new=dict(OUT=output,OUTPUT_POSIX=str(output),
            CPU_OUT=output.with_name(output.name+'-CPU-unused'),CPU_OUTPUT_POSIX=str(output.with_name(output.name+'-CPU-unused')))
        for name,value in new.items():
            setattr(D,name,value);deltas.append(dict(module='contract090',name=name,before=str(original[name]),after=str(value)))
        E=C.load(files['external025.py'],'external025');old_external=E.OUT
        substrate=C.load(files['owned_substrate.py'],'owned_substrate')
        c,S,H,budget_pairs=substrate.load(output)
        C.need(E.OUT==output and S.PHYSICAL==(4,5,6,7) and S.PHASE==3600 and S.CLEANUP==180 and
               S.WORKSPACE==32*c.GIB and S.MEM==32*c.GIB and S.RESERVE==8*c.GIB and
               S.HOST_MEM==512*2**20,'unchanged registered original025/cap32/resources/window/cleanup gates')
        for name in NAMES:
            if name in sys.modules:C.need(C.ref(sys.modules[name].__file__)==files[name+'.py'], 'source-bound private025 dependency '+name)
        authority=C.obj(inputs['authority'])
        C.need(c.CUTOFF==authority['cutoff_epoch'] and authority['start_epoch']<=__import__('time').time()<c.CUTOFF,
               'actual unchanged separately authorized cutoff, no reset/extension')
        proof=dict(schema='bole.native-ar-private-host-namespace/v1',additional_globals=deltas,
            external_output=dict(before=str(old_external),after=str(E.OUT)),
            inverse_required_after_cleanup=True,original025_safety_reimplemented=False,
            owner_substrate=files['owned_substrate.py'],external025=files['external025.py'],
            original_budget_deltas=[dict(before=a.decode(),after=b.decode())for a,b in budget_pairs],
            phase_seconds=3600,cleanup_seconds=180,resource_guards_preserved=True,
            protected0_3_preserved=True,physical=[4,5,6,7],NPU=False)
        yield c,S,H,proof
    finally:
        if 'D'in locals() and 'original'in locals():
            for name,value in original.items():
                C.need(getattr(D,name)==new[name], 'no foreign private output global replacement')
                setattr(D,name,value);C.need(getattr(D,name)is value,'exact original global object inverse')
        if E is not None and old_external is not None:E.OUT=old_external
        sys.path[:]=old_path
