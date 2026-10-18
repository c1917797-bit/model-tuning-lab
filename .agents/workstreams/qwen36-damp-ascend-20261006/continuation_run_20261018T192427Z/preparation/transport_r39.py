"""Bounded read-only pages of the exact frozen R39 preparation.

All three source trees are composed in memory, and no destination, output,
ledger or subprocess is opened. Every page binds the same complete package.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat

GENERATOR_BYTES = 35016
GENERATOR_SHA256 = '18d542f2286cd93d7e466cddb92f6ed2d07cf94a87efc4e9514e8d955b8f02e4'
OUTPUT_CAP = 128 * 1024
FRAGMENT_CAP = 64 * 1024
INDEX_CAP = 64
SCHEMA = 'deltalog.r39-readonly-transport/v1'


def need(value, reason):
    if not value:
        raise ValueError(reason)


def wire(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False, ensure_ascii=False) + '\n').encode('utf8')


def checked_generator(ref):
    need(type(ref) is dict and set(ref) == {'path', 'bytes', 'sha256'}, 'exact generator Ref3')
    need(ref['bytes'] == GENERATOR_BYTES and ref['sha256'] == GENERATOR_SHA256, 'only the frozen reviewed R39 preparation algorithm')
    path = Path(ref['path'])
    need(type(ref['path']) is str and path.is_absolute() and str(path) == ref['path']
         and '..' not in path.parts and all(not p.is_symlink() for p in (path, *path.parents)), 'ordinary exact generator source path')
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode), 'regular generator source')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(GENERATOR_BYTES + 1)
        opened = os.fstat(fd)
    finally:
        os.close(fd)
    after = path.lstat()
    key = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    need(key(before) == key(opened) == key(after) and len(raw) == GENERATOR_BYTES
         and hashlib.sha256(raw).hexdigest() == GENERATOR_SHA256, 'complete stable frozen R39 preparation source')
    return path, raw


def load_generator(ref):
    path, raw = checked_generator(ref)
    spec = importlib.util.spec_from_loader('_r39_frozen_transport_preparer', loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    checked_generator(ref)
    return module


def ref(path, raw):
    return dict(path=path, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def inventory(preparer, bundle):
    aliases = dict(model=preparer.MODEL_ROOT, early=preparer.EARLY_ROOT, payload=preparer.PAYLOAD_ROOT)
    need(set(bundle) == {'receipt', 'package_id', 'index', 'trees'}
         and set(bundle['trees']) == set(aliases.values()) and set(bundle['index']) == set(aliases), 'exact complete frozen three-tree return')
    need(hashlib.sha256(preparer.serial(dict(receipt=bundle['receipt'], index=bundle['index']))).hexdigest() == bundle['package_id'], 'whole complete package digest')
    refs, entries = {}, {}
    for alias, root in sorted(aliases.items()):
        refs[root], entries[alias] = {}, []
        rows = bundle['index'][alias]
        tree = bundle['trees'][root]
        need([row['relative_name'] for row in rows] == sorted(tree), 'exact complete sorted file inventory')
        for row in rows:
            name = row['relative_name']; content = tree[name]; path = Path(name)
            need(type(name) is str and str(path) == name and not path.is_absolute()
                 and '..' not in path.parts and type(content) is str, 'exact UTF8 source leaf')
            raw = content.encode('utf8'); current = ref(root + '/' + name, raw)
            need(set(row) == {'relative_name', 'ref', 'unchanged_original_ref'} and row['ref'] == current, 'whole indexed actual source bytes')
            refs[root][name] = current
            original = row['unchanged_original_ref']
            if original is not None:
                need(type(original) is dict and set(original) == {'path', 'bytes', 'sha256'}
                     and all(original[k] == current[k] for k in ('bytes', 'sha256')), 'unchanged exact source copy bytes')
            entry = dict(row)
            entry['transfer'] = 'copy-exact-original' if original is not None else ('utf8-file-batch' if len(raw) <= 60000 else 'fragments-then-one-patch')
            entries[alias].append(entry)
    return aliases, refs, entries


def response(args, preparer, bundle, generator_ref):
    aliases, refs, entries = inventory(preparer, bundle)
    package_id = bundle['package_id']
    need(args.receipt or args.expected_package_id is not None, 'data pages require the reviewed receipt package_id')
    need(args.expected_package_id is None or args.expected_package_id == package_id, 'same full immutable package across transport pages')
    value = dict(schema=SCHEMA, package_id=package_id, generator_ref=generator_ref,
                 output_cap_bytes=OUTPUT_CAP, prepared_only=True, read_only=True,
                 model_source_created=False, early_bound_source_created=False, NPU=False, qualified=False)
    if args.receipt:
        value.update(mode='receipt', receipt=bundle['receipt'], tree_roots=aliases,
                     file_counts={k: len(v) for k, v in entries.items()},
                     inventory_sha256=hashlib.sha256(wire(refs)).hexdigest(),
                     index_sha256=hashlib.sha256(preparer.serial(bundle['index'])).hexdigest())
        value['structured_patch_entries'] = {
            alias: [entry for entry in rows if entry['unchanged_original_ref'] is None
                    or Path(entry['relative_name']).name in {'SOURCE_TEMPLATE.json', 'SOURCE_MANIFEST.json', 'SOURCE_BOUND.json'}
                    or Path(entry['relative_name']).name.startswith('COMMANDS')]
            for alias, rows in entries.items()}
        return value
    need(args.tree in aliases, 'explicit model, early or payload tree required')
    root = aliases[args.tree]
    value.update(tree=args.tree, logical_root=root)
    if args.index:
        need(type(args.offset) is int and 0 <= args.offset < len(entries[args.tree]) and 1 <= args.limit <= INDEX_CAP, 'bounded exact inventory page')
        page = entries[args.tree][args.offset:args.offset + args.limit]
        end = args.offset + len(page)
        value.update(mode='index', offset=args.offset, total=len(entries[args.tree]), entries=page,
                     next_offset=end if end < len(entries[args.tree]) else None)
        return value
    tree = bundle['trees'][root]
    if args.files:
        need(args.names_json is not None, 'explicit exact filename whitelist required')
        names = json.loads(args.names_json)
        need(type(names) is list and 0 < len(names) <= INDEX_CAP and len(set(names)) == len(names)
             and all(type(name) is str and name in tree for name in names), 'distinct declared filenames only')
        value.update(mode='files', files={name: dict(ref=refs[root][name], utf8_content=tree[name]) for name in names})
        return value
    need(args.fragment and args.name in tree, 'one exact declared fragment filename')
    raw = tree[args.name].encode('utf8')
    need(type(args.byte_offset) is int and 0 <= args.byte_offset < len(raw)
         and 1 <= args.byte_count <= FRAGMENT_CAP, 'bounded exact source byte fragment')
    part = raw[args.byte_offset:args.byte_offset + args.byte_count]
    end = args.byte_offset + len(part)
    value.update(mode='fragment', relative_name=args.name, ref=refs[root][args.name],
                 byte_offset=args.byte_offset, fragment_bytes=len(part),
                 fragment_sha256=hashlib.sha256(part).hexdigest(), base64=base64.b64encode(part).decode('ascii'),
                 next_byte_offset=end if end < len(raw) else None)
    return value


def emit(value):
    raw = wire(value)
    need(len(raw) <= OUTPUT_CAP, 'transport page exceeds128KiB; use fewer files or64KiB fragments')
    sys.stdout.buffer.write(raw); sys.stdout.buffer.flush()


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--receipt', action='store_true'); mode.add_argument('--index', action='store_true')
    mode.add_argument('--files', action='store_true'); mode.add_argument('--fragment', action='store_true')
    parser.add_argument('--generator-ref'); parser.add_argument('--expected-package-id')
    parser.add_argument('--tree', choices=('model', 'early', 'payload'))
    parser.add_argument('--offset', type=int, default=0); parser.add_argument('--limit', type=int, default=32)
    parser.add_argument('--names-json'); parser.add_argument('--name')
    parser.add_argument('--byte-offset', type=int, default=0); parser.add_argument('--byte-count', type=int, default=FRAGMENT_CAP)
    args = parser.parse_args()
    if not any((args.receipt, args.index, args.files, args.fragment)):
        emit(dict(schema=SCHEMA, enabled=False, read_only=True, output_cap_bytes=OUTPUT_CAP, NPU=False, qualified=False))
        return 0
    need(args.generator_ref, 'exact frozen R39 preparation Ref required')
    generator_ref = json.loads(args.generator_ref)
    preparer = load_generator(generator_ref)
    bundle = preparer.prepare()
    value = response(args, preparer, bundle, generator_ref)
    checked_generator(generator_ref)
    emit(value)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, TypeError, OSError, UnicodeError) as error:
        emit(dict(schema=SCHEMA, error=type(error).__name__, reason=str(error)[:3000], read_only=True, qualified=False))
        raise SystemExit(2)
