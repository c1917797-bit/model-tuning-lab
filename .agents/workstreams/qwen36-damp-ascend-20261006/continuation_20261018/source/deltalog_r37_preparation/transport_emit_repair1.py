"""Bounded read-only transport of the frozen R37 preparation algorithm.

No source tree, output, ledger or process is created. Authenticate the exact
preparer and patch Ref, compose in memory, then emit at most 128 KiB of JSON.
Every page names the same digest of the complete two-tree Ref inventory.
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

GENERATOR_BYTES = 16231
GENERATOR_SHA256 = 'e8b9d86268e4f59bd5818dcfa6603461f6e486e960551db67b3b01a4d8708837'
OUTPUT_CAP = 128 * 1024
FRAGMENT_CAP = 64 * 1024
INDEX_CAP = 64
SCHEMA = 'deltalog.r37-readonly-transport/v2'


def need(value, reason):
    if not value:
        raise ValueError(reason)


def wire(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       allow_nan=False, ensure_ascii=False) + '\n').encode('utf8')


def checked_generator(ref):
    need(type(ref) is dict and set(ref) == {'path', 'bytes', 'sha256'},
         'exact generator Ref3')
    need(ref['bytes'] == GENERATOR_BYTES and ref['sha256'] == GENERATOR_SHA256,
         'only the frozen reviewed preparation algorithm')
    path = Path(ref['path'])
    need(type(ref['path']) is str and path.is_absolute()
         and str(path) == ref['path'] and '..' not in path.parts
         and all(not p.is_symlink() for p in (path, *path.parents)),
         'ordinary exact generator source path')
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode), 'regular generator source')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(GENERATOR_BYTES + 1)
        after_fd = os.fstat(fd)
    finally:
        os.close(fd)
    after = path.lstat()
    key = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size,
                     s.st_mtime_ns, s.st_ctime_ns)
    need(key(before) == key(after_fd) == key(after)
         and len(raw) == GENERATOR_BYTES
         and hashlib.sha256(raw).hexdigest() == GENERATOR_SHA256,
         'complete stable frozen preparation source')
    return path, raw


def load_generator(ref):
    path, raw = checked_generator(ref)
    # Compile the authenticated source bytes directly: no bytecode cache or
    # ambient same-name module can substitute for this exact defining body.
    spec = importlib.util.spec_from_loader('_r37_frozen_transport_preparer', loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    checked_generator(ref)
    return module


def ref(path, raw):
    return dict(path=path, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def inventory(preparer, bundle):
    tree_aliases = {'model': preparer.MODEL_NEW, 'early': preparer.EARLY_NEW}
    need(set(bundle) == {'receipt', 'trees'}
         and set(bundle['trees']) == set(tree_aliases.values()),
         'exact frozen two-tree preparation return')
    old_model = json.loads(preparer.checked(preparer.M_OLD_REF))
    old_early = json.loads(preparer.checked(preparer.E_OLD_REF))
    old_trees = {'model': old_model, 'early': old_early}
    refs, entries = {}, {}
    for alias, root in sorted(tree_aliases.items()):
        refs[root], entries[alias] = {}, []
        tree = bundle['trees'][root]
        for name, content in sorted(tree.items()):
            path = Path(name)
            need(type(name) is str and name == str(path)
                 and not path.is_absolute() and '..' not in path.parts
                 and type(content) is str, 'exact UTF8 declared source leaf')
            raw = content.encode('utf8')
            current = ref(root + '/' + name, raw)
            refs[root][name] = current
            prior = old_trees[alias]['files'].get(name)
            if prior is None and name == 'SOURCE_TEMPLATE.json':
                prior = preparer.M_OLD_REF if alias == 'model' else preparer.E_OLD_REF
            same = prior if prior is not None and all(
                prior[k] == current[k] for k in ('bytes', 'sha256')) else None
            hint = 'copy-exact-original' if same is not None else (
                'utf8-file-batch' if len(raw) <= 60000 else 'fragments-then-one-patch')
            entries[alias].append(dict(relative_name=name, ref=current,
                                       unchanged_original_ref=same, transfer=hint))
    return tree_aliases, refs, entries


def response(args, preparer, bundle, generator_ref, patch_ref):
    aliases, refs, entries = inventory(preparer, bundle)
    package_material = dict(generator_ref=generator_ref, patch_manifest_ref=patch_ref,
                            all_file_refs=refs)
    package_id = hashlib.sha256(wire(package_material)).hexdigest()
    need(args.expected_package_id is None or args.expected_package_id == package_id,
         'same complete authenticated package across transport pages')
    value = dict(schema=SCHEMA, package_id=package_id,
                 generator_ref=generator_ref, patch_manifest_ref=patch_ref,
                 output_cap_bytes=OUTPUT_CAP, prepared_only=True,
                 model_source_created=False, NPU=False, qualified=False)
    if args.receipt:
        value.update(mode='receipt', receipt=bundle['receipt'], tree_roots=aliases,
                     file_counts={k: len(v) for k, v in entries.items()},
                     inventory_sha256=hashlib.sha256(wire(refs)).hexdigest())
        return value
    need(args.tree in aliases, 'explicit model or early tree required')
    root = aliases[args.tree]
    value.update(tree=args.tree, logical_root=root)
    if args.index:
        need(type(args.offset) is int and 0 <= args.offset < len(entries[args.tree])
             and 1 <= args.limit <= INDEX_CAP, 'bounded exact index page')
        page = entries[args.tree][args.offset:args.offset + args.limit]
        end = args.offset + len(page)
        value.update(mode='index', offset=args.offset, total=len(entries[args.tree]),
                     entries=page, next_offset=end if end < len(entries[args.tree]) else None)
        return value
    tree = bundle['trees'][root]
    if args.files:
        need(args.names_json is not None, 'explicit exact filename whitelist required')
        names = json.loads(args.names_json)
        need(type(names) is list and 0 < len(names) <= INDEX_CAP
             and all(type(name) is str and name in tree for name in names)
             and len(set(names)) == len(names), 'distinct declared filenames only')
        value.update(mode='files', files={name: dict(ref=refs[root][name],
                                                    utf8_content=tree[name]) for name in names})
        return value
    need(args.fragment and args.name in tree, 'one exact declared fragment filename')
    raw = tree[args.name].encode('utf8')
    need(0 <= args.byte_offset < len(raw)
         and 1 <= args.byte_count <= FRAGMENT_CAP, 'bounded exact original byte fragment')
    part = raw[args.byte_offset:args.byte_offset + args.byte_count]
    end = args.byte_offset + len(part)
    value.update(mode='fragment', relative_name=args.name, ref=refs[root][args.name],
                 byte_offset=args.byte_offset, fragment_bytes=len(part),
                 fragment_sha256=hashlib.sha256(part).hexdigest(),
                 base64=base64.b64encode(part).decode('ascii'),
                 next_byte_offset=end if end < len(raw) else None)
    return value


def emit(value):
    raw = wire(value)
    need(len(raw) <= OUTPUT_CAP,
         'transport page exceeds 128KiB; request fewer filenames or a 64KiB fragment')
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--receipt', action='store_true')
    mode.add_argument('--index', action='store_true')
    mode.add_argument('--files', action='store_true')
    mode.add_argument('--fragment', action='store_true')
    parser.add_argument('--generator-ref')
    parser.add_argument('--patch-manifest-ref')
    parser.add_argument('--expected-package-id')
    parser.add_argument('--tree', choices=('model', 'early'))
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--limit', type=int, default=32)
    parser.add_argument('--names-json')
    parser.add_argument('--name')
    parser.add_argument('--byte-offset', type=int, default=0)
    parser.add_argument('--byte-count', type=int, default=FRAGMENT_CAP)
    args = parser.parse_args()
    if not any((args.receipt, args.index, args.files, args.fragment)):
        emit(dict(schema=SCHEMA, enabled=False, read_only=True, NPU=False,
                  output_cap_bytes=OUTPUT_CAP, qualification=False))
        return 0
    need(args.generator_ref and args.patch_manifest_ref, 'exact two input source Refs required')
    generator_ref = json.loads(args.generator_ref)
    patch_ref = json.loads(args.patch_manifest_ref)
    preparer = load_generator(generator_ref)
    bundle = preparer.prepare(patch_ref, emit=True)
    value = response(args, preparer, bundle, generator_ref, patch_ref)
    # Repeat source authentication after composition; all original own-source
    # files were checked by the unchanged preparer during every invocation.
    checked_generator(generator_ref)
    emit(value)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, TypeError, OSError, UnicodeError) as error:
        emit(dict(schema=SCHEMA, error=type(error).__name__,
                  reason=str(error)[:3000], read_only=True, qualified=False))
        raise SystemExit(2)
