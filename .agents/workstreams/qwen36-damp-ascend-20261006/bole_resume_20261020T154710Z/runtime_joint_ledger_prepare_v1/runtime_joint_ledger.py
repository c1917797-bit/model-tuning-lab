"""Runtime joint evidence accounting only; never authorizes a source or device."""
import json
import os
from pathlib import Path

SCHEMA = 'bole.runtime-joint-capture-ledger/v1'
RAW_CAP = 2**30
LOGICAL_CAP = 384 * 2**20
FRAME_WIRE_CAP = 448 * 2**20
CHECKPOINT_RESERVE = 128 * 2**20
METADATA_RESERVE = 64 * 2**20
SERIALIZATION_TEMP = 8 * 2**20
FAILURE_TEMP = 8 * 2**20
CONTRACT = dict(schema=SCHEMA, enabled=True, raw_cap=RAW_CAP, logical_cap=LOGICAL_CAP,
    frame_wire_cap=FRAME_WIRE_CAP, cpu_copies=2, checkpoint_reserve=CHECKPOINT_RESERVE,
    metadata_reserve=METADATA_RESERVE, serialization_temp=SERIALIZATION_TEMP,
    failure_temp=FAILURE_TEMP, lower_wire_bound_proven=False, numerical_qualified=False)


def require_temporary_evidence():
    # A bounded write callback controls disk bytes, NOT torch.save's allocation
    # before invoking write(data). The16MiB is only a reservation, not a proven
    # serializer/export/reload high-water. No caller boolean/PASS opens this.
    raise ValueError('actual same-image tensor serializer temporary high-water unmeasured; runtime joint fit pending')


def need(value, message):
    if not value:
        raise ValueError(message)


class BudgetReject(ValueError):
    pass


class Writer:
    def __init__(self, ledger, stream):
        self.ledger, self.stream, self.count = ledger, stream, 0

    def write(self, data):
        n = memoryview(data).nbytes
        # Actual bytes are checked BEFORE the underlying write. A partial file
        # is preserved; no failed chunk, fabricated completion or ACK is emitted.
        if self.ledger.failed or self.count + n > self.ledger.quota:
            self.ledger.failed = True
            raise BudgetReject('actual serialization chunk exceeds joint wire quota before write')
        # Debit before the syscall, so a short write/serializer finalizer cannot
        # reuse uncounted space after an underlying partial failure.
        self.count += n
        self.ledger.written = self.count
        try:
            written = self.stream.write(data)
            need(type(written) is int and written == n, 'complete bounded underlying write')
        except Exception:
            self.ledger.failed = True
            raise
        return written

    def flush(self):
        self.stream.flush()

    def tell(self):
        return self.count


class Joint:
    def __init__(self, c):
        self.c = c
        C, m = c['C'], c['m']
        import long_gate_primitives as L
        import g2_contract as G
        C.need(m.get('runtime_joint_capture_ledger') == CONTRACT and
               C.ref(__file__) == m['files']['runtime_joint_ledger.py'] and
               C.ref(L.__file__) == m['files']['long_gate_primitives.py'] and
               C.ref(G.__file__) == m['files']['g2_contract.py'],
               'default OFF complete source-owned joint ledger/unchanged budget parents')
        C.need((G.RAW_CAP, G.FRAME_LOGICAL_CAP, G.FRAME_WIRE_CAP, G.CHECKPOINT_CAP, G.METADATA_CAP) ==
               (RAW_CAP, LOGICAL_CAP, FRAME_WIRE_CAP, CHECKPOINT_RESERVE, METADATA_RESERVE),
               'original1GiB/384/448/128/64 caps unchanged')
        self.L = L
        self.phase = 'idle'
        self.failed = False
        self.ref = None
        self.written = 0
        self.quota = 0

    def total(self, wire):
        # Do not infer one CPU copy from del raw. No measured predecessor exists.
        total = self.L.raw_reservation(self.first, self.logical, wire,
                                      CHECKPOINT_RESERVE, METADATA_RESERVE)
        need(total + SERIALIZATION_TEMP + FAILURE_TEMP <= RAW_CAP,
             'joint raw/copies/checkpoint/metadata plus explicit temporary reserves')
        return total + SERIALIZATION_TEMP + FAILURE_TEMP

    def pre_export(self, frame, logical):
        try:
            return self._pre_export(frame, logical)
        except Exception:
            # Preserve the first refusal: callers cannot turn a failed frame
            # into a new attempt by changing quota or a later prerequisite.
            self.failed, self.phase = True, 'failed'
            raise

    def _pre_export(self, frame, logical):
        C = self.c['C']
        C.need(self.phase == 'idle' and not self.failed, 'no unACKed or failed frame may advance')
        C.need(type(logical) is int and 0 <= logical <= LOGICAL_CAP and
               frame['source'] == self.c['source'] and type(frame['rank']) is int and
               frame['rank'] == self.c['rank'] and type(frame['generation']) is int and
               frame['generation'] in (1, 2) and type(frame['ordinal']) is int and frame['ordinal'] >= 0,
               'actual source/rank/frame/logical operand before export')
        C.need(type(self.c['used']) is int and self.c['used'] >= 0 and
               type(self.c['metadata_bytes']) is int and 0 <= self.c['metadata_bytes'] <= METADATA_RESERVE,
               'actual retained first/failed wire and metadata counters')
        self.first, self.logical = self.c['used'], logical
        available = RAW_CAP - self.first - 2*logical - CHECKPOINT_RESERVE - METADATA_RESERVE - SERIALIZATION_TEMP - FAILURE_TEMP
        if available <= 0:
            raise BudgetReject('no positive current wire quota before X.export/t.save/t.load')
        self.quota = min(FRAME_WIRE_CAP, available)
        self.total(self.quota)
        require_temporary_evidence()
        self.phase, self.written, self.ref = 'pre_export', 0, None
        # This is a bounded allowed quota, NOT a claim that Torch serialization
        # fits or a caller-supplied PASS/lower-bound. Unique wire storage minimum
        # remains unproven without actual tensor+serializer evidence.
        return dict(quota=self.quota, wire_lower_bound=None, cpu_copies=2,
                    HBM_separate_cap=LOGICAL_CAP, numerical_qualified=False)

    def writer(self, stream):
        need(self.phase == 'pre_export' and not self.failed, 'pre-export admission before serialization')
        self.phase = 'serializing'
        return Writer(self, stream)

    def _dirsync(self, path):
        fd = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def serialization_failed(self, path, error):
        self.failed, self.phase = True, 'failed'
        self._dirsync(path)
        r = self.c['C'].ref(path)
        self.c['C'].checked(r)
        # Count the real partial file; retain it even though it is NOT a complete
        # reloadable frame. The source owner must stop, never ACK/release/retry.
        self.c['used'] += r['bytes']
        self.ref = r
        raise BudgetReject('partial serialization preserved; no ACK: ' +
                           json.dumps(dict(actual_partial_wire=r, complete=False,
                                           cause=repr(error)), sort_keys=True)) from error

    def after_wire(self, ref):
        need(self.phase == 'serializing' and not self.failed, 'actual complete serialization stage')
        C = self.c['C']
        C.checked(ref)
        self.ref = dict(ref)
        try:
            C.need(type(ref['bytes']) is int and ref['bytes'] == self.written and
                   0 < ref['bytes'] <= self.quota <= FRAME_WIRE_CAP,
                   'actual durable current wire equals bounded writer bytes')
            self.total(ref['bytes'])
        except Exception:
            self.failed, self.phase = True, 'failed'
            self.c['used'] += ref['bytes']
            raise
        self.phase = 'wired'

    def before_reload(self):
        need(self.phase == 'wired' and not self.failed, 'only complete admitted wire may independently reload')
        C = self.c['C']
        C.need(self.c['used'] == self.first + self.ref['bytes'], 'actual current wire charged before reload')
        C.checked(self.ref)
        self.total(self.ref['bytes'])
        self.phase = 'reloading'

    def ack_release(self, retained, report_ref, release_ref):
        need(self.phase == 'reloading' and not self.failed and type(retained) is bool,
             'only original independent consumption and durable release may ACK')
        C = self.c['C']
        C.checked(report_ref)
        release = C.obj(release_ref)
        C.need(release['source'] == self.c['source'] and release['actual_frame'] == self.ref and
               release['report'] == report_ref and release['retained'] is retained and
               release['released_after_independent_consumption'] is (not retained) and
               release['numerical_qualified'] is False and release['formal_performance'] is False,
               'actual original report/RELEASE metadata join')
        C.need(self.c['used'] == self.first + (self.ref['bytes'] if retained else 0),
               'only successful owned nonfirst wire released after durable independent report')
        if retained:
            C.checked(self.ref)
        else:
            C.need(not Path(self.ref['path']).exists(), 'released actual current file no longer exists')
        C.need(self.c['metadata_bytes'] <= METADATA_RESERVE, 'complete metadata remains inside original reserve')
        self.phase, self.ref = 'idle', None


def get(c):
    if 'runtime_joint_ledger' not in c:
        c['runtime_joint_ledger'] = Joint(c)
    return c['runtime_joint_ledger']
