"""Source-bound external/internal IDs. No suffix guessing or runtime ID rewriting."""
from __future__ import annotations
import argparse
import inspect
import json
import os
from pathlib import Path
import re
from .contract import RESULT_ROOT,canonical,digest,file_digest,load_manifest,require,token_digest

NATIVE_SOURCES = {
    "/vllm-workspace/vllm/vllm/v1/engine/input_processor.py":
    "c5673988c0f7cfec268220e3f044e718702c015a4f236c020937cfd40a793f15",
    "/vllm-workspace/vllm/vllm/v1/engine/llm_engine.py":
    "2900f6732a1e507f6ced6f75f05f1fcaf2cc2929df0f5066574e9077ad3fbde1",
    "/vllm-workspace/vllm/vllm/v1/engine/output_processor.py":
    "464c3cda347512cf1090f8e6471d0d3f0f65e286eb9a7b97be52efbc1ffd572a",
}
ENGINE_SOURCE = "/vllm-workspace/vllm/vllm/v1/engine/llm_engine.py"
LEGACY_CONTAINER = "qwen36_damp_collector_tp4_20261006_v4"
LEGACY_ID = "4d28e606bfd804ddfbcb2835800d2f3a63b26fd528ac568e5401798f2e74b981"
LEGACY_IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"

def read_records(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

def exact_pair(external,internal):
    require(type(external) is str and bool(external) and type(internal) is str and
            re.fullmatch(re.escape(external)+r"-[0-9a-f]{8}",internal) is not None,
            "source-bound external + exact eight-hex internal ID required")

def source_identity():
    require(os.environ.get("VLLM_DISABLE_REQUEST_ID_RANDOMIZATION","0") == "0",
            "request-ID randomization must remain native and enabled")
    require(all(file_digest(path) == sha for path,sha in NATIVE_SOURCES.items()),
            "native request-ID source changed")
    return dict(schema="damp.request-identity/v1",native_sources=dict(NATIVE_SOURCES),
                identity_helper_sha256=file_digest(__file__),
                mechanism="instance-add_request-return-observer")

class Observer:
    """Observe the bound add_request return; forward original objects/arguments."""
    def __init__(self,original,manifest,emit):
        self.original,self.signature,self.emit = original,inspect.signature(original),emit
        self.rows = {r["input_ids_sha256"]:r for r in manifest["rows"]}
        require(len(self.rows) == len(manifest["rows"]), "nonunique prompt source")
        self.by_external,self.by_internal,self.seen_logical = {},{},set()

    def __call__(self,*args,**kwargs):
        call = self.signature.bind(*args,**kwargs)
        external,prompt,params = (call.arguments[k] for k in ("request_id","prompt","params"))
        require(type(external) is str and external not in self.by_external and
                isinstance(prompt,dict) and prompt.get("type") == "token" and
                prompt.get("prompt_embeds") is None and not prompt.get("multi_modal_data") and
                not prompt.get("encoder_prompt") and getattr(params,"n",None) == 1,
                "unsupported/nonunique native add_request input")
        ids = prompt["prompt_token_ids"]; fingerprint = token_digest(ids)
        require(fingerprint in self.rows, "add_request prompt outside immutable manifest")
        row = self.rows[fingerprint]
        require(row["id"] not in self.seen_logical and list(ids) == row["input_ids"],
                "logical replay or engine prompt mismatch")
        result = self.original(*args,**kwargs)
        exact_pair(external,result)
        require(result not in self.by_internal and token_digest(ids) == fingerprint,
                "internal ID collision or native prompt mutation")
        record = dict(logical_id=row["id"],external_request_id=external,runtime_id=result,
            prompt_token_sha256=fingerprint,origin="native-add_request-return",
            prompt_type="token",native_arguments_unmodified=True,native_return_unmodified=True)
        self.emit(record)
        self.by_external[external] = record; self.by_internal[result] = record
        self.seen_logical.add(row["id"])
        return result

    def output(self,external,row,prompt_ids):
        require(external in self.by_external, "output external ID has no observed add_request")
        record = self.by_external[external]
        require(record["logical_id"] == row["id"] and
            record["prompt_token_sha256"] == token_digest(prompt_ids) == row["input_ids_sha256"],
            "output prompt/external/internal identity mismatch")
        return record

    def complete(self):
        require(self.seen_logical == {row["id"] for row in self.rows.values()},
                "incomplete add_request observation coverage")

def install(engine,manifest,emit):
    identity = source_identity()
    require(type(engine).__module__ == "vllm.v1.engine.llm_engine" and
            type(engine).__qualname__ == "LLMEngine" and "add_request" not in engine.__dict__,
            "unsupported engine class/instance override")
    original = engine.add_request
    require(inspect.ismethod(original) and original.__self__ is engine and
            original.__func__.__qualname__ == "LLMEngine.add_request" and
            Path(inspect.getsourcefile(original.__func__)).resolve() == Path(ENGINE_SOURCE),
            "native add_request owning function mismatch")
    observer = Observer(original,manifest,emit)
    engine.add_request = observer
    return observer,identity

def live_identity(root,manifest,clients):
    root = Path(root); run = json.loads((root/"RUN.json").read_text())
    require(run.get("request_identity") == dict(schema="damp.request-identity/v1",
        native_sources=dict(NATIVE_SOURCES),identity_helper_sha256=file_digest(__file__),
        mechanism="instance-add_request-return-observer"), "missing/drifted live request identity")
    records = read_records(root/"request-identities.jsonl")
    expected = {r["id"]:r for r in manifest["rows"]}; logical,external,internal = set(),set(),set()
    for record in records:
        rid = record["logical_id"]; ext = record["external_request_id"]; runtime = record["runtime_id"]
        exact_pair(ext,runtime)
        require(rid in expected and rid not in logical and ext not in external and runtime not in internal and
            record["origin"] == "native-add_request-return" and record["prompt_type"] == "token" and
            record["native_arguments_unmodified"] is True and record["native_return_unmodified"] is True,
            "nonunique/unproven observation identity")
        client = clients[rid]
        require(client["external_request_id"] == ext and client["runtime_id"] == runtime and
            client["prompt_token_sha256"] == record["prompt_token_sha256"] == expected[rid]["input_ids_sha256"],
            "client/observer identity mismatch")
        logical.add(rid);external.add(ext);internal.add(runtime)
    require(logical == set(expected) and len(records) == len(expected), "partial identity observations")
    return dict(schema="damp.request-identity/v1",path=str(root/"request-identities.jsonl"),
                sha256=file_digest(root/"request-identities.jsonl"),native_sources=dict(NATIVE_SOURCES))

def legacy_source(path,root,dense_root,manifest):
    """Only the independently inspected, stopped original v4 two-request pair."""
    path = Path(path).resolve(strict=True); lock = json.loads(path.read_text())
    require(lock.get("schema") == "damp.legacy-v4-source/v1" and
        lock["container_name"] == LEGACY_CONTAINER and lock["container_id"] == LEGACY_ID and
        lock["image_id"] == LEGACY_IMAGE and Path(lock["on_root"]).resolve() == Path(root).resolve() and
        Path(lock["off_root"]).resolve() == Path(dense_root).resolve() and
        lock["manifest_semantic_sha256"] == digest(manifest), "legacy source/roots not original v4")
    require(Path(root).resolve() == RESULT_ROOT/"smoke-hook-v4-on" and
        Path(dense_root).resolve() == RESULT_ROOT/"smoke-hook-v4-off" and
        manifest["mode"] == "smoke" and len(manifest["rows"]) == 2,
        "legacy recovery restricted to original v4 pair")
    receipt = lock["docker_inspect"]; require(file_digest(receipt["path"]) == receipt["sha256"],
        "container inspection bytes changed")
    inspected = json.loads(Path(receipt["path"]).read_text())
    require(isinstance(inspected,list) and len(inspected) == 1, "exact one-container inspect required")
    entry = inspected[0]
    require(entry["Id"] == LEGACY_ID and entry["Image"] == LEGACY_IMAGE and
        entry["Name"] == "/"+LEGACY_CONTAINER and entry["State"]["Status"] == "exited" and
        entry["HostConfig"]["Privileged"] is False, "legacy inspected container identity/status mismatch")
    devices = entry["HostConfig"]["Devices"]
    physical = [(d["PathOnHost"],d["PathInContainer"]) for d in devices
                if re.fullmatch(r"/dev/davinci[0-9]+",d["PathOnHost"])]
    require(sorted(physical) == [(f"/dev/davinci{r+4}",f"/dev/davinci{r}") for r in range(4)],
            "legacy device mapping not exact physical4-7")
    require(set(lock["native_sources"]) == set(NATIVE_SOURCES), "three native source receipts required")
    for source,sha in NATIVE_SOURCES.items():
        r = lock["native_sources"][source]
        require(r["sha256"] == sha and file_digest(r["path"]) == sha, "legacy native source bytes changed")
    for directory in (Path(root),Path(dense_root)):
        require("request_identity" not in json.loads((directory/"RUN.json").read_text()),
                "not an original legacy run")
    return dict(path=str(path),sha256=file_digest(path),container_id=LEGACY_ID,
                image_id=LEGACY_IMAGE,native_sources=dict(NATIVE_SOURCES),
                docker_inspect=dict(receipt),source_receipts=lock["native_sources"])

def recover_bindings(manifest,clients,oracles,rank_bindings):
    """Pure strict join. External ID is known independently, never stripped."""
    ids = {r["id"] for r in manifest["rows"]}; expected = {r["id"]:r for r in manifest["rows"]}
    require(len(rank_bindings) == 4 and set(clients) == set(oracles) == ids, "legacy complete TP4/client identity required")
    recovered,external_seen,internal_seen = {},set(),set()
    for index,row in enumerate(manifest["rows"]):
        rid = row["id"]; live,oracle = clients[rid],oracles[rid]; ext = live["runtime_id"]
        require(ext == oracle["runtime_id"] == str(index) and ext not in external_seen and
            live["prompt_token_sha256"] == oracle["prompt_token_sha256"] == row["input_ids_sha256"] and
            live["output_token_ids"] == oracle["output_token_ids"] and
            live["output_tokens"] == oracle["output_tokens"] == manifest["generation"]["max_tokens"] and
            len(live["output_token_ids"]) == manifest["generation"]["max_tokens"] and
            token_digest(live["output_token_ids"]) == live["output_token_sha256"] == oracle["output_token_sha256"],
            "legacy external/prompt/output mismatch")
        across = []
        for rank,bindings in enumerate(rank_bindings):
            require(len(bindings) == len(ids) and {b["logical_id"] for b in bindings} == ids and
                all(b["rank"] == rank for b in bindings), "legacy missing/duplicate request bound")
            found = [b for b in bindings if b["logical_id"] == rid]
            require(len(found) == 1 and found[0]["prompt_token_sha256"] == row["input_ids_sha256"],
                    "legacy worker prompt mismatch")
            runtime = found[0]["runtime_id"];exact_pair(ext,runtime);across.append(runtime)
        require(len(set(across)) == 1 and across[0] not in internal_seen, "legacy rank disagreement/collision")
        recovered[rid] = dict(logical_id=rid,external_request_id=ext,runtime_id=across[0],
                             prompt_token_sha256=row["input_ids_sha256"])
        external_seen.add(ext);internal_seen.add(across[0])
    return recovered

def legacy_identity(root,dense_root,manifest,clients,oracles,source_path):
    receipt = legacy_source(source_path,root,dense_root,manifest)
    ranks = [[e for e in read_records(Path(root)/f"rank-{r}"/"events.jsonl")
              if e["event"] == "request_bound"] for r in range(4)]
    bindings = recover_bindings(manifest,clients,oracles,ranks)
    return bindings,dict(mode="explicit-readonly-legacy-v4-source-bound-recovery",source=receipt,
                         bindings=bindings,original_failure_preserved=True)

def audit_destination(output,root,dense_root):
    destination = Path(output).resolve()
    require(destination.is_relative_to(RESULT_ROOT) and destination != RESULT_ROOT and
        not destination.exists() and not destination.is_relative_to(Path(root).resolve()) and
        not destination.is_relative_to(Path(dense_root).resolve()),
        "legacy audit must be a new sibling directory, never inside original evidence")
    return destination

def legacy_audit(manifest_path,root,dense_root,source_path,output):
    from .validate import validate
    destination = audit_destination(output,root,dense_root)
    manifest = load_manifest(manifest_path)
    destination.mkdir(parents=False,exist_ok=False)
    try:
        result = validate(root,manifest,dense_root,legacy_source_path=source_path)
        raw = []
        for directory in (Path(root).resolve(),Path(dense_root).resolve()):
            for p in sorted(directory.rglob("*")):
                if p.is_file():
                    require(p.resolve().is_relative_to(directory), "legacy raw symlink outside root")
                    raw.append(dict(path=str(p),sha256=file_digest(p),bytes=p.stat().st_size))
        report = dict(schema="damp.legacy-v4-identity-audit/v1",status="identity_and_capture_audit_pass",
            manifest=dict(path=str(Path(manifest_path).resolve()),sha256=file_digest(manifest_path),semantic_sha256=digest(manifest)),
            validation=result,raw_receipts=raw,raw_receipts_sha256=digest(raw),
            no_original_evidence_modified=True,not_proven=["compressed recurrence","graph","E2E speedup","task accuracy"])
        with (destination/"AUDIT.json").open("xb") as f:f.write(canonical(report)+b"\n")
        with (destination/"VALIDATION.json").open("xb") as f:f.write(canonical(result)+b"\n")
        return dict(path=str(destination/"AUDIT.json"),sha256=file_digest(destination/"AUDIT.json"),status=report["status"])
    except Exception as error:
        with (destination/"FAILURE.json").open("xb") as f:f.write(canonical(dict(
            status="failed",error=type(error).__name__,detail=str(error),original_evidence_unchanged=True))+b"\n")
        raise

def main():
    p = argparse.ArgumentParser(description="Explicit read-only original-v4 identity audit; writes only NEW audit output")
    p.add_argument("--manifest",required=True);p.add_argument("--output-dir",required=True)
    p.add_argument("--on-root",required=True);p.add_argument("--off-root",required=True)
    p.add_argument("--legacy-source",required=True);a=p.parse_args()
    print(json.dumps(legacy_audit(a.manifest,a.on_root,a.off_root,a.legacy_source,a.output_dir),sort_keys=True))

if __name__ == "__main__":main()
