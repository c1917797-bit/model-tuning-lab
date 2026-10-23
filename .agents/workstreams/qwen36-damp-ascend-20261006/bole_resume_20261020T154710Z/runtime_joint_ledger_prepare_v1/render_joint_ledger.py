"""Exact reversible taps into the full existing FAST sink; default OFF library."""
from pathlib import Path
HERE = Path(__file__).resolve().parent


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('one actual joint-ledger seam: ' + old[:100])
    return text.replace(old, new, 1)


def adapt(files):
    original = files['fastpath_numeric_sink.py']
    s = original.decode() if type(original) is bytes else original
    if 'runtime_joint_ledger.py' in files:
        raise ValueError('joint ledger already applied')
    s = once(s, 'import json\n', 'import json\nimport runtime_joint_ledger as J\n')
    marker = '    logical=logical_bytes(t,frame)'
    s = once(s, marker, marker + '\n    joint=J.get(c)\n    joint.pre_export(frame,logical)')
    old = """    with os.fdopen(fd,'wb')as stream:
        t.save(raw,stream);stream.flush();os.fsync(stream.fileno())"""
    new = """    try:
        with os.fdopen(fd,'wb')as stream:
            bounded=joint.writer(stream)
            try:
                t.save(raw,bounded);bounded.flush()
            finally:
                stream.flush();os.fsync(stream.fileno())
    except Exception as serialization_error:
        joint.serialization_failed(path,serialization_error)"""
    s = once(s, old, new)
    s = once(s, '    ref=C.ref(path)', '    joint._dirsync(path)\n    ref=C.ref(path)\n    joint.after_wire(ref)')
    s = once(s, "    saved=t.load(C.checked(ref),map_location='cpu',weights_only=True)",
        "    joint.before_reload()\n    saved=t.load(C.checked(ref),map_location='cpu',weights_only=True)")
    s = once(s, "    metadata(c,c['root']/(stem+'-RELEASE.json'),dict(",
        "    release_ref=metadata(c,c['root']/(stem+'-RELEASE.json'),dict(")
    s = once(s, "    return dict(schema='bole.actual-fastpath-numeric-frame-ack/v1',",
        "    joint.ack_release(retained,report_ref,release_ref)\n    return dict(schema='bole.actual-fastpath-numeric-frame-ack/v1',")
    out = dict(files)
    out['fastpath_numeric_sink.py'] = s.encode() if type(original) is bytes else s
    raw = (HERE/'runtime_joint_ledger.py').read_bytes()
    out['runtime_joint_ledger.py'] = raw if type(original) is bytes else raw.decode()
    for n, b in out.items():
        if n.endswith('.py'):
            compile(b, n, 'exec')
    return out, dict(original_sink=original, after_sink=out['fastpath_numeric_sink.py'],
                     helper=out['runtime_joint_ledger.py'], added='runtime_joint_ledger.py')


def inverse(files, delta):
    out = dict(files)
    if (delta['added'] != 'runtime_joint_ledger.py' or
            out['fastpath_numeric_sink.py'] != delta['after_sink'] or
            out['runtime_joint_ledger.py'] != delta['helper']):
        raise ValueError('exact joint-ledger inverse addition')
    del out['runtime_joint_ledger.py']
    out['fastpath_numeric_sink.py'] = delta['original_sink']
    return out
