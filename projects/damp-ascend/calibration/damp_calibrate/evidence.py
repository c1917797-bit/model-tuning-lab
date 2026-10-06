"""Strict full36/TP4/48-layer reference receipts; no partial or smoke calibration."""
import hashlib
import json
import math
from pathlib import Path
from damp_capture.contract import (FULL_ANCHORS, INPUT_ROOT, LAYERS, MODEL_HASHES,
    STATE_BYTES, digest, file_digest, load_manifest, require)
from damp_capture.bindings import BINDING_SOURCES
from damp_capture.text_positions import TEXT_METADATA_SOURCES
from damp_capture.validate import validate
from .rules import partition_rows

COMMON = ("gdn_path","gdn_sha256","runner_path","runner_sha256","collector_path",
    "collector_sha256","device_operator_path","device_operator_sha256","text_metadata_sources",
    "text_positions_helper_sha256","binding_sources","bindings_helper_sha256",
    "recurrent_schema","recurrent_schema_sha256")

def read_json(path, maximum=8*1024*1024):
    p = Path(path).resolve(strict=True)
    require(p.is_file() and p.stat().st_size <= maximum, "JSON missing/oversized")
    return json.loads(p.read_text()), dict(path=str(p),sha256=file_digest(p),bytes=p.stat().st_size)

def lines(path, maximum=64*1024*1024, maximum_lines=400000):
    p = Path(path); require(p.is_file() and p.stat().st_size <= maximum, "audit missing/oversized")
    with p.open() as handle:
        for count,line in enumerate(handle,1):
            # Full B1 has 2*36*4096 turn/position events before state receipts.
            require(count <= maximum_lines and len(line) <= 2*1024*1024, "audit line/count too large")
            if line.strip(): yield json.loads(line)

def report_receipt(identity, mode, requests):
    report,receipt = read_json(identity["path"])
    require(receipt["sha256"] == identity["sha256"] and report.get("status") == "pass" and
            report.get("mode") == mode and report.get("ranks") == 4 and report.get("layers") == 48 and
            report.get("requests") == requests and
            report.get("output_parity") == "all token IDs bitwise same-eager", "unproven parity report")
    return report,receipt

def lock_source(path,manifest_path,manifest,root):
    lock,receipt = read_json(path)
    require(lock.get("schema") == "damp.source-lock/v1" and lock.get("created_by") == "parent-controller"
            and lock.get("model_config_sha256") == MODEL_HASHES["config.json"] and
            isinstance(lock.get("image_id"),str) and lock["image_id"].startswith("sha256:")
            and len(lock["image_id"]) == 71 and all(c in "0123456789abcdef" for c in lock["image_id"][7:]),
            "independent source lock/model/image required")
    mi = lock["manifest"]
    require(Path(mi["path"]).resolve() == Path(manifest_path).resolve() and
            mi["file_sha256"] == file_digest(manifest_path) and mi["semantic_sha256"] == digest(manifest)
            and Path(lock["capture_root"]).resolve() == root, "source lock full input/root drift")
    ranks = lock["ranks"]
    require(len(ranks) == 4 and [r["rank"] for r in ranks] == list(range(4)), "source lock TP4 incomplete")
    expected = None
    for rank,row in enumerate(ranks):
        events = root/f"rank-{rank}"/"events.jsonl"
        require(Path(row["events_path"]).resolve() == events and file_digest(events) == row["events_sha256"],
                "source lock worker receipt changed")
        require(row["source"]["logical_device"] == rank and row["source"]["physical_device"] == rank+4
                and row["source"]["tp_world"] == 4, "source lock device/rank mismatch")
        common = {key:row["source"][key] for key in COMMON}
        if expected is None: expected = common
        require(common == expected, "locked source differs across ranks")
    require(expected["binding_sources"] == BINDING_SOURCES and
            expected["text_metadata_sources"] == TEXT_METADATA_SOURCES and
            expected["recurrent_schema_sha256"] == digest(expected["recurrent_schema"]),
            "source lock not frozen hook/schema identity")
    require(1 <= lock["smoke_validation"]["requests"] <= 12, "invalid smoke proof request count")
    smoke,smoke_receipt = report_receipt(lock["smoke_validation"],"smoke",lock["smoke_validation"]["requests"])
    full,full_receipt = report_receipt(lock["native_output_parity"],"full",36)
    # Full evidence is revalidated independently; a smoke pass cannot replace it.
    actual = validate(root,manifest,lock["native_output_parity"]["dense_root"])
    require(actual == full, "full native-off/on report does not reproduce")
    return expected,dict(source_lock=receipt,image_id=lock["image_id"],worker_sources=[r["source"] for r in ranks],smoke_report=smoke_receipt,
                          full_parity_report=full_receipt,full_parity_rechecked=actual)

def train_sources(manifest):
    used,files = set(),{}
    for row in manifest["rows"]:
        require(row.get("context_records") and row.get("context_policy"), "TRAIN context provenance missing")
        for source in [row["source"],*row["context_records"]]:
            key = (source["dataset"],str(source["record_id"]))
            require(key not in used and source["split"] == "train", "TRAIN record overlap/evaluation leak")
            require(source["dataset"] == row["source"]["dataset"] and
                    source["revision"] == row["source"]["revision"] and source["license"] and
                    len(source["record_sha256"]) == 64, "context source drift")
            used.add(key); p = Path(source["artifact_path"]).resolve(strict=True)
            require(p.is_relative_to(INPUT_ROOT.resolve()), "TRAIN bytes outside data root")
            if p not in files: files[p] = file_digest(p)
            require(files[p] == source["artifact_sha256"], "TRAIN context bytes drift")
    return dict(records=len(used),artifacts=[dict(path=str(p),sha256=h) for p,h in sorted(files.items())])

class Capture:
    def __init__(self,manifest_path,root,lock_path):
        self.manifest = load_manifest(manifest_path)
        require(self.manifest["mode"] == "full", "smoke cannot fit calibration")
        self.partitions = partition_rows(self.manifest["rows"])
        self.rows = {r["id"]:r for r in self.manifest["rows"]}; self.root = Path(root).resolve(strict=True)
        training = train_sources(self.manifest)
        source,lock = lock_source(lock_path,manifest_path,self.manifest,self.root)
        run,rr = read_json(self.root/"RUN.json"); complete,cr = read_json(self.root/"CLIENT_COMPLETE.json")
        mh = digest(self.manifest)
        require(run["manifest_sha256"] == complete["manifest_sha256"] == mh and run["capture_enabled"]
                and run["enforce_eager"] and run["generation"] == self.manifest["generation"]
                and complete["rows"] == 36, "reference not complete/same native FP32 protocol")
        client_path = self.root/"client.jsonl"; clients = {}
        for event in lines(client_path):
            rid = event["logical_id"]
            require(rid in self.rows and rid not in clients and
                event["prompt_token_sha256"] == self.rows[rid]["input_ids_sha256"] and
                event["output_tokens"] == len(event["output_token_ids"]) == 4096, "client identity incomplete")
            clients[rid] = event
        require(set(clients) == set(self.rows), "missing reference client")
        expected = {(rid,l,t) for rid in self.rows for l in LAYERS for t in FULL_ANCHORS}
        self.index = {}; audits = []
        for rank in range(4):
            directory = self.root/f"rank-{rank}"; audit = directory/"events.jsonl"
            started = dispatch = turns = positions = 0; bindings = set(); done = set()
            refs = {"anchor":{},"future":{}}; rms_counts = {layer:0 for layer in LAYERS}
            for e in lines(audit,512*1024*1024):
                kind = e["event"]; require(e["rank"] == rank and kind != "capture_failed", "capture/rank failure")
                if kind == "worker_started":
                    started += 1; s = e["source"]
                    require(e["manifest_sha256"] == mh and s["tp_world"] == 4 and
                        s["logical_device"] == rank and s["physical_device"] == rank+4 and
                        s == lock["worker_sources"][rank] and {k:s[k] for k in COMMON} == source and e["state_dtype"] == "float32" and
                        e["native_state_layout"] == "Hv,Dv,Dk", "worker source/device/layout mismatch")
                elif kind == "worker_dispatch_verified":
                    dispatch += 1; entries = e["layers"]
                    require(len(entries) == 48 and {r["layer"] for r in entries} == set(LAYERS), "actual48 missing")
                    for r in entries:
                        require(r["instance_class"] == "vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn.QwenGatedDeltaNetAttention"
                            and r["class_sha256"] == BINDING_SOURCES.get(r["class_path"])
                            and r["core_owner"]["sha256"] == source["collector_sha256"]
                            and r["original_core_owner"]["sha256"] == source["gdn_sha256"]
                            and r["outer_forward_owner"]["sha256"] == source["gdn_sha256"], "actual receiver mismatch")
                elif kind == "request_bound":
                    rid = e["logical_id"]
                    require(rid in clients and rid not in bindings and e["runtime_id"] == clients[rid]["runtime_id"]
                        and e["prompt_token_sha256"] == clients[rid]["prompt_token_sha256"], "request binding mismatch")
                    bindings.add(rid)
                elif kind in refs:
                    key = (e["logical_id"],e["layer"],e["update"])
                    require(key in expected and key not in refs[kind], "unknown/duplicate anchor/future")
                    require((e["state_shape"] == [12,128,128] and e["split"] == self.rows[key[0]]["split"])
                        if kind == "anchor" else (e["shape"] == [256,12] and e["log_decay"] is True), "wrong anchor/future axes")
                    artifact = dict(e["artifact"]); p = (directory/artifact["path"]).resolve(strict=True)
                    size = STATE_BYTES if kind == "anchor" else 256*12*4
                    require(p.is_relative_to(directory) and p.is_file() and
                        p.stat().st_size == artifact["bytes"] == size, "outside/wrong size artifact")
                    artifact["path"] = str(p); refs[kind][key] = artifact
                elif kind == "layer_complete":
                    key = (e["logical_id"],e["layer"])
                    require(key not in done and e["anchors"] == list(FULL_ANCHORS), "incomplete/duplicate timeline")
                    done.add(key)
                elif kind == "turn_complete":
                    turns += 1; require(e["layers"] == list(LAYERS), "turn coverage missing")
                elif kind == "text_positions_verified":
                    positions += 1; require(e["native_arguments_unmodified"] is True and
                        e["mode"] in ("pure-text-1d","pure-text-mrope-3-identical-rows"), "unproven text positions")
                elif kind == "fit_rms_snapshot":
                    layer = e["layer"]
                    require(layer in rms_counts and e["count"] == rms_counts[layer]+1 and
                        e["shape"] == [12,128] and e["accumulation_dtype"] == "float64",
                        "fit RMS stream identity/sequence mismatch")
                    values = e["sum_mean_key_square"]
                    require(len(values) == 12 and all(len(v) == 128 and
                        all(math.isfinite(x) and x >= 0 for x in v) for v in values),
                        "invalid streamed fit RMS")
                    rms_counts[layer] += 1
                else:
                    raise ValueError("unknown capture audit event: "+str(kind))
            require(started == dispatch == 1 and bindings == set(self.rows) and turns > 0 and turns == positions
                and done == {(rid,l) for rid in self.rows for l in LAYERS}, "partial rank/request/layer evidence")
            require(all(set(v) == expected for v in refs.values()), "incomplete anchor/future matrix")
            require(all(count == 72 for count in rms_counts.values()), "partial fit RMS stream")
            for key in sorted(expected): self.index[(rank,*key)] = {kind:refs[kind][key] for kind in refs}
            audits.append(dict(rank=rank,path=str(audit),sha256=file_digest(audit),anchors=len(expected),futures=len(expected)))
        _,mr = read_json(manifest_path)
        self.provenance = dict(manifest=mr,manifest_semantic_sha256=mh,source=source,**lock,training=training,
            run=rr,complete=cr,client=dict(path=str(client_path),sha256=file_digest(client_path)),ranks=audits,
            artifact_index_sha256=digest([dict(key=list(k),**v) for k,v in sorted(self.index.items())]))

    def samples(self,rank,layer,split,torch):
        for row in self.partitions[split]:
            for step in FULL_ANCHORS:
                receipt = self.index[(rank,row["id"],layer,step)]; tensors = []
                for kind,shape in (("anchor",(12,128,128)),("future",(256,12))):
                    a = receipt[kind]; payload = Path(a["path"]).read_bytes()
                    require(len(payload) == a["bytes"] and hashlib.sha256(payload).hexdigest() == a["sha256"],
                            "reference artifact hash changed")
                    value = torch.frombuffer(bytearray(payload),dtype=torch.float32).clone().reshape(shape)
                    require(bool(torch.isfinite(value).all()), "nonfinite reference artifact")
                    tensors.append(value)
                yield row["id"],step,*tensors
