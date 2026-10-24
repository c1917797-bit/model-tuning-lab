"""Exact two-file GE window/identity derivation. No owner, ticket or execution."""
import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath

WORK = PurePosixPath('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
PARENT = WORK / 'good_enough_current_leaf_prepare_v1'
PREP = WORK / 'good_enough_layer37_renew_v2_20261024'
ROOT = PREP / 'prepared-source'
START, CUT = 1792828303, 1792914703
PARENTS = {
    'prepare_successor.py': dict(path=str(PARENT / 'prepare_successor.py'), bytes=12656, sha256='1b61e5336086610d40e01cc7ccbef30f7d29fdd1e445602fdec11339f41e61be'),
    'successor_bindings.py': dict(path=str(PARENT / 'successor_bindings.py'), bytes=4263, sha256='7444033ec7c606999a7c68643e82cb1385c17f46a1f20dadd6f85d65e3c5b6ed'),
}
WINDOW = dict(path=str(WORK / 'renew24_20261024T075143Z/BACKUP_PREPARATION_WINDOW_V1.json'), bytes=721, sha256='245827bb2bfef8f24d5d92116315a58847355230f01b745fa04067f6fd2f64f8')
OUTPUTS = {stage: '/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-RENEW24H_GEL37STABILITY_20261024_' + stage + '_V2' for stage in ('CPU', 'NPU')}


def need(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def once(source, before, after):
    need(source.count(before) == 1, 'exact GE renewal seam: ' + before[:80])
    return source.replace(before, after, 1)


def assignment(source, name, value):
    nodes = [n for n in ast.parse(source).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    need(len(nodes) == 1, 'one top-level assignment: ' + name)
    return once(source, ast.get_source_segment(source, nodes[0]), name + '=' + repr(value))


def adapt(files):
    need(type(files) is dict and set(files) == set(PARENTS), 'exact two original GE producer/gate files')
    for name, ref in PARENTS.items():
        need(type(files[name]) is bytes and len(files[name]) == ref['bytes'] and digest(files[name]) == ref['sha256'], 'exact reviewed original GE bytes: ' + name)
    out = {}
    for name, raw in files.items():
        s = raw.decode('utf-8')
        s = once(s, "PREP=WORK/'good_enough_current_leaf_prepare_v1'", "PREP=WORK/'good_enough_layer37_renew_v2_20261024'")
        s = once(s, '\nSTART,CUT=1792740953,1792827353\n', '\nSTART,CUT=1792828303,1792914703\n')
        s = assignment(s, 'WINDOW_REF' if name == 'prepare_successor.py' else 'WINDOW', WINDOW)
        if name == 'prepare_successor.py':
            s = once(s, "s=once(s,'START,CUT=1792226600,1792313000','START,CUT=1792740953,1792827353')", "s=once(s,'START,CUT=1792226600,1792313000','START,CUT=1792828303,1792914703')")
            s = once(s, "OWNER='ge-l37-current24h-20261023-v1'", "OWNER='ge-l37-renew24h-20261024-v2'")
            for stage in ('CPU', 'NPU'):
                s = once(s, 'run-mxr-event-single6-owned-main-CURRENT24H_GEL37STABILITY_' + stage + '_001', Path(OUTPUTS[stage]).name)
            s = once(s, 'prep=[PARENT_REF,WINDOW_REF,*parent[\'files\'].values(),', 'prep=[PARENT_REF,WINDOW_REF,*' + repr(list(PARENTS.values())) + ',*parent[\'files\'].values(),')
        need(s.endswith('\n\n') and not s.endswith('\n\n\n'), 'exact inherited final blank line')
        s = s[:-1]  # Explicit new-source EOF-only delta; frozen parents unchanged.
        compile(s, str(PREP / name), 'exec')
        out[name] = s.encode('utf-8')
    delta = dict(schema='ge.layer37-window-renewal-exact-two-file/v2', parents=PARENTS, preparation_window_ref=WINDOW,
                 changes={name: dict(before=files[name].decode('utf-8'), after=out[name].decode('utf-8')) for name in files},
                 device_execution=False, authority_created=False, numerical_qualification=False)
    return out, delta


def inverse(files, delta):
    need(type(files) is dict and set(files) == set(PARENTS) and delta['parents'] == PARENTS and delta['preparation_window_ref'] == WINDOW, 'exact renewal inverse domain')
    original = {}
    for name, ref in PARENTS.items():
        row = delta['changes'][name]
        need(files[name] == row['after'].encode('utf-8'), 'unchanged derived GE source')
        raw = row['before'].encode('utf-8')
        need(len(raw) == ref['bytes'] and digest(raw) == ref['sha256'], 'exact historical GE source restored')
        original[name] = raw
    return original


def read_parents():
    files = {}
    for name, ref in PARENTS.items():
        p = Path(ref['path'])
        need(p.is_absolute() and p.is_file() and not any(x.is_symlink() for x in (p, *p.parents)), 'ordinary original GE source')
        files[name] = p.read_bytes()
    return files


def main():
    p = argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument('--check', action='store_true')
    a = p.parse_args()
    if not a.check:
        print('{"enabled":false,"NPU":false,"authority_created":false}')
        return
    original = read_parents()
    out, delta = adapt(original)
    need(inverse(out, delta) == original, 'complete outer producer/gate inverse')
    print(json.dumps(dict(source_files=2, original_GE_files=62, expected_generated_files=64, exact_outer_inverse=True,
                          whole64_render_executed=False, sameimage96_executed=False, NPU=False, launch_ready=False)))


if __name__ == '__main__':
    main()
