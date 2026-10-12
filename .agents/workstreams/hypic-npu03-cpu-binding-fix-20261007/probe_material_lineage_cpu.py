"""CPU-only probe of exact HYPIC material-store lineage; not device evidence."""
from __future__ import annotations
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys

SOURCE = Path("/cache/cch/hypic_vllm_ascend-hotproof-20261008")
COMMIT = "4429e35177979c874bf053ab29789e4773f39b22"
MATERIAL_SHA = "cd677063af4e296be00d12ae9f148fc384cdf4f29b376170f89cd56eb5cf6f68"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    require(subprocess.check_output(
        ["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip() == COMMIT,
        "source commit drift")
    require(not subprocess.check_output(
        ["git", "-C", str(SOURCE), "status", "--porcelain", "--untracked-files=no"],
        text=True).strip(), "source tracked files dirty")
    path = SOURCE / "hypic_vllm_ascend/material.py"
    require(hashlib.sha256(path.read_bytes()).hexdigest() == MATERIAL_SHA,
            "material source drift")
    sys.path.insert(0, str(SOURCE))
    material = importlib.import_module("hypic_vllm_ascend.material")
    require(Path(material.__file__).resolve() == path.resolve(), "wrong import")
    import torch
    Store = material.MaterializedSegmentStore
    a, b = b"lineage-A", b"lineage-B"
    layers = dict(expected_full_layers={"attn"}, expected_gdn_layers={"gdn"})
    store = Store()
    store.configure(max_mb=1, min_free_mb=0, max_segments=1,
                    storage_device="cpu", gdn_storage_device="cpu",
                    pin_cpu_material=False)
    # Only CPU ownership/lifecycle is tested; no device allocator is queried.
    store._device_free_bytes = lambda: None

    def begin(key, protected=()):
        store.begin_step([key], protected_hashes=protected, **layers)

    def tensors(value):
        return [torch.full((2, 2), float(value + n)) for n in range(5)]

    def put(key, values):
        k, v, s, conv, transition = values
        return (store.put_full_kv(key, "attn", k, v),
                store.put_gdn_state(key, "gdn", s, conv, transition))

    def payload(obj):
        return (*obj.full_kv_by_layer["attn"], obj.gdn_state_by_layer["gdn"],
                obj.conv_tail_by_layer["gdn"], obj.transition_by_layer["gdn"])

    def finish():
        return store.finish_step(require_full_kv=True, require_gdn=True,
                                 require_transition=True, **layers)

    checks = []
    begin(a)
    producer = tensors(1)
    expected = [t.clone() for t in producer]
    require(put(a, producer) == (True, True), "initial writes failed")
    first = store.get(a)
    require(all(x.data_ptr() != y.data_ptr()
                for x, y in zip(payload(first), producer)), "stored tensor alias")
    for tensor in producer:
        tensor.add_(100)
    require(all(torch.equal(x, y) for x, y in zip(payload(first), expected)),
            "producer mutation changed stored bytes")
    require(finish().ready_hashes == (a,), "initial not ready")
    checks.append("producer_inputs_are_owned_clones_cpu")

    # A successful write attempt/readiness report is NOT a new generation.
    begin(a)
    attempted = tensors(20)
    require(put(a, attempted) == (True, True), "duplicate writes failed")
    require(finish().ready_hashes == (a,), "retained entry not reported ready")
    require(store.get(a) is first, "duplicate unexpectedly replaces object")
    require(all(torch.equal(x, y) for x, y in zip(payload(first), expected)),
            "duplicate overwrote retained material")
    require(all(not torch.equal(x, y)
                for x, y in zip(payload(first), attempted)),
            "negative control lacks different numerical inputs")
    checks.append("duplicate_put_true_and_ready_can_retain_old_generation")

    begin(b, protected=(a,))
    require(put(b, tensors(30)) == (False, False), "protected entry evicted")
    failed = finish()
    require(failed.failed and not failed.ready_hashes, "budget failure hidden")
    require(store.get(a) is first and store.get(b) is None,
            "protected object changed")
    checks.append("active_replay_protection_refuses_competing_material")

    begin(b)
    require(put(b, tensors(40)) == (True, True), "unprotected replacement failed")
    report = finish()
    require(report.evicted_hashes == (a,) and store.get(a) is None,
            "victim missing from eviction report")
    require(all(torch.equal(x, y) for x, y in zip(payload(first), expected)),
            "eviction mutated an existing tensor reference")
    checks.append("eviction_removes_mapping_not_retained_tensor_bytes")

    begin(a)
    new_values = tensors(50)
    require(put(a, new_values) == (True, True), "same-hash regeneration failed")
    require(finish().ready_hashes == (a,), "regeneration not ready")
    second = store.get(a)
    require(second is not first, "regeneration reuses retained object")
    require(all(torch.equal(x, y) for x, y in zip(payload(second), new_values)),
            "regenerated payload mismatch")
    require(all(not torch.equal(x, y)
                for x, y in zip(payload(first), payload(second))),
            "same-hash different-generation control is not discriminating")
    checks.append("same_hash_after_eviction_can_have_new_object_and_values")
    print(json.dumps(dict(schema="hypic-material-lineage-cpu-probe/v1",
        source_commit=COMMIT, material_sha256=MATERIAL_SHA,
        checks=checks, checks_passed=len(checks), device_execution=False,
        scope="real store methods with tiny synthetic CPU tensors",
        quality_cause_proven=False,
        next="Observe actual committed object generation and payload at producer and consumer; do not equate put success or ready hash with new generation."),
        indent=2))


if __name__ == "__main__":
    main()

