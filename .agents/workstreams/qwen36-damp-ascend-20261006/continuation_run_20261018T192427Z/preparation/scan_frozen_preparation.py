"""Read-only full-source clock/authority inventory for the next batch.

Compose the frozen R38 preparation in memory, then scan all declared Python
sources in model, early and the original payload. No source tree, output,
ledger, subprocess, Torch or model is created. Findings are observations,
never permission to rewrite every matching historical reference.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import types

GENERATOR_BYTES = 23738
GENERATOR_SHA = 'ad622334b9d3d5df0c225f687f23a67c00af93ed5b1a9e185df1a9e2678d1648'
PATCH_REF = dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-r37-preparation-MAIN-renew24h-20261018-001/PATCHES.json', bytes=1885, sha256='0bd70da9feea656e0146853d90078fcd3e7684c6ec42551129b3738edfc18b1f')
PAYLOAD_REF = dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-selected-firstdecode-renew24h-20261018-001-r36-all4-publication/SOURCE_MANIFEST.json', bytes=22730, sha256='75330c840e308aa9946a729f8a0948b39f13f213e9a1bcf3560f25a9560a50b4')
PATTERN = re.compile(r'1792226600|1792313000|2026-10-18T08:43:20|20261017_084320|cdba34641b429a6132e7af5a6a88a93b63faf7d0834a9313a8b948e2a4907b6d|442cb693c1724834238779a0179b2667776f2d2f2ce5c48ee63850f18dcc3d7c|explicit-renewed24h|renewed24h\.historical-artifact-reuse')
CAP = 128 * 1024


def need(value, reason):
    if not value:
        raise ValueError(reason)


def ref(path, raw):
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def checked(value):
    need(type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}, 'exact Ref3')
    path = Path(value['path'])
    need(type(value['bytes']) is int and 0 < value['bytes'] <= 4 * 2**20
         and path.is_absolute() and str(path) == value['path'] and '..' not in path.parts
         and not any(p.is_symlink() for p in (path, *path.parents)), 'bounded ordinary source')
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode), 'regular source')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        with os.fdopen(fd, 'rb', closefd=False) as handle:
            raw = handle.read(value['bytes'] + 1)
        opened = os.fstat(fd)
    finally:
        os.close(fd)
    after = path.lstat()
    key = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    need(key(before) == key(opened) == key(after) and ref(path, raw) == value, 'complete stable source Ref')
    return raw


def scan_tree(alias, root, tree):
    findings = []
    count = 0
    for name, raw in sorted(tree.items()):
        if not name.endswith('.py'):
            continue
        parsed = ast.parse(raw)
        count += 1
        lines = raw.decode('utf8').splitlines()
        hits = []
        for index, line in enumerate(lines, 1):
            tokens = sorted(set(PATTERN.findall(line)))
            if tokens:
                hits.append(dict(line=index, tokens=tokens,
                                 excerpt=line[:240], excerpt_truncated=len(line) > 240))
        if hits:
            findings.append(dict(tree=alias, name=name, ref=ref(root + '/' + name, raw),
                                 top_level_functions=[n.name for n in parsed.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
                                 hits=hits))
    return count, findings


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--scan', action='store_true')
    parser.add_argument('--generator-ref')
    args = parser.parse_args()
    if not args.scan:
        print('{"enabled":false,"read_only":true,"NPU":false,"qualified":false}')
        return 0
    need(args.generator_ref is not None, 'exact frozen R38 generator Ref required')
    generator_ref = json.loads(args.generator_ref)
    need(generator_ref['bytes'] == GENERATOR_BYTES and generator_ref['sha256'] == GENERATOR_SHA,
         'only exact frozen R38 preparation source')
    raw = checked(generator_ref)
    generator = types.ModuleType('_read_only_r38_clock_inventory')
    generator.__file__ = generator_ref['path']
    exec(compile(raw, generator.__file__, 'exec'), generator.__dict__)
    checked(generator_ref)
    bundle = generator.prepare(PATCH_REF, emit=True)
    payload = json.loads(checked(PAYLOAD_REF))
    need(payload['root'] == str(Path(PAYLOAD_REF['path']).parent), 'original exact payload root')
    trees = {'model': (generator.MODEL_NEW, {n: body.encode('utf8') for n, body in bundle['trees'][generator.MODEL_NEW].items()}),
             'early': (generator.EARLY_NEW, {n: body.encode('utf8') for n, body in bundle['trees'][generator.EARLY_NEW].items()}),
             'payload': (payload['root'], generator.own_bytes(payload))}
    counts = {}
    findings = []
    for alias, (root, tree) in trees.items():
        counts[alias], rows = scan_tree(alias, root, tree)
        findings.extend(rows)
    checked(generator_ref)
    checked(PATCH_REF)
    checked(PAYLOAD_REF)
    result = dict(schema='deltalog.continuation-frozen-clock-inventory/v1',
                  generator_ref=generator_ref, patch_ref=PATCH_REF, payload_ref=PAYLOAD_REF,
                  predecessor_receipt=bundle['receipt'], python_counts=counts,
                  matching_file_count=len(findings), findings=findings,
                  read_only=True, source_tree_created=False, NPU=False, qualified=False)
    body = (json.dumps(result, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode('utf8')
    need(len(body) <= CAP, 'bounded 128KiB inventory; never truncate findings')
    sys.stdout.buffer.write(body)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
