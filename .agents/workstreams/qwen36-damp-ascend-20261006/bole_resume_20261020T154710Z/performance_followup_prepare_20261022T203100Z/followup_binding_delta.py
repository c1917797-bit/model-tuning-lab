"""Exact source-only replacements of historical execution-authority seams."""
import performance_followup_delta as D


def render(files):
    out=dict(files)
    def edit(name,before,after):out[name]=D.once(out[name].decode(),before,after).encode()
    edit('contract090.py',
      " if clock:need(START<=time.time()and time.time()+3600<CUT,'whole3600 must fit unchanged actual window')",
      " if clock:\n  import followup_source_validate as FSV\n  FSV.execution_window(m,clock=True,require_phase=True)")
    edit('worker_bootstrap.py',
      " authority=C.obj(m['authority_ref'])\n C.need(authority['start_epoch']==1792511230 and authority['cutoff_epoch']==1792597630 and\n        1792511230<=time.time()<1792597630,'actual current batch hardware window')",
      " import followup_source_validate as FSV\n C.need(C.ref(FSV.__file__)==m['files']['followup_source_validate.py'],'actual own execution-authority helper')\n FSV.execution_window(m,clock=True,require_phase=False)")
    edit('owned_substrate.py',
      " c.CUTOFF=1792597630;c.CUT='2026-10-21T15:47:10+00:00'",
      " import contract090 as CURRENT,followup_source_validate as FSV\n import datetime\n current=CURRENT.obj(CURRENT.ref(Path(CURRENT.__file__).resolve().parent/'SOURCE_BOUND.json'))\n authority=FSV.execution_window(current,clock=True,require_phase=False)\n c.CUTOFF=authority['cutoff_epoch'];c.CUT=datetime.datetime.fromtimestamp(c.CUTOFF,datetime.timezone.utc).isoformat()")
    edit('host_service.py',
      "import performance_validate as G3V;C.need(C.ref(G3V.__file__)==m['files']['performance_validate.py'],'current complete successor source gate');_g3_source_proof=G3V.validate(sr);C.need(type(_g3_source_proof)is dict and _g3_source_proof['schema']=='bole.performance-successor-source-validation/v1' and _g3_source_proof['source']==sr and _g3_source_proof['source_validated']is True,'full current successor source validation')",
      "import followup_source_validate as G3V;C.need(C.ref(G3V.__file__)==m['files']['followup_source_validate.py'],'current complete followup source gate');_g3_source_proof=G3V.validate(sr);C.need(type(_g3_source_proof)is dict and _g3_source_proof['schema']=='bole.followup-whole-source-validation/v1' and _g3_source_proof['source']==sr and _g3_source_proof['source_validated']is True,'full current followup source validation')")
    # Original software lane also has an independent absolute cutoff guard.
    # Its phase/cleanup/CPU limits are not changed; only actual authority source.
    edit('performance_software_stages.py','import performance_validate as V','import followup_source_validate as V')
    edit('performance_software_stages.py',
      '    b=Budget(phase_entry,lane_start,lane_deadline,1792597630,guest_entry)\n    m=C.obj(sr);P=Path(m[\'root\'])',
      '    m=C.obj(sr);P=Path(m[\'root\'])\n    b=Budget(phase_entry,lane_start,lane_deadline,V.active_cutoff(),guest_entry)')
    text=out['performance_software_stages.py'].decode()
    if text.count('fixed_cutoff=1792597630')!=2:raise ValueError('exact two original software admission cutoff fields')
    out['performance_software_stages.py']=text.replace('fixed_cutoff=1792597630','fixed_cutoff=V.active_cutoff()').encode()
    edit('performance_exact_controls.py','import performance_validate as V','import followup_source_validate as V')
    edit('service_entry.py','  import performance_validate as V','  import followup_source_validate as V')
    edit('g2_software_stages.py',
      "C.need(cutoff==1792597630 and lane_deadline-now<=cutoff-wall-CLEANUP+0.01,'same unchanged absolute cutoff and cleanup reserve')",
      "C.need(cutoff==__import__('followup_source_validate').active_cutoff() and lane_deadline-now<=cutoff-wall-CLEANUP+0.01,'same actual new authority cutoff and unchanged cleanup reserve')")
    # A full-source audit is not algorithm admission. Keep this explicit
    # fail-closed hook before the host reaches resource creation.
    edit('host_service.py',
      "'full current followup source validation');C.need(m['service_experiment']==G1.SCOPE",
      "'full current followup source validation');G3V.require_fastpath_admission(m);C.need(m['service_experiment']==G1.SCOPE")
    for name in('contract090.py','worker_bootstrap.py','owned_substrate.py','host_service.py',
                'performance_software_stages.py','performance_exact_controls.py','service_entry.py','g2_software_stages.py'):
        compile(out[name],name,'exec')
    return out
