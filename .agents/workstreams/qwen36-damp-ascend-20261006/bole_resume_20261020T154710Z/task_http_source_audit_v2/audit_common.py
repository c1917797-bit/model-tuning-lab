"""Whole-file source IO only; no network, device or application imports."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

P = Path(__file__).resolve().parent
HTTP_SHA = 'fa3a0f55304a53a3006c616cfdd3a1dc035b86c1a3d978f1aae8a334b02680ec'
DECODER_SHA = '248fe4f5ddd17cb9bad494d05e692ba0edee95fe4cb5c78bebcb58fc0a0a2129'
HORIZON = 1792597630
SECONDS = 600
MAX_FILE = 256 * 2**20
FORBIDDEN = {'torch', 'torch_npu', 'vllm', 'vllm_ascend', 'triton', 'transformers', 'tokenizers', 'numpy', 'tqdm'}


def need(value, why):
    if not value:
        raise ValueError(why)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def parse(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'no duplicate JSON keys')
            result[key] = value
        return result
    def bad(value):
        raise ValueError('nonfinite JSON ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


def ref(path):
    p = Path(path)
    need(p.is_absolute() and p.is_file() and not any(q.is_symlink() for q in (p, *p.parents)), 'ordinary absolute whole file')
    a = p.stat()
    need(p.suffix not in {'.safetensors', '.bin', '.pth'} and a.st_size <= MAX_FILE, 'bounded metadata/input; no checkpoint file')
    h = hashlib.sha256()
    size = 0
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            h.update(block)
            size += len(block)
    b = p.stat()
    need((a.st_ino, a.st_size, a.st_mtime_ns) == (b.st_ino, b.st_size, b.st_mtime_ns) and size == b.st_size, 'stable whole bytes')
    return dict(path=str(p), bytes=size, sha256=h.hexdigest())


def checked(value):
    need(type(value) is dict and set(value) in ({'path', 'sha256'}, {'path', 'bytes', 'sha256'}), 'exact Ref2/Ref3')
    actual = ref(value['path'])
    need(actual['sha256'] == value['sha256'] and ('bytes' not in value or value['bytes'] == actual['bytes']), 'exact complete file bytes')
    return Path(actual['path'])


def obj(value):
    return parse(checked(value).read_bytes())


def write(path, value):
    p = Path(path)
    need(p.is_absolute() and p.parent.is_dir() and not p.exists() and not any(q.is_symlink() for q in p.parents), 'new ordinary output')
    with p.open('xb') as stream:
        stream.write(canonical(value) + b'\n')
        stream.flush()
        os.fsync(stream.fileno())
    return ref(p)


def new_leaf(path):
    p = Path(path)
    need(p.is_absolute() and p.parent.is_dir() and not p.exists() and not any(q.is_symlink() for q in p.parents), 'absent ordinary leaf with existing parent')
    p.mkdir(mode=0o700)
    return p


def load(reference, name):
    need(name not in sys.modules, 'fresh exact source namespace ' + name)
    spec = importlib.util.spec_from_file_location(name, checked(reference))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        checked(reference)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def authority(reference, remaining):
    value = obj(reference)
    need(0 <= remaining <= SECONDS and value['start_epoch'] <= time.time()
         and time.time() + remaining < value['cutoff_epoch'] <= HORIZON, 'fresh authority within original horizon and finite remaining budget')
    return value


def verify_manifest(reference, root, expected_sha=None):
    path = checked(reference)
    need(path.parent == root and (expected_sha is None or reference['sha256'] == expected_sha), 'exact source-owned manifest and frozen parent')
    value = obj(reference)
    need(type(value['files']) is dict and value['files'], 'complete explicit file inventory')
    refs = [ref(path)]
    for name, row in value['files'].items():
        relative = Path(name)
        need(not relative.is_absolute() and '..' not in relative.parts, 'only explicit relative source files')
        actual = ref(root / relative)
        need((actual['bytes'], actual['sha256']) == (row['bytes'], row['sha256']), 'unchanged source file ' + name)
        refs.append(actual)
    return value, refs


class Inventory:
    """Counts explicit attachments, not hidden IO performed by frozen helpers."""
    def __init__(self):
        self.files = {}
        self.categories = {}
        self.attachments = 0

    def add(self, reference, category):
        actual = ref(checked(reference))
        prior = self.files.get(actual['path'])
        need(prior is None or prior == actual, 'no conflicting same-path reference')
        self.files[actual['path']] = actual
        self.categories.setdefault(category, set()).add(actual['path'])
        self.attachments += 1
        return actual

    def extend(self, references, category):
        for reference in references:
            self.add(reference, category)

    def snapshot(self):
        return {p: r['sha256'] for p, r in sorted(self.files.items())}

    def recheck(self):
        before = self.snapshot()
        for r in self.files.values():
            checked(r)
        need(before == self.snapshot(), 'complete immutable readset before/after')
        return before

    def counts(self):
        return dict(unique_files=len(self.files), unique_bytes=sum(r['bytes'] for r in self.files.values()),
                    explicit_ref_attachments=self.attachments, duplicate_ref_attachments=self.attachments-len(self.files),
                    category_unique_files={k: len(v) for k, v in sorted(self.categories.items())},
                    hidden_frozen_helper_IO_attempts_counted=False)


def install_read_only_import_guard():
    need(not any(k.split('.')[0] in FORBIDDEN for k in sys.modules), 'fresh stdlib-only audit process')
    attempts = []
    def hook(event, args):
        if event == 'import' and args and str(args[0]).split('.')[0] in FORBIDDEN:
            attempts.append(str(args[0]))
            raise RuntimeError('source-only getter forbids runtime import ' + str(args[0]))
        if event.startswith('socket.') or event in {'subprocess.Popen', 'os.system', 'os.fork', 'os.posix_spawn', 'os.exec'}:
            raise RuntimeError('source-only getter forbids process/network execution: ' + event)
    sys.addaudithook(hook)
    return attempts
