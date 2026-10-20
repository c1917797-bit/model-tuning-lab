"""Strong process-local reuse of the original actual twelve-case calibration.

An existing file is never admission. The same worker/model/operator objects,
process, complete loaded-library set, ABI, source bytes and original receipts
must survive every acquire. This module changes no numerical reference.
"""
import copy
import os
import model_calibration131r12 as MC
from model_entry import need
import g1_contract as G1


class ProcessCalibration:
    def __init__(self, *, worker, model, source_ref, own, rank, old_ref):
        need(type(rank) is int and rank in range(4), 'actual TP4 calibration rank')
        self.worker = worker
        self.runner = worker.model_runner
        self.model = model
        self.pid = os.getpid()
        self.source_ref = copy.deepcopy(source_ref)
        self.own = copy.deepcopy(own)
        self.rank = rank
        self.old_ref = copy.deepcopy(old_ref)
        self.ref = None
        self.operator = None
        self.torch_module = None
        self.registration_module = None
        self.registration_callable = None
        self.generations = []
        self.proofs = []

    def acquire(self, t, C, *, worker, model, source_ref, own, rank,
                old_ref, native_registration, request_epoch):
        G1.epoch(request_epoch)
        need(request_epoch == len(self.generations) + 1 and
             self.generations == list(range(1, request_epoch)),
             'strict monotonic process calibration acquisitions')
        need(os.getpid() == self.pid and worker is self.worker and
             worker.model_runner is self.runner and model is self.model and
             source_ref == self.source_ref and own == self.own and
             C.obj(source_ref) == self.own and old_ref == self.old_ref and
             rank == self.rank, 'same strong worker/model/process/source/rank calibration owner')
        MC.own_module(C, own, MC)
        for ref in own['files'].values():
            C.checked(ref)
        for ref in own['runtime_sources'].values():
            C.checked(ref)
        if self.ref is not None:
            need(t is self.torch_module and native_registration is self.registration_module and
                 native_registration.actual is self.registration_callable,
                 'same strong runtime and registration callable before any reuse call')
        original = C.obj(old_ref)
        before = native_registration.actual(t, C, arm_verified=True)
        op = t.ops._C_ascend.npu_causal_conv1d_custom.default
        need(MC.identity(before) == MC.expected(original['registration']) and
             MC.schema_family(t) == original['actual_schema_family'],
             'unchanged entire actual library identity and callable ABI before acquire')
        created = self.ref is None
        if created:
            need(request_epoch == 1 and self.operator is None,
                 'only first real prefill creates original actual calibration')
            # MC.run owns its exclusive path and deliberately rejects preexistence.
            ref = MC.run(t, C, source_ref, own, old_ref, rank, native_registration)
        else:
            need(op is self.operator and t is self.torch_module and
                 native_registration is self.registration_module and
                 native_registration.actual is self.registration_callable,
                 'same strongly retained actual calibrated operator/runtime/registration callable')
            ref = self.ref
        value = MC.validate(C, ref, old_ref, source_ref, rank)
        after = native_registration.actual(t, C, arm_verified=True)
        need(t.ops._C_ascend.npu_causal_conv1d_custom.default is op and
             id(op) == value['callable_object_id'] and
             MC.schema_family(t) == value['actual_schema_family'] and
             MC.identity(before) == MC.identity(after) ==
             MC.identity(value['registration']) == MC.identity(value['registration_after']) ==
             MC.expected(original['registration']),
             'actual strong operator, source, ABI and complete loaded libraries revalidated')
        for lib in (MC.identity(after)['extension'], *MC.identity(after)['opapi']):
            C.checked(lib)
        self.operator = op
        self.torch_module = t
        self.registration_module = native_registration
        self.registration_callable = native_registration.actual
        self.ref = copy.deepcopy(ref)
        self.generations.append(request_epoch)
        proof = dict(schema='bole.process-local-actual-calibration-acquire/v1',
            source=source_ref, rank=rank, pid=self.pid, generation=request_epoch,
            created=created, reused=not created, calibration_ref=ref, old_abi_ref=old_ref,
            worker_object_id=id(worker), runner_object_id=id(self.runner),
            model_object_id=id(model), callable_object_id=id(op),
            actual_schema_family=value['actual_schema_family'],
            actual_registration_before=before, actual_registration_after=after,
            original_twelve_receipts_reopened=True, exact_library_identity=True,
            model_ready=False)
        self.proofs.append(copy.deepcopy(proof))
        return ref, value, proof
