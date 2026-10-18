"""Source-bound repaired CPU reader, with original data and opt prewrite gates."""
import argparse
import hashlib
import importlib.util
import json
import os
import stat
import sys
from pathlib import Path


def need(value, message):
    if not value:
        raise ValueError(message)


def checked(value):
    need(type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}, 'exact bootstrap Ref3')
    path = Path(value['path'])
    before = path.lstat()
    need(path.is_absolute() and stat.S_ISREG(before.st_mode) and not any(p.is_symlink() for p in (path, *path.parents)), 'ordinary exact consumer bootstrap file')
    body = path.read_bytes()
    after = path.lstat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    need(identity(before) == identity(after) and len(body) == value['bytes'] and hashlib.sha256(body).hexdigest() == value['sha256'], 'actual immutable consumer bootstrap bytes')
    return path, body


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--execute', action='store_true')
    names = ('consumer-source-ref', 'model-source-ref', 'payload-source-ref', 'owner-ref', 'inspect-ref', 'loaded-ref', 'reports-ref', 'geometry-refs-ref')
    for name in names:
        parser.add_argument('--' + name)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(enabled=False, NPU=False, qualified=False)))
        return 0
    need(all(getattr(args, name.replace('-', '_')) is not None for name in names), 'complete actual consumer/model/payload/evidence CLI')
    values = [json.loads(getattr(args, name.replace('-', '_'))) for name in names]
    consumer_ref, model_ref, payload_ref, owner_ref, inspect_ref, loaded_ref, reports_ref, geometry_ref = values
    _, manifest_body = checked(consumer_ref)
    manifest = json.loads(manifest_body)
    host_path, _ = checked(manifest['files']['host_consumer.py'])
    spec = importlib.util.spec_from_file_location('_source_bound_geometry_consumer_host', host_path)
    need(spec is not None and spec.loader is not None, 'declared independent consumer verifier')
    host = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = host
    spec.loader.exec_module(host)
    source = host.consumer_source(consumer_ref)
    need(Path(__file__).resolve() == host.checked(source['files']['postconsume_entry_new.py']), 'actual new consumer entry, never an old model file')
    need(source['model_source'] == model_ref and source['payload_source'] == payload_ref, 'exact original model/payload source relation')
    need(sys.platform == 'linux' and os.environ.get('ASCEND_RT_VISIBLE_DEVICES') == '' and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD') == '0' and not list(Path('/dev').glob('davinci*')), 'actual Devices-empty CPU guest')
    model, _ = host.original_model(source)
    host.old_output_absent(model)
    host.geometry_readset(consumer_ref, source, dict(reports_ref=reports_ref), geometry_ref)
    cli = host.module(source['files']['consumer_cli.py'], '_source_bound_geometry_consumer_cli')
    value = cli.consume(consumer_ref, model_ref, payload_ref, owner_ref, inspect_ref, loaded_ref, reports_ref, geometry_ref)
    need(value['consumer_source'] == consumer_ref and value['model_source'] == model_ref and value['source'] == payload_ref and value['geometry_refs_ref'] == geometry_ref and value['repair_scope'] == 'geometry-control-accounting-only', 'new reader provenance with unchanged original data identities')
    need(value['schema'] == 'deltalog.independent-all4-firstdecode/v1' and value['full_model_qualified'] is value['performance_qualified'] is value['task_qualified'] is False, 'independent diagnostic result contract')
    need(args.output == Path('/adakv-results/FIRST-DECODE-INDEPENDENT.json'), 'one exact owned CPU output')
    host.consumer_source(consumer_ref)
    host.old_output_absent(model)
    body = (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()
    import ipc_controls
    scanner = ipc_controls.load_scanner()
    used = 0
    for root in (model['output_root'], source['output_root']):
        root = Path(root)
        observation = scanner.scan(root, socket_parent=[root / name for name in ('cpu-preflight', 'candidate', 'cpu-consumer')], ipc_source=scanner.IPC_SOURCE)
        used += scanner.consume(observation, root)
    host.old_output_absent(model)
    need(used + len(body) + 64 * 2**20 <= 2 * 2**30, 'same combined opt2GiB and terminal64MiB before CPU result write')
    with args.output.open('xb') as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps(dict(path=args.output.as_posix(), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())))
    return 0 if value['diagnostic_complete'] else 3


if __name__ == '__main__':
    raise SystemExit(main())
