"""R24 C2 snapshot receipt audit layered on unchanged R21 Canary gates.

The pure join below is NOT numerical/device acceptance by itself. audit() first
runs the existing source/mechanism/numerical/physical/isolation/release auditor.
"""
import hashlib
import json
from pathlib import Path

from audit_r21_c2_finite_canary import audit as audit_base

_MODEL = "compact_model_rows_completed"
_CHECKED = "c2_block_table_snapshot_layer_checked"
_INSTALL = "compact_hypic_hooks_installed"
_CAPTURE = "compact_native_attention_groups_captured"
_GROUP_SOURCE = "verified-native-full-attention-spec"
_COMPLETED = {"compact_c2_queries_completed", "mixed_native_c2_completed"}
_RELEVANT = {_MODEL, _CHECKED, _INSTALL, _CAPTURE} | _COMPLETED


def _request_ids(value):
    if (not isinstance(value, list) or not value
            or any(not isinstance(x, str) or not x for x in value)
            or len(set(value)) != len(value)):
        raise ValueError("nonempty unique exact request ids required")
    return frozenset(value)


def _count(value):
    if type(value) is not int or value < 0:
        raise ValueError("nonnegative exact snapshot count required")
    return value


def audit_snapshot_receipts(events, workers, manifest, *, enabled,
                            expected_group=None, expected_layers):
    """Join one source-bound single-group forward, not unrelated green counts."""
    if (type(enabled) is not bool or (expected_group is not None and
            (type(expected_group) is not int or expected_group < 0))):
        raise ValueError("explicit snapshot mode and native group required")
    if not isinstance(expected_layers, (list, tuple)):
        raise ValueError("frozen layer inventory required")
    expected_layers = tuple(expected_layers)
    if (len(expected_layers) != 16 or len(set(expected_layers)) != 16
            or any(not isinstance(x, str) or not x for x in expected_layers)):
        raise ValueError("exact frozen 27B sixteen-layer inventory required")
    layer_set = frozenset(expected_layers)
    if (set(workers) != set(range(4))
            or any(type(r) is not int for r in workers)
            or any(type(pid) is not int or pid < 1 for pid in workers.values())
            or len(set(workers.values())) != 4
            or not isinstance(manifest, str) or len(manifest) != 64
            or any(c not in "0123456789abcdef" for c in manifest)):
        raise ValueError("exact four source-bound workers required")
    pid_rank = {pid: rank for rank, pid in workers.items()}
    installs = {}
    models = {}
    checked = {}
    completed = {}
    captures = {}
    def identity(event):
        rank = event.get("rank")
        if (type(rank) is not int or rank not in workers
                or type(event.get("pid")) is not int
                or event["pid"] != workers[rank]
                or event.get("manifest_sha256") != manifest
                or type(event.get("step")) is not int or event["step"] < 1):
            raise ValueError("snapshot rank/PID/source/step identity drift")
        if "group" in event and (type(event["group"]) is not int or event["group"] < 0):
            raise ValueError("invalid native group identity")
        if expected_group is not None and "group" in event and event["group"] != expected_group:
            raise ValueError("snapshot native group drift")
        return rank, event["step"]
    for position, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError("event object required")
        kind = event.get("event")
        if kind not in _RELEVANT:
            continue
        if kind == _INSTALL:
            pid = event.get("pid")
            if (type(pid) is not int or pid not in pid_rank
                    or event.get("manifest_sha256") != manifest
                    or event.get("c2_block_table_snapshot") is not enabled
                    or event.get("c2_block_table_diagnostic") is not True):
                raise ValueError("snapshot install PID/source/mode drift")
            rank = pid_rank[pid]
            if ("rank" in event and
                    (type(event["rank"]) is not int or event["rank"] != rank)):
                raise ValueError("snapshot installation rank drift")
            if rank in installs:
                raise ValueError("duplicate snapshot worker installation")
            installs[rank] = position
            continue
        forward = identity(event)
        if forward[0] not in installs or position <= installs[forward[0]]:
            raise ValueError("snapshot receipt precedes own worker installation")
        if kind == _CAPTURE:
            groups = event.get("attention_groups")
            if (forward in captures or event.get("source") != _GROUP_SOURCE
                    or not isinstance(groups, list) or len(groups) != 1
                    or not isinstance(groups[0], dict)):
                raise ValueError("unique source-verified native full-attention capture required")
            group = groups[0].get("group")
            names = groups[0].get("layers")
            if (type(group) is not int or group < 0
                    or (expected_group is not None and group != expected_group)
                    or not isinstance(names, list) or len(names) != 16
                    or any(not isinstance(x, str) or not x for x in names)
                    or len(set(names)) != 16 or set(names) != layer_set):
                raise ValueError("native capture group/frozen layer inventory drift")
            captures[forward] = (position, _request_ids(event.get("request_ids")), group)
            continue
        if kind == _MODEL:
            if forward in models:
                raise ValueError("duplicate snapshot model forward")
            ids = _request_ids(event.get("request_ids"))
            if event.get("c2_block_table_snapshot") is not enabled:
                raise ValueError("snapshot model mode drift")
            reads = _count(event.get("c2_block_table_snapshot_reads"))
            hits = _count(event.get("c2_block_table_snapshot_hits"))
            if (enabled and (reads != 1 or hits < 15)) or (
                    not enabled and (reads != 0 or hits != 0)):
                raise ValueError("snapshot forward reuse/disabled counts invalid")
            models[forward] = (position, ids, reads, hits)
            continue
        layer = event.get("layer")
        if not isinstance(layer, str) or layer not in layer_set:
            raise ValueError("snapshot layer outside frozen inventory")
        key = forward + (layer,)
        if kind == _CHECKED:
            if not enabled:
                raise ValueError("disabled arm emitted snapshot checked receipt")
            if key in checked or type(event.get("group")) is not int or event["group"] < 0:
                raise ValueError("duplicate/incorrect snapshot layer or group")
            checked[key] = (position, _request_ids(event.get("request_ids")),
                _count(event.get("reads_delta")), _count(event.get("hits_delta")),
                event["group"])
        else:
            rid = event.get("request_id")
            if not isinstance(rid, str) or not rid:
                raise ValueError("snapshot completion request identity missing")
            item = key + (rid,)
            windows = event.get("query_windows")
            if item in completed or type(windows) is not int or windows < 1:
                raise ValueError("duplicate/invalid snapshot layer completion")
            completed[item] = (position, windows, kind, event.get("group"))
    if set(installs) != set(workers) or not models:
        raise ValueError("snapshot four-worker install/model coverage incomplete")
    if {r for r, step in models} != set(workers):
        raise ValueError("snapshot four-rank forward coverage incomplete")
    steps_by_rank = {r: {step for rank, step in models if rank == r} for r in workers}
    if any(steps != steps_by_rank[0] for steps in steps_by_rank.values()):
        raise ValueError("snapshot forward steps differ across TP workers")
    for step in steps_by_rank[0]:
        ids = models[(0, step)][1]
        if any(models[(rank, step)][1] != ids for rank in workers):
            raise ValueError("snapshot forward request cohort differs across ranks")
        if (any((rank, step) not in captures for rank in workers)
                or len({captures[(rank, step)][2] for rank in workers}) != 1):
            raise ValueError("snapshot native group capture missing or differs across ranks")
    expected_completions = set()
    expected_checked = set()
    summaries = []
    for forward, (model_position, ids, model_reads, model_hits) in models.items():
        rank, step = forward
        if forward not in captures or captures[forward][1] != ids:
            raise ValueError("snapshot model lacks exact native capture cohort")
        capture_position, capture_ids, group = captures[forward]
        layers = []
        for layer in expected_layers:
            key = forward + (layer,)
            positions = []
            windows = 0
            for rid in ids:
                item = key + (rid,)
                expected_completions.add(item)
                if item not in completed:
                    raise ValueError("snapshot model lacks exact request/layer completion")
                position, n, kind, completion_group = completed[item]
                if completion_group is not None and completion_group != group:
                    raise ValueError("completion/native captured group drift")
                if position <= capture_position:
                    raise ValueError("C2 completion precedes independent native capture")
                if position >= model_position:
                    raise ValueError("snapshot model precedes layer completion")
                positions.append(position)
                windows += n
            if enabled:
                expected_checked.add(key)
                if key not in checked:
                    raise ValueError("snapshot model lacks checked layer")
                position, checked_ids, reads, hits, checked_group = checked[key]
                if checked_group != group:
                    raise ValueError("checked/native captured group drift")
                if checked_ids != ids or reads + hits != windows:
                    raise ValueError("snapshot request/window count conservation failed")
                if position <= max(positions) or position >= model_position:
                    raise ValueError("snapshot layer checked/model order invalid")
                layers.append((position, reads, hits))
        if enabled:
            layers.sort()
            for index, (_, reads, hits) in enumerate(layers):
                if reads != (1 if index == 0 else 0):
                    raise ValueError("snapshot cold first-layer/read reuse order invalid")
            reads = sum(x[1] for x in layers)
            hits = sum(x[2] for x in layers)
            if (reads, hits) != (model_reads, model_hits):
                raise ValueError("snapshot layer/model counters do not conserve")
        summaries.append(dict(rank=rank, step=step, group=group,
            request_ids=sorted(ids), layers=16, reads=model_reads, hits=model_hits))
    if set(completed) != expected_completions or set(checked) != expected_checked:
        raise ValueError("extra or unmatched snapshot layer/request/forward receipt")
    return dict(enabled=enabled, forwards=len(models),
        checked_layers=len(checked), request_layer_completions=len(completed),
        reads=sum(v[2] for v in models.values()),
        hits=sum(v[3] for v in models.values()),
        expected_group=expected_group, expected_layers=list(expected_layers),
        group_source=_GROUP_SOURCE, native_captures=len(captures),
        per_forward=sorted(summaries, key=lambda x: (x["rank"], x["step"])),
        scope="exact snapshot source/worker/forward/group/layer/request/order/count join only")


def audit(path, *, live_release=False):
    cp = Path(path).resolve()
    contract = json.loads(cp.read_text())
    report = audit_base(cp, live_release=live_release)
    acceptance = contract.get("c2_snapshot_acceptance")
    if not isinstance(acceptance, dict):
        raise ValueError("frozen C2 snapshot acceptance inventory required")
    manifest_path = cp.parent / contract["cache_diagnostic"]["compact_manifest"]
    manifest = json.loads(manifest_path.read_text())
    config = json.loads((cp.parent / manifest["config"]).read_text())
    enabled = config.get("c2_block_table_snapshot")
    if (type(enabled) is not bool or acceptance.get("enabled") is not enabled
            or acceptance.get("group_source") != _GROUP_SOURCE
            or config.get("c2_block_table_diagnostic") is not True
            or config.get("c2_layer_completion_barrier") is not True):
        raise ValueError("snapshot contract/config/layer-barrier mode mismatch")
    events = []
    for file in sorted((Path(contract["raw_root"]) / "diagnostics").glob(
            "compact-worker-*.jsonl")):
        if file.is_symlink() or not file.is_file():
            raise ValueError("regular snapshot worker log required")
        events.extend(json.loads(line) for line in file.read_text().splitlines())
    workers = {int(rank): pid for rank, pid in report["hot"]["worker_pids"].items()}
    report["c2_block_table_snapshot"] = audit_snapshot_receipts(
        events, workers, hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        enabled=enabled, expected_group=None,
        expected_layers=acceptance.get("layers", ()))
    report["scope"] = (
        "bounded R24 unchanged R21 numerical/mechanism/source/physical/isolation/"
        "release plus exact C2 snapshot receipts; not formal speed or full task quality")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--live-release", action="store_true")
    args = parser.parse_args()
    print(json.dumps(audit(args.contract, live_release=args.live_release)))
