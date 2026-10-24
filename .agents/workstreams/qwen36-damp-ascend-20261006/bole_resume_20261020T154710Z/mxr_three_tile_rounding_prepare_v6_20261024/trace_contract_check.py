"""CPU-only actual Trace contract regression; no Torch/NPU imports."""
import ast,contextlib,io,json
from pathlib import Path
def need(v,s):
    if not v:raise ValueError(s)
def check(source):
    from rounding_stage_trace import Trace
    from wu_stage_trace import Trace as OldTrace
    capture=(Path(__file__).parent/'rounding_capture.py').read_bytes()
    tree=ast.parse(capture);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='run')
    tiles=next(n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='TILES'for t in n.targets))
    tiles=ast.literal_eval(tiles.value);need(tiles==((0,0),(3,2),(19,5)),'actual capture tile identities')
    calls=[n for n in ast.walk(fn)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and isinstance(n.func.value,ast.Name)and n.func.value.id=='trace'and n.func.attr=='stage']
    need(len(calls)==4,'all actual syntactic trace call sites')
    actual=[]
    for call in calls:
        need(len(call.args)==4 and not call.keywords,'actual four-position trace ABI')
        vals=[]
        for n in call.args:
            if isinstance(n,ast.Name):
                need(n.id=='c','only declared selected-tile trace variable');vals.append('_tile_chunk')
            else:vals.append(ast.literal_eval(n))
        if '_tile_chunk'in vals:
            need(vals==['serialize','saved_candidate','_tile_chunk','precast'],'actual selected-tile serializer trace')
            actual.extend(tuple(c if x=='_tile_chunk'else x for x in vals)for c,h in tiles)
        else:actual.append(tuple(vals))
    expected=[(s,'saved_candidate',None,'precast')for s in('h2d','call','sync')]+[('serialize','saved_candidate',c,'precast')for c in(0,3,19)]
    need(set(actual)==set(expected)and len(actual)==len(expected),'exact complete6 calls, no unknown expansion')
    negatives=[]
    def refuse(args,label,trace=None):
        t=Trace(source)if trace is None else trace
        try:
            with t.stage(*args):pass
        except ValueError:negatives.append(label);return
        raise ValueError('incorrectly accepted '+label)
    with contextlib.redirect_stdout(io.StringIO()):
        t=Trace(source)
        for args in expected:
            with t.stage(*args):pass
        need(len(t.events)==12 and not t.active and not t.failed,'all actual positive calls emit bounded complete events')
        need(all(r['schema']=='mxr.native2048-three-tile-rounding-stage/v1'and r['qualification']is r['performance']is False for r in t.events),'diagnostic-only trace identity')
        for args,label in[
            (('cpu_reference','saved_candidate',None,'precast'),'old-only stage'),
            (('unknown','saved_candidate',None,'precast'),'unknown stage'),
            (('call','foreign',None,'precast'),'unknown arm'),
            (('call','saved_candidate',31,'precast'),'wrong whole-scope chunk'),
            (('call','saved_candidate',True,'precast'),'bool whole-scope chunk'),
            (('serialize','saved_candidate',None,'precast'),'missing tile'),
            (('serialize','saved_candidate',31,'precast'),'old-only tile'),
            (('serialize','saved_candidate',True,'precast'),'bool tile'),
            (('call','saved_candidate',None,'original'),'old-only variant'),
            (('h2d','saved_candidate',None,None),'missing variant'),
            ((True,'saved_candidate',None,'precast'),'non-string stage')]:
            refuse(args,label)
        with Trace(source).stage('h2d','saved_candidate',None,'precast') as unused:
            # Explicit nested state uses the same actual trace instance below.
            pass
        nested=Trace(source)
        with nested.stage('h2d','saved_candidate',None,'precast'):
            refuse(('call','saved_candidate',None,'precast'),'nested stage',nested)
        failed=Trace(source)
        try:
            with failed.stage('call','saved_candidate',None,'precast'):raise RuntimeError('real body exception')
        except RuntimeError:pass
        need(failed.failed and not failed.active and [r['state']for r in failed.events]==['start','error'],'original exception/state preserved')
        refuse(('call','saved_candidate',None,'precast'),'failed trace retry',failed)
        cap=Trace(source)
        for _ in range(32):
            with cap.stage('h2d','saved_candidate',None,'precast'):pass
        refuse(('call','saved_candidate',None,'precast'),'event cap',cap)
        need(len(cap.events)==64,'unchanged64 cap')
        refuse(('h2d','saved_candidate',None,'precast'),'record byte cap',Trace({'oversize':'x'*3000}))
        old=OldTrace(source)
        with old.stage('h2d','saved_candidate',31,None):pass
        with old.stage('call','saved_candidate',31,'original'):pass
        try:
            with OldTrace(source).stage('h2d','saved_candidate',None,'precast'):pass
        except ValueError:pass
        else:raise ValueError('original pre-fix refusal must remain')
    return dict(schema='mxr.three-tile-actual-trace-contract/v1',source=source,positive_calls=6,negative_controls=len(negatives),
        actual_classes=True,complete_source_call_sites=True,old_trace_preserved=True,events=12,event_cap=64,record_cap=2048,
        NPU=False,qualification=False,performance=False)
