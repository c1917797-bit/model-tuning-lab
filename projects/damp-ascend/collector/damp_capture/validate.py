"""Offline evidence validator; no NPU calls and no partial TP acceptance."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .contract import LAYERS, STATE_BYTES, digest, file_digest, load_manifest, require,token_digest
from .text_positions import TEXT_METADATA_SOURCES
from .bindings import BINDING_SOURCES
from .identity import live_identity,legacy_identity


def records(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def validate(root, manifest, dense_root, *, legacy_source_path=None):
    root, dense_root = Path(root), Path(dense_root)
    mhash = digest(manifest)
    run = json.loads((root / "RUN.json").read_text())
    dense = json.loads((dense_root / "RUN.json").read_text())
    require(run["manifest_sha256"] == dense["manifest_sha256"] == mhash and
            run["capture_enabled"] and not dense["capture_enabled"], "paired run/manifest mismatch")
    require(run["generation"] == dense["generation"] == manifest["generation"] and
            run["batch_size"] == dense["batch_size"] and
            run["enforce_eager"] and dense["enforce_eager"], "same-eager pair required")
    for path in (root, dense_root):
        complete = json.loads((path / "CLIENT_COMPLETE.json").read_text())
        require(complete["rows"] == len(manifest["rows"]) and complete["manifest_sha256"] == mhash,
                "client completion mismatch")
    clients = {r["logical_id"]: r for r in records(root / "client.jsonl")}
    oracles = {r["logical_id"]: r for r in records(dense_root / "client.jsonl")}
    ids = {r["id"] for r in manifest["rows"]}
    require(set(clients) == set(oracles) == ids, "missing/extra client rows")
    require(len(records(root / "client.jsonl")) == len(ids) and
            len(records(dense_root / "client.jsonl")) == len(ids), "duplicate client rows")
    for row in manifest["rows"]:
        live, oracle = clients[row["id"]], oracles[row["id"]]
        require(live["prompt_token_sha256"] == oracle["prompt_token_sha256"] == row["input_ids_sha256"],
                "prompt identity differs")
        require(live["output_token_ids"] == oracle["output_token_ids"], "capture changed output token IDs")
        for output in (live,oracle):
            require(output["output_tokens"] == len(output["output_token_ids"]) ==
                manifest["generation"]["max_tokens"] and
                output["output_token_sha256"] == token_digest(output["output_token_ids"]),
                "wrong output length/hash")
    if legacy_source_path is None:
        identity = dict(mode="observed-native-add_request",
            capture=live_identity(root,manifest,clients),oracle=live_identity(dense_root,manifest,oracles))
        recovered = None
    else:
        recovered,identity = legacy_identity(root,dense_root,manifest,clients,oracles,legacy_source_path)
    expected = {(rid, layer, step) for rid in ids for layer in LAYERS for step in manifest["anchors"]}
    for rank in range(4):
        directory = root / f"rank-{rank}"
        events = records(directory / "events.jsonl")
        require(events and all(e["rank"] == rank for e in events), "rank evidence mismatch")
        require(not any(e["event"] == "capture_failed" for e in events), "worker capture failure")
        started = [e for e in events if e["event"] == "worker_started"]
        require(len(started) == 1 and started[0]["manifest_sha256"] == mhash, "worker manifest mismatch")
        source = started[0]["source"]
        require(source["tp_world"] == 4 and source["logical_device"] == rank and
                source["physical_device"] == rank + 4 and
                source["gdn_sha256"] == manifest["runtime_hashes"]["gdn"] and
                source["runner_sha256"] == manifest["runtime_hashes"]["runner"] and
                source["recurrent_schema_sha256"] == digest(source["recurrent_schema"]), "runtime identity mismatch")
        require(source.get("text_metadata_sources") == TEXT_METADATA_SOURCES,
                "text/sequence metadata source identity mismatch")
        require(source.get("binding_sources") == BINDING_SOURCES, "actual receiver source identity mismatch")
        dispatch = [e for e in events if e["event"] == "worker_dispatch_verified"]
        require(len(dispatch) == 1 and len(dispatch[0]["layers"]) == len(LAYERS) and
                {r["layer"] for r in dispatch[0]["layers"]} == set(LAYERS),
                "actual receiver instance proof incomplete")
        for binding in dispatch[0]["layers"]:
            require(binding["instance_class"] ==
                    "vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn.QwenGatedDeltaNetAttention" and
                    binding["class_path"] ==
                    "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py" and
                    binding["class_sha256"] == BINDING_SOURCES[binding["class_path"]] and
                    binding["core_owner"]["sha256"] == source["collector_sha256"] and
                    binding["original_core_owner"]["sha256"] == source["gdn_sha256"] and
                    binding["outer_forward_owner"]["sha256"] == source["gdn_sha256"],
                    "actual receiver/wrapper/native owning function mismatch")
        bindings = [e for e in events if e["event"] == "request_bound"]
        require(len(bindings) == len(ids) and {e["logical_id"] for e in bindings} == ids,
                "worker request identity incomplete")
        for event in bindings:
            client = clients[event["logical_id"]]
            runtime_id = client["runtime_id"] if recovered is None else recovered[event["logical_id"]]["runtime_id"]
            require(event["runtime_id"] == runtime_id and
                    event["prompt_token_sha256"] == client["prompt_token_sha256"], "worker/client identity mismatch")
        for kind, size in (("anchor", STATE_BYTES), ("future", manifest["horizon"] * 12 * 4)):
            selected = [e for e in events if e["event"] == kind]
            keys = {(e["logical_id"], e["layer"], e["update"]) for e in selected}
            require(keys == expected and len(selected) == len(expected), "missing/duplicate " + kind)
            for event in selected:
                artifact = event["artifact"]
                path = (directory / artifact["path"]).resolve()
                require(path.is_relative_to(directory.resolve()) and path.is_file() and
                        artifact["bytes"] == size and path.stat().st_size == size and
                        file_digest(path) == artifact["sha256"], "corrupt/outside artifact")
        done = [e for e in events if e["event"] == "layer_complete"]
        require(len(done) == len(ids) * len(LAYERS) and
                {(e["logical_id"], e["layer"]) for e in done} ==
                {(rid, layer) for rid in ids for layer in LAYERS}, "incomplete layer timelines")
        turns = [e for e in events if e["event"] == "turn_complete"]
        require(turns and all(e["layers"] == list(LAYERS) for e in turns), "GDN coverage incomplete")
        position_events = [e for e in events if e["event"] == "text_positions_verified"]
        require(len(position_events) == len(turns) and
                all(p["runtime_ids"] == t["runtime_ids"] and p["native_arguments_unmodified"] is True and
                    p["mode"] in ("pure-text-mrope-3-identical-rows", "pure-text-1d")
                    for p, t in zip(position_events, turns)), "text position proof/turn coverage mismatch")
    return dict(status="pass", mode=manifest["mode"], ranks=4, layers=len(LAYERS), requests=len(ids),
                anchors=len(manifest["anchors"]), output_parity="all token IDs bitwise same-eager",
                scope="smoke-hook-not-calibration" if manifest["mode"] == "smoke" else "FP32-reference-calibration-only",
                not_proven=["compressed recurrence", "NPU graph", "end-to-end speedup", "task accuracy"],
                request_identity=identity)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--dense-output-dir", required=True)
    a = p.parse_args()
    result = validate(a.output_dir, load_manifest(a.manifest), a.dense_output_dir)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
