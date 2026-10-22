"""Exact current-authority clock seam. Pure source renderer; no approval or launch."""
import ast

OLD='''def phase_admission(C,entry_start):
    C.need(type(entry_start)in(int,float)and C.CUT==CUTOFF,'original fixed source-owned cutoff')
    now=time.monotonic();remaining=min(entry_start+PHASE-now,C.CUT-time.time())-CLEANUP
    C.need(now>=entry_start and remaining>=CREATE_CAP,'cold source/readset work consumes original3600; original180cleanup and create60 must still fit, never reset')
    return remaining


def controller_admission(C,c,S,ctl,entry_start):
    C.need(S.PHASE==PHASE and S.CLEANUP==CLEANUP and c.CUTOFF==CUTOFF and
        ctl.created_monotonic==entry_start and ctl.deadline==entry_start+PHASE,
        'same actual main entry reaches original Joint/controller deadline and fixed cutoff')
    # Exact original remaining() already subtracts CLEANUP. Do not reserve it twice.
    C.need(ctl.remaining(cap=CREATE_CAP)==CREATE_CAP,'before create original capped60 must fit after original cleanup reserve; no renewed start')'''

NEW='''def current_authority(C):
    from pathlib import Path
    import followup_source_validate as V
    root=Path(C.__file__).resolve().parent
    m=C.obj(C.ref(root/'SOURCE_BOUND.json'))
    C.need(m['root']==str(root)and
           C.ref(__file__)==m['files']['g2_cold_clock.py']and
           C.ref(V.__file__)==m['files']['followup_source_validate.py'],
           'actual source-owned clock and current authority helper')
    # Initial C.source already reserved the complete3600+180 window. Every
    # downstream check preserves that ONE main-entry clock, never starts it anew.
    return V.execution_window(m,clock=True,require_phase=False)


def phase_admission(C,entry_start):
    C.need(type(entry_start)in(int,float),'actual original monotonic main entry')
    cutoff=current_authority(C)['cutoff_epoch']
    now=time.monotonic();remaining=min(entry_start+PHASE-now,cutoff-time.time())-CLEANUP
    C.need(now>=entry_start and remaining>=CREATE_CAP,'cold source/readset work consumes original3600; original180cleanup and create60 must still fit, never reset')
    return remaining


def controller_admission(C,c,S,ctl,entry_start):
    cutoff=current_authority(C)['cutoff_epoch']
    C.need(S.PHASE==PHASE and S.CLEANUP==CLEANUP and c.CUTOFF==cutoff and
        ctl.created_monotonic==entry_start and ctl.deadline==entry_start+PHASE,
        'same actual main entry reaches original Joint/controller deadline and CURRENT authority cutoff')
    # Exact original remaining() already subtracts CLEANUP. Do not reserve it twice.
    C.need(ctl.remaining(cap=CREATE_CAP)==CREATE_CAP,'before create original capped60 must fit after original cleanup reserve; no renewed start')'''


def apply(files):
    out=dict(files);text=out['g2_cold_clock.py'].decode()
    if text.count(OLD)!=1:raise ValueError('one exact old reachable phase/controller clock seam')
    new=text.replace(OLD,NEW,1)
    if new.replace(NEW,OLD,1)!=text:raise ValueError('complete clock inverse')
    ast.parse(new);out['g2_cold_clock.py']=new.encode()
    return out
