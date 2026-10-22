"""Pure exact consumer delta, no source binding or execution. Explicit --check only."""
import ast
import hashlib
from pathlib import Path

OLD="""        for name,current in(('GDN',frame['before_GDN']),('FA',frame['before_FA'])):
            old={r['layer']:r for r in previous['after_'+name]}
            for r in current:
                for key in(('native_state','full_conv_slot')if name=='GDN'else('key','value')):
                    N.equal(t,r[key],old[r['layer']][key],'next actual before-image equals previous actual postimage')"""
NEW="""        old_g={r['layer']:r for r in previous['after_GDN']}
        for r in frame['before_GDN']:
            for key in('native_state','full_conv_slot'):
                N.equal(t,r[key],old_g[r['layer']][key],'next actual before-image equals previous actual postimage')
        import long_gate_primitives as LONG
        C.need(C.ref(LONG.__file__)==m['files']['long_gate_primitives.py'],'actual source-bound long page-continuity helper')
        old_f={r['layer']:r for r in previous['after_FA']}
        for r in frame['before_FA']:
            LONG.page_transition(old_f[r['layer']],r,previous['owner'],owner,
                previous['publication']['next_length'],previous['publication']['next_version'],
                equal_page=lambda a,b,why:N.equal(t,a,b,why))"""


def render(original):
    if original.count(OLD)!=1:raise ValueError('one exact original continuity block')
    successor=original.replace(OLD,NEW,1)
    if successor.replace(NEW,OLD,1)!=original:raise ValueError('exact inverse consumer delta')
    ast.parse(successor)
    return successor


def check():
    p=Path(__file__).resolve().parent.parent/'fastpath_numeric_bridge_prepare_v1/fastpath_numeric_consumer.py'
    text=p.read_text();out=render(text)
    return dict(original_sha256=hashlib.sha256(text.encode()).hexdigest(),
        successor_sha256=hashlib.sha256(out.encode()).hexdigest(),exact_inverse=True,
        original_math_reference_and_threshold_bytes_unchanged=True,
        source_binding_pending=True,NPU_executed=False,execution_ready=False)


if __name__=='__main__':
    import json,sys
    if sys.argv[1:]!=['--check']:raise SystemExit('default OFF: source-only --check')
    print(json.dumps(check(),sort_keys=True))
