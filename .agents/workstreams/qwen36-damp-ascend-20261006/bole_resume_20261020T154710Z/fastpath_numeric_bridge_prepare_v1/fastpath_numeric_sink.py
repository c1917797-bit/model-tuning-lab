"""Bounded short-smoke sink. No owner/controller/process creation. Long streaming stays pending."""
from pathlib import Path
import os
import json

_CONTEXT=None


def logical_bytes(t,value):
    if isinstance(value,t.Tensor):return value.numel()*value.element_size()
    if type(value)is dict:return sum(logical_bytes(t,x)for x in value.values())
    if type(value)in(list,tuple):return sum(logical_bytes(t,x)for x in value)
    if value is None or type(value)in(str,int,float,bool):return 0
    raise TypeError('unbounded qualification export operand')


def durable(C,path,value):
    ref=C.write(path,value)
    # sourceio.write is exclusive but not fsync. A consumed raw must not be
    # released until both its exact report and directory entry are durable.
    fd=os.open(C.checked(ref),os.O_RDONLY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)
    fd=os.open(Path(path).parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)
    return ref


def metadata(c,path,value):
    raw=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
    c['C'].need(len(raw)<=256*2**10 and c['metadata_bytes']+len(raw)<=64*2**20 and
                c['used']+c['metadata_bytes']+len(raw)<=2**30,
                'complete qualification JSON charged before write to fixed metadata/raw budget')
    ref=durable(c['C'],path,value)
    c['C'].need(ref['bytes']==len(raw),'actual exact charged qualification metadata bytes')
    c['metadata_bytes']+=ref['bytes']
    return ref


def configure(t,C,source,m,rank):
    global _CONTEXT
    C.need(m['fastpath_numeric_qualification']['output_tokens']==8,
           'short8 only; longer qualification needs original bounded streaming integration')
    if _CONTEXT is not None:
        C.need(_CONTEXT['source']==source and _CONTEXT['m']==m and _CONTEXT['rank']==rank,
               'same actual source/rank may reuse its bounded sink for generation2')
        return sink
    root=Path(m['model_receipt_root'])/('FASTPATH-NUMERIC-R%d'%rank)
    C.need(root.parent.is_dir()and not root.exists(),'fresh actual owned qualification leaf')
    root.mkdir(mode=0o700)
    _CONTEXT=dict(t=t,C=C,source=source,m=m,rank=rank,root=root,used=0,metadata_bytes=0,previous=None)
    return sink


def sink(frame):
    c=_CONTEXT
    if c is None:raise ValueError('actual source-bound qualification sink not configured')
    t,C,m,source=c['t'],c['C'],c['m'],c['source']
    import diagnostic_export as X
    import fastpath_numeric_consumer as N
    C.need(C.ref(__file__)==m['files']['fastpath_numeric_sink.py']and
           C.ref(X.__file__)==m['files']['diagnostic_export.py']and
           C.ref(N.__file__)==m['files']['fastpath_numeric_consumer.py'],
           'actual complete source-owned exporter and independent consumer')
    logical=logical_bytes(t,frame)
    C.need(c['used']+2*logical+128*2**20+64*2**20<=2**30,
           'retained raw plus two current copies/checkpoint/metadata inside original1GiB')
    raw=X.export(t,frame,cap_bytes=384*2**20)
    C.need(raw['logical_tensor_bytes']==logical,'same complete logical size before allocation and after export')
    stem='G%d-O%d'%(frame['generation'],frame['ordinal'])
    path=c['root']/(stem+'.pt')
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:
        t.save(raw,stream);stream.flush();os.fsync(stream.fileno())
    ref=C.ref(path)
    C.need(c['used']+ref['bytes']<=2**30,'short-smoke actual wire evidence inside original1GiB per rank')
    c['used']+=ref['bytes']
    # Reopen the actual saved primitive/CPU tensor evidence before independent
    # numerical consumption; never consume synthetic replacements or saved PASS.
    saved=t.load(C.checked(ref),map_location='cpu',weights_only=True)
    C.need(saved['schema']=='bole.model-diagnostic-primitives/v1'and
           saved['logical_tensor_bytes']==logical,'complete actual saved bounded frame')
    previous=c['previous']
    if previous is not None and previous['owner']['generation']!=frame['generation']:previous=None
    report=N.consume_frame(t,C,m,source,saved['payload'],previous=previous)
    report.update(actual_frame=ref,logical_tensor_bytes=logical,raw_retained_during_consumption=True)
    report_ref=metadata(c,c['root']/(stem+'.json'),report)
    current=saved['payload']
    c['previous']={k:current[k]for k in('owner','publication','after_GDN','after_FA')}
    # Same durable-independent-consumption-before-release ordering as original
    # G2. Keep one complete first frame per rank; preserve every failed frame.
    # No foreign/previous path is eligible: this call exclusively created path.
    retained=frame['generation']==1 and frame['ordinal']==0
    C.checked(report_ref);C.checked(ref)
    if not retained:
        C.need(path.parent==c['root']and path.name==stem+'.pt','only this owned consumed frame')
        path.unlink();c['used']-=ref['bytes']
    metadata(c,c['root']/(stem+'-RELEASE.json'),dict(source=source,actual_frame=ref,
        report=report_ref,retained=retained,released_after_independent_consumption=not retained,
        successful_raw_replay_available=retained,numerical_qualified=False,formal_performance=False))
    return dict(schema='bole.actual-fastpath-numeric-frame-ack/v1',source=source,rank=c['rank'],
        generation=frame['generation'],ordinal=frame['ordinal'],frame_checks_passed=True,
        actual_frame=ref,report=report_ref,formal_performance=False)
