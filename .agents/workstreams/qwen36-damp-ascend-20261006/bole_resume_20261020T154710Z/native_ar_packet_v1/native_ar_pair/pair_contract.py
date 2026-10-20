"""Pure helpers for an untimed, default-OFF actual native AR/BOLE identity pair."""
import hashlib
import importlib.util
import json
from pathlib import Path

SCOPE = dict(schema='bole.actual-native-ar-bole-token-pair/v1', prefix=131,
             request_count=2, output_tokens=2, concurrency=1,
             ignore_eos=True, normal_EOS_qualified=False)
AR_HTTP = 'bole.actual-native-ar-smoke-HTTP/v1'
AR_RAW = 'bole.actual-native-ar-smoke-rank/v1'
CAP = 2**30
PROFILE = dict(endpoint='/v1/completions', prompt_count=1, n=1,
               beam_search=False, streaming_input=False)


def need(value, message):
    if not value:
        raise ValueError(message)


def ref(path):
    p = Path(path)
    need(p.is_absolute() and p.is_file() and not any(x.is_symlink() for x in (p, *p.parents)),
         'ordinary absolute evidence file')
    before = p.stat()
    digest, count = hashlib.sha256(), 0
    with p.open('rb') as f:
        for block in iter(lambda: f.read(2**20), b''):
            digest.update(block)
            count += len(block)
    after = p.stat()
    need((before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_ino, after.st_size, after.st_mtime_ns) and count == after.st_size,
         'stable exact evidence bytes')
    return dict(path=str(p), bytes=count, sha256=digest.hexdigest())


def checked(value):
    need(type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}
         and ref(value['path']) == value, 'exact ordinary Ref3')
    return Path(value['path'])


def obj(value):
    return json.loads(checked(value).read_bytes())


def write(path, value):
    with Path(path).open('x', encoding='utf8', newline='\n') as f:
        json.dump(value, f, sort_keys=True, allow_nan=False)
        f.write('\n')
    return ref(Path(path).resolve())


def load(reference, name):
    spec = importlib.util.spec_from_file_location(name, checked(reference))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def native_argv(on_argv):
    """One declared algorithm delta; no opportunistic common-option edits."""
    need(type(on_argv) is list and all(type(x) is str for x in on_argv)
         and on_argv.count('--speculative-config') == 1, 'one source-bound ON MTP option')
    position = on_argv.index('--speculative-config')
    need(position + 1 < len(on_argv) and json.loads(on_argv[position + 1]) ==
         dict(method='mtp', num_speculative_tokens=8), 'exact declared BOLE MTP8 algorithm profile')
    result = on_argv[:position] + on_argv[position + 2:]
    need(not any(x.startswith('--speculative-config') for x in result), 'native AR has no speculative option')
    return result


def source(sr):
    m = obj(sr)
    need(m['schema'] == 'bole.native-ar-pair-observer-source/v1'
         and m['prepared_only'] is False and m['default_enabled'] is False
         and m['scope'] == SCOPE and m['root'] == str(Path(__file__).resolve().parent),
         'actual bound default-OFF AR observer packet')
    for r in (*m['files'].values(), *m['runtime_sources'].values()):
        checked(r)
    need(ref(__file__) == m['files']['pair_contract.py'], 'exact pair helper source')
    need(m['native_server_argv'] == native_argv(obj(m['BOLE_server_command_ref'])['argv']),
         'only declared AR versus BOLE algorithm argv delta')
    return m
