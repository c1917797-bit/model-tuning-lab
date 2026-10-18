"""Read-only closed2 accounting before the unchanged storage061 check.

This is a new binding invocation, not a change to the frozen capture, ledger,
storage checker, or model Lease.  It creates no reservation and no output.
The full original readset/validate still execute after independent closed2
verification; the fresh model Lease must subsequently admit its own writes.
"""
import hashlib
import inspect
import os
import shutil
import stat
import types
from pathlib import Path

G = 2**30
PRIOR_SHA = '0b33e15e99c976ede98d76a77a5214c72dbfd018c46be145c7d9ffaa9e184efe'
ADJUSTED_SHA = 'dbb97b3410d5b37e0e976c5f4f24a59dff0ce02d046b2ec439e421ed7e896fb6'
CHECK_SHA = 'c3e29d465cff65b61bd795531126cfa657f6f5f2365f02ef6fa51e5bb7790d1b'
OLD = 'proof=S.check()'
NEW = '_readonly_patch(S);proof=S.check()'


def need(value, message):
    if not value:
        raise ValueError(message)


def body_sha(function):
    return hashlib.sha256(inspect.getsource(function).encode()).hexdigest()


def prior_delta(text):
    need(hashlib.sha256(text.encode()).hexdigest() == PRIOR_SHA,
         'exact complete original prior_policy body')
    need(text.count(OLD) == 1 and NEW not in text, 'one original real S.check seam')
    changed = text.replace(OLD, NEW)
    need(changed.count(NEW) == 1 and changed.replace(NEW, OLD) == text,
         'whole prior_policy inverse; original S.check retained')
    return changed


def strict_accounting(budget, total, old_committed, phases, rows):
    need(type(total) is int and type(old_committed) is int and
         0 <= total <= old_committed, 'real nonnegative whole-root commitment')
    need(budget.CAP == 32 * G and budget.LIMIT == 80 * G and budget.FREE == 100 * G,
         'unchanged32/80/100 accounting constants')
    need(body_sha(budget.adjusted) == ADJUSTED_SHA, 'same reviewed adjusted function')
    # A new bind has no own payload. Retained R34 payload remains in total;
    # passing its bytes here would incorrectly waive new-run capacity.
    return budget.adjusted(total, old_committed, phases, rows, 0, 0)


def require_fresh_free(budget, proof, live_free):
    need(type(live_free) is int and live_free >= budget.FREE + budget.CAP and
         proof['filesystem_free_bytes'] >= budget.FREE + budget.CAP,
         'prospective new32GiB preserves original free100GiB')


def wrap_commitment(storage, budget, phases, ledger, fence):
    need(storage.LIMIT == 80 * G and storage.FREE == 100 * G,
         'unchanged real storage061 80/100 checker')
    need(body_sha(storage.check) == CHECK_SHA, 'original storage061.check complete body')
    original = storage.commitment
    closed = inspect.getclosurevars(original).nonlocals.get('closed')
    need(type(closed) is list and len(closed) == 13 and
         len({row['leaf'] for row in closed}) == 13,
         'exact original thirteen distinct closed commitments')
    need(not ({row['leaf'] for row in phases} & {row['leaf'] for row in closed}),
         'closed2 not already discounted in original thirteen')
    original_check = storage.check
    record = dict(calls=0)

    def commitment(root, current):
        need(Path(root) == storage.ROOT and current == ledger,
             'same authorized root and immutable ledger23')
        fence()
        total, old = original(root, current)
        committed = strict_accounting(budget, total, old, phases, current['reservations'])
        record.update(calls=record['calls'] + 1, used_bytes=total,
                      original13_committed_bytes=old, committed_bytes=committed,
                      closed2_savings_bytes=sum(33 * G - row['frozen_bytes'] for row in phases),
                      prospective_new_cap_bytes=32 * G)
        need(storage.check is original_check, 'real storage check never replaced')
        return total, committed

    storage.commitment = commitment
    return record, original_check


def typed_closed2(seal, K, evidence, source_ref, ledger, original):
    e = evidence
    need(e['schema'] == seal.SCHEMA and e['source_manifest_ref'] == source_ref and
         e['baseline_ledger_ref'] == seal.BASE and e['original_source_ref'] == seal.SOURCE,
         'same original closed2 source/evidence/ledger identities')
    need(e['core_ledger_written'] is e['numeric_qualified'] is False and
         e['old_flags_preserved'] is True, 'historical no-ledger/no-qualification flags')
    need(e['root'] == str(seal.ROOT) and e['authority_ref'] == ledger['authority_ref'] and
         e['prior_sealed_evidence_ref'] == ledger['sealed_evidence_ref'],
         'same original authority and prior thirteen seal')
    need(e['global_inventory_before'] == e['global_inventory_after'],
         'original complete capture inventory stable')
    need(type(e['phases']) is list and len(e['phases']) == len(original) == 2,
         'exactly original N16 and N160')
    for index, row in enumerate(e['phases']):
        need(row['leaf'] == str(seal.LEAVES[index]) and
             all(row[key] == value for key, value in original[index].items()),
             'original leaf/create/cleanup/CID/failure flags preserved')
        matches = [value for value in ledger['reservations'] if value['leaf'] == row['leaf']]
        need(len(matches) == 1 and matches[0]['stage'] == 'numeric' and
             type(matches[0]['budget_bytes']) is int and matches[0]['budget_bytes'] == 33 * G,
             'one exact original numeric33GiB ledger row per leaf')
        need(type(row['frozen_bytes']) is int and 0 <= row['frozen_bytes'] <= 33 * G,
             'strict bounded original frozen byte count')


def readset(O, seal, contract, model_manifest):
    """Called only by the source-bound binder after its original guards.

    Never call Lease.open here: binding must not allocate an output/journal.
    No S.check exception is caught, no free override is supplied, and no
    numerical flag is promoted.
    """
    import fcntl
    import model_snapshot_budget as budget
    import stream_closed_tree as stream
    import renewed_closed_reader101r19 as renewal

    need(type(model_manifest) is dict and model_manifest['prepared_only'] is True,
         'actual prepared model source required by readonly binder')
    own = model_manifest['files']
    modules = {'readonly_closed_admission.py': Path(__file__),
               'model_snapshot_budget.py': Path(budget.__file__),
               'stream_closed_tree.py': Path(stream.__file__),
               'renewed_closed_reader101r19.py': Path(renewal.__file__)}
    for name, path in modules.items():
        need(path.resolve() == O.obj_file(own[name]).resolve() and
             own[name]['path'] == model_manifest['root'] + '/' + name,
             'exact source-bound admission dependency ' + name)
    source_ref = contract['closed_source_ref']
    evidence_ref = contract['closed_evidence_ref']
    historical = O.obj(source_ref)
    need(stream.file_ref(seal.__file__) == historical['files']['capture_closed2.py'],
         'frozen original capture source; installed guards retained')
    need(seal._renewed_authority_check is renewal.check and
         body_sha(budget.adjusted) == ADJUSTED_SHA, 'original renewal and adjusted arithmetic')
    renewal.check()
    K, _ = seal.canonical(source_ref)
    e = K.read(evidence_ref)
    ledger = K.read(seal.BASE)
    need(budget.ROOT == seal.ROOT and budget.LEAF.parent == seal.ROOT and
         budget.JOURNAL.parent == seal.ROOT and budget.LEAF not in seal.LEAVES,
         'one source-declared future model leaf and journal in same root')

    def absent():
        need(not os.path.lexists(budget.LEAF) and not os.path.lexists(budget.JOURNAL),
             'readonly new binding creates neither payload nor journal')

    # Use the already-existing shared lock without O_CREAT or any file write.
    lock = seal.ROOT / '.storage061.lock'
    before_lock = lock.lstat()
    need(stat.S_ISREG(before_lock.st_mode) and
         all(not p.is_symlink() for p in (lock, *lock.parents)), 'ordinary existing shared061 lock')
    fd = os.open(lock, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        need(stream.identity(os.fstat(fd)) == stream.identity(before_lock), 'same opened shared lock inode')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        absent()
        need(seal.latest(K) == seal.BASE, 'unchanged highest original ledger23')
        global_before = seal.inventory(seal.ROOT)
        K.no_writers()
        original = seal.receipts(K)
        typed_closed2(seal, K, e, source_ref, ledger, original)
        need(K.inspect_all() == e['states_before'] == e['states_after'],
             'all original exact closed2 CIDs stopped before hashing')
        baselines = {}
        for row in e['phases']:
            tree = seal.read_tree(K, row['tree_ref'])
            need(tree['root'] == row['leaf'] and K.tree(row['leaf'], True) == tree['files'] and
                 row['frozen_bytes'] == sum(item['bytes'] for item in tree['files']),
                 'independent complete original closed2 hashes before any discount')
            baselines[row['leaf']] = stream.metadata(row['leaf'])
        need(seal.inventory(seal.ROOT) == global_before,
             'complete existing root unchanged around prevalidation')

        def fence():
            absent()
            renewal.check()
            need(stream.identity(os.fstat(fd)) == stream.identity(before_lock) and
                 stream.identity(lock.lstat()) == stream.identity(before_lock), 'same held shared lock')
            need(seal.latest(K) == seal.BASE and K.read(seal.BASE) == ledger and K.read(evidence_ref) == e,
                 'same immutable ledger and closed2 evidence throughout invocation')
            K.no_writers()
            need(K.inspect_all() == e['states_before'] == e['states_after'],
                 'fresh original exact CIDs remain stopped')
            for row in e['phases']:
                need(K.ref(row['tree_ref']['path']) == row['tree_ref'] and
                     stream.metadata(row['leaf']) == baselines[row['leaf']],
                     'all fully verified closed2 data and indices remain unchanged')

        fence()
        policies = []

        def patch(storage):
            need(not policies, 'one original prior-policy installation')
            record, original_check = wrap_commitment(storage, budget, e['phases'], ledger, fence)
            policies.append((storage, record, original_check))

        # Keep the already-installed readonly-command/stream/renewal functions;
        # clone only invocation globals. The frozen seal module is not patched.
        scope = dict(seal.validate.__globals__, _readonly_patch=patch)
        exec(compile(prior_delta(inspect.getsource(seal.prior_policy)),
                     seal.__file__ + '#readonly-closed2-admission', 'exec'), scope)
        validate = types.FunctionType(seal.validate.__code__, scope, 'validate',
                                      seal.validate.__defaults__, seal.validate.__closure__)
        read_scope = dict(seal.readset.__globals__, validate=validate)
        original_readset = types.FunctionType(seal.readset.__code__, read_scope, 'readset',
                                              seal.readset.__defaults__, seal.readset.__closure__)
        value = original_readset(evidence_ref, source_ref)
        need(value['closed_count'] == 15 and value['numeric_qualified'] is False and len(policies) == 1,
             'whole original fifteen-leaf readset and validation completed')
        storage, record, original_check = policies[0]
        need(storage.check is original_check and record['calls'] >= 1,
             'real original S.check was reached with proved closed2 accounting')
        # Re-run the exact check, with actual live free space, after the full
        # original readset. This remains an observation, not a reservation.
        proof = storage.check()
        require_fresh_free(budget, proof, shutil.disk_usage(seal.ROOT).free)
        fence()
        need(seal.inventory(seal.ROOT) == global_before and
             global_before['bytes'] == proof['used_bytes'], 'whole root stable and original scan agrees')
        for name in modules:
            O.obj_file(own[name])
        need(value['proof']['used_bytes'] == proof['used_bytes'] and
             value['proof']['committed_bytes'] == proof['committed_bytes'],
             'same real storage accounting before and after full original validation')
        value['proof'] = proof
        value['readonly_admission'] = dict(
            schema='deltalog.readonly-closed2-accounting/v1', helper_ref=own['readonly_closed_admission.py'],
            adjusted_source_ref=own['model_snapshot_budget.py'], original_storage_source_ref=K.read(seal.SOURCE)['files']['storage061.py'],
            evidence_ref=evidence_ref, ledger_ref=seal.BASE, accounting=record,
            full_original_closed15_validation=True, original_check_body_unchanged=True,
            core_ledger_written=False, model_journal_created=False, reservation_created=False,
            requires_fresh_model_lease=True, NPU=False, numeric_qualified=False)
        return value
    finally:
        os.close(fd)
