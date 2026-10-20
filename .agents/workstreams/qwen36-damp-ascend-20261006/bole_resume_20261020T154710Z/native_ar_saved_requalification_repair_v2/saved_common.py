"""Stdlib exact saved-evidence joins; no device, Docker or numerical execution."""
import importlib.util
import json
import os
from pathlib import Path
import re
import stat

LOCK = '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/MAIN_ADMISSION.lock'
FILES = ('ar_owner_common.py', 'ar_saved_namespace.py', 'saved_common.py', 'saved_preflight.py',
         'saved_cpu_owner.py', 'prepare_saved_owner.py', 'ACTUAL_SAVED_REFS.json', 'NAMESPACE_DELTA.json',
         'ACTUAL_FAILURE_REFS.json','CONSUMER_METADATA_DELTA.json','derived_math_consumer.py',
         'http_provenance.py','saved_consume_entry.py')


def common():
    path = Path(__file__).resolve().parent/'ar_owner_common.py'
    import hashlib
    raw = path.read_bytes()
    if (len(raw), hashlib.sha256(raw).hexdigest()) != (19055, '5d0b9034706b9a942a4d7dd10870139959b22dfaab2cebbdddf25ba962e456a4'):
        raise ValueError('exact frozen v5 common helper')
    spec = importlib.util.spec_from_file_location('_saved_ar_original_common', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def held_main_lock(C):
    """Observe the inherited outer flock; never open/acquire/create a new lock."""
    path = Path(LOCK)
    C.need(path.is_file() and not any(p.is_symlink() for p in (path, *path.parents)) and
           stat.S_IMODE(path.stat().st_mode) == 0o600, 'actual ordinary0600 MAIN lock')
    identity = path.stat()
    fds = []
    for descriptor in Path('/proc/self/fd').iterdir():
        try:
            value = descriptor.stat()
            if (value.st_dev, value.st_ino) == (identity.st_dev, identity.st_ino) and os.readlink(descriptor) == LOCK:
                fds.append(int(descriptor.name))
        except FileNotFoundError:
            continue
    lines = []
    for line in Path('/proc/locks').read_text().splitlines():
        values = line.split()
        if len(values) >= 8 and values[1:4] == ['FLOCK', 'ADVISORY', 'WRITE'] and values[4] == str(os.getpid()):
            parts = values[5].split(':')
            if len(parts) == 3 and int(parts[0], 16) == os.major(identity.st_dev) and int(parts[1], 16) == os.minor(identity.st_dev) and int(parts[2]) == identity.st_ino:
                lines.append(line)
    C.need(fds and len(lines) == 1, 'outer MAIN flock --no-fork inherited by this exact owner PID')
    return dict(path=LOCK, host_pid=os.getpid(), inherited_FDs=sorted(fds), actual_proc_locks=lines,
                lock_acquired_by_this_helper=False, inherited_MAIN_lock_verified=True)


def installed_map(C, original_inputs, ar_source, on, g1_bundle, *, check_copies=True):
    """Full Ref3 equality, never prefix or path-only exemption."""
    result = {}
    declared = dict(ar_source['runtime_sources'])
    copies = dict(original_inputs['runtime_host_evidence'])
    C.need(set(declared) == set(copies), 'complete actual runtime/host evidence map')
    framework = C.framework_sources(g1_bundle)
    C.need(set(framework) == set(original_inputs['framework_host_evidence']), 'complete actual four-framework map')
    rows = [(r, copies[k]) for k, r in declared.items()]
    rows += [(r, original_inputs['framework_host_evidence'][k]) for k, r in framework.items()]
    for installed, host in rows:
        C.need(type(installed) is dict and set(installed) == {'path', 'bytes', 'sha256'} and
               type(host) is dict and set(host) == {'path', 'bytes', 'sha256'} and host['path'] != installed['path'] and
               (host['bytes'], host['sha256']) == (installed['bytes'], installed['sha256']),
               'distinct declared installed/host paths with exact equal content')
        if installed['path'] in result:
            C.need(result[installed['path']]['installed'] == installed, 'same installed path cannot conflict')
        else:
            result[installed['path']] = dict(installed=installed, host=host)
        if check_copies:
            C.checked(host)
    return result


def collect(C, value, mapping, *, installed=False):
    """Resolve only exact declared Ref3 to host copies, retaining both identities."""
    refs, resolved = {}, []
    def add(reference):
        C.checked(reference)
        full = C.ref(reference['path'])
        if full['path'] in refs:
            C.need(refs[full['path']] == full, 'one exact ordinary readset identity')
        refs[full['path']] = full
    def walk(item):
        if type(item) is dict:
            if set(item) in ({'path', 'bytes', 'sha256'}, {'path', 'sha256'}):
                match = mapping.get(item['path'])
                if match is not None and item == match['installed']:
                    add(match['host'])
                    if installed:
                        add(item)
                    resolved.append(match)
                else:
                    add(item)  # Includes unknown installed-looking paths and Ref2: ordinary check must fail if absent.
            else:
                for child in item.values():
                    walk(child)
        elif type(item) is list:
            for child in item:
                walk(child)
    walk(value)
    return list(refs.values()), resolved


def prior(C, actual_refs):
    expected = C.obj(C.ref(Path(__file__).resolve().parent/'ACTUAL_SAVED_REFS.json'))
    C.need(actual_refs == expected, 'exact actual stopped v5 evidence refs, no arbitrary failed producer')
    objects = {name: C.obj(reference) for name, reference in actual_refs.items()}
    producer, x, m = (objects[n] for n in ('RESULT.json', 'OWNER_INPUTS.json', 'AR_SOURCE_BOUND.json'))
    ar, onbundle, pair = (objects[n] for n in ('NATIVE-AR-BUNDLE.json', 'BOLE-BUNDLE.json', 'PAIR-INPUTS.json'))
    C.need(producer['schema'] == 'bole.actual-native-ar-finite-owner/v1' and producer['primary']['error'] ==
           "ValueError('ordinary absolute Ref')" and producer['primary']['phase'] == dict(name='dense-stop-retain', ordinal=8) and
           'collect(bundle);collect(onbundle);collect(pair_ref)' in producer['primary']['traceback'] and
           producer['secondary'] == [] and producer['source_before'] == producer['source_after'] and
           producer['source_before'] and 'independent_child' not in producer['summary'] and
           'independent' not in producer['summary'] and producer['worker_signal_sent'] is False,
           'exact original postrelease host collector failure retained; no prior CPU numerical verdict')
    C.need(producer['inputs'] == actual_refs['OWNER_INPUTS.json'] and producer['source'] == x['AR_source'] ==
           actual_refs['AR_SOURCE_BOUND.json'] and m['pair_consumer_output_root'] == str(Path(x['output_root'])/'cpu-consumer') and
           pair['source'] == x['AR_source'] and pair['native_AR'] == actual_refs['NATIVE-AR-BUNDLE.json'] and
           pair['BOLE'] == actual_refs['BOLE-BUNDLE.json'] and pair['scope'] == m['scope'] and
           pair['inputs_ref'] == x['frozen_inputs'], 'actual saved pair/source/original owner input closure')
    C.need(ar['source'] == x['AR_source'] and onbundle['source'] == m['BOLE_source_ref'] and
           len(ar['ranks']) == len(ar['snapshots']) == len(ar['host_bindings']) == 4 and ar['worker_signal_sent'] is False,
           'actual four-rank saved native target, no worker signal')
    release = objects['dense/cleanup.json']
    owned = objects['dense/OWNED.json']
    C.need(producer['summary']['model_release']['path'] == actual_refs['dense/cleanup.json']['path'] and
           release['stopped'] is True and release['retained'] is True and release['deleted'] is False and
           release['errors'] == [] and release['container'] == owned['cid'] == ar['frontend_binding']['owned_cid'] and
           owned['arm'] == 'dense' and owned['source'] == x['AR_source'] and owned['image'] == m['expected_image_id'],
           'actual stopped retained original model owner')
    for key in ('sameimage_release', 'model_release'):
        value = C.obj(producer['summary'][key])
        C.need(value['stopped'] is True and value['retained'] is True and value['errors'] == [], 'original phases released')
    terminal = C.obj(producer['summary']['client_terminal'])
    C.need(terminal['exit_code'] == 0, 'actual original two-request/barrier client exited zero')
    return objects, x, m


def readset(C, y, *, installed=False):
    objects, x, m = prior(C, y['actual_saved_refs'])
    C.need(y['schema'] == 'bole.native-ar-saved-requalification-inputs/v2' and y['default_enabled'] is False and
           y['prepared_only'] is True and y['MAIN_lock'] == LOCK and y['AR_source'] == x['AR_source'] and
           y['original_owner_inputs'] == y['actual_saved_refs']['OWNER_INPUTS.json'] and
           y['output_root'] != x['output_root'] and y['consumer_output_root'] == str(Path(y['output_root'])/'cpu-consumer'),
           'new explicit CPU-only source ticket; unchanged producer and frozen consumer output contract')
    _, on, base = C.readset(x, installed=installed)
    b = C.obj(x['G1_bundle'])
    mapping = installed_map(C, x, m, on, b)
    failure_refs=C.obj(C.ref(Path(__file__).resolve().parent/'ACTUAL_FAILURE_REFS.json'))
    C.need(y['actual_prior_cpu_failure_refs']==failure_refs,'exact original saved CPUv1 failure and actual HTTP refs')
    failure_objects={}
    for name,r in failure_refs.items():
        C.checked(r)
        if name.endswith('.json'):failure_objects[name]=C.obj(r)
    old=failure_objects['saved_v1/RESULT.json'];release=failure_objects['saved_v1/cleanup.json']
    C.need(old['schema']=='bole.native-ar-saved-evidence-owner/v1'and old['primary']is not None and
           old['secondary']==[]and old['source_before']==old['source_after']and
           old['independent_numeric_requalification_pass']is False and 'independent'not in old['summary']and
           old['source']==x['AR_source']and release['stopped']is True and release['retained']is True and release['errors']==[],
           'actual failed first CPU qualification retained; no prior numeric pass')
    stderr=C.checked(failure_refs['saved_v1/SAVED-PAIR-INDEPENDENT.stderr']).read_text()
    C.need("KeyError: 'inputs_ref'"in stderr and 'http_tokens'in stderr,'exact actual first CPU metadata failure')
    failure_objects['saved_v1/INPUTS.json']=C.obj(old['inputs'])
    values = [*objects.values(), *y['actual_saved_refs'].values(), y['files']]
    values.extend([*failure_objects.values(),*failure_refs.values(),old['inputs']])
    for bundle in (objects['NATIVE-AR-BUNDLE.json'], objects['BOLE-BUNDLE.json']):
        values.append(C.obj(bundle['http']))
        values.extend(C.obj(row['receipt']) for row in bundle['ranks'])
    values.append(C.obj(objects['dense/cleanup.json']['after_inspect']))
    extra, resolutions = collect(C, values, mapping, installed=installed)
    unique = {}
    for reference in (*base, *extra):
        if reference['path'] in unique:
            C.need(unique[reference['path']] == reference, 'consistent immutable complete readset')
        unique[reference['path']] = reference
    verify_derivative(C,y,m)
    return x, m, on, list(unique.values()), dict(schema='bole.exact-installed-to-host-evidence/v1',
        declared_distinct_installed_paths=len(mapping), resolved_occurrences=len(resolutions),
        mapping=list(mapping.values()), unknown_path_exemption=False, installed_sources_reopened=installed)


def verify_derivative(C,y,m):
    delta=C.obj(y['files']['CONSUMER_METADATA_DELTA.json'])
    pairs=[("C.ref(__file__)==m['files']['consume_pair.py']","C.ref(__file__)==_SAVED_METADATA['files']['derived_math_consumer.py']"),
           ("str(output)==m['pair_consumer_output_root']","str(output)==_SAVED_METADATA['consumer_output_root']"),
           ("value['inputs_ref']==frozen['reference']","_http_provenance(C,source_ref,bundle,value,schema,header_prefix,frozen,_SAVED_METADATA)")]
    C.need(delta['original']==m['files']['consume_pair.py']and delta['edits']==[dict(before=a,after=b)for a,b in pairs],
           'only exact preregistered source/output/HTTP provenance expressions may change')
    original=C.checked(m['files']['consume_pair.py']).read_bytes()
    inverse=C.checked(y['files']['derived_math_consumer.py']).read_text()
    for before,after in reversed(pairs):
        C.need(inverse.count(after)==1,'unique inverse metadata expression')
        inverse=inverse.replace(after,before)
    C.need(inverse.encode()==original,'whole original numerical/identity consumer byte inverse')
    return True


def source(C, reference):
    y = C.obj(reference)
    C.need(y['files']['saved_common.py'] == C.ref(__file__), 'exact new saved-evidence common source')
    for r in y['files'].values():
        C.checked(r)
    return y
