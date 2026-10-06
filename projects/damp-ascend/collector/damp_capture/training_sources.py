"""Pinned TRAIN-only download plan; explicit bounded fetch, never model execution."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import urllib.request
from .contract import INPUT_ROOT, canonical, file_digest, require

# Identity pins were read from the publishers' immutable HF commit LFS pointers.
PLAN = {
    "schema": "damp-training-source-plan/v1",
    "status": "metadata-only-not-downloaded",
    "root": "/cache/cch/qwen36-damp-20261006/calibration-inputs/source-v1",
    "maximum_total_bytes": 134217728,
    "artifacts": [
        {
            "domain": "math",
            "dataset": "MATH",
            "repository": "EleutherAI/hendrycks_math",
            "revision": "7811dc4cf37bd3a0384adc84f33da0695629b4dc",
            "path": "algebra/train-00000-of-00001.parquet",
            "size": 505186,
            "sha256": "73347f5b55869f21ff094361025dbd12d291e971aa4d72142eacee10438e449f",
            "license": "MIT",
            "format": "parquet",
            "split": "train",
            "provenance_url": "https://huggingface.co/datasets/EleutherAI/hendrycks_math/commit/7811dc4cf37bd3a0384adc84f33da0695629b4dc",
            "resolve_url": "https://huggingface.co/datasets/EleutherAI/hendrycks_math/resolve/7811dc4cf37bd3a0384adc84f33da0695629b4dc/algebra/train-00000-of-00001.parquet"
        },
        {
            "domain": "math",
            "dataset": "MATH",
            "repository": "EleutherAI/hendrycks_math",
            "revision": "7811dc4cf37bd3a0384adc84f33da0695629b4dc",
            "path": "counting_and_probability/train-00000-of-00001.parquet",
            "size": 329354,
            "sha256": "d37ae017930df41678edee50dcde18c17fb06afaff9eb505c1b95f1002bfcb31",
            "license": "MIT",
            "format": "parquet",
            "split": "train",
            "provenance_url": "https://huggingface.co/datasets/EleutherAI/hendrycks_math/commit/7811dc4cf37bd3a0384adc84f33da0695629b4dc",
            "resolve_url": "https://huggingface.co/datasets/EleutherAI/hendrycks_math/resolve/7811dc4cf37bd3a0384adc84f33da0695629b4dc/counting_and_probability/train-00000-of-00001.parquet"
        },
        {
            "domain": "math",
            "dataset": "MATH",
            "repository": "EleutherAI/hendrycks_math",
            "revision": "7811dc4cf37bd3a0384adc84f33da0695629b4dc",
            "path": "geometry/train-00000-of-00001.parquet",
            "size": 549388,
            "sha256": "9dbf5e5b55499e696e0ba72da9d85d4f0be3acbf7eaa6cb014b0fc78bb63784f",
            "license": "MIT",
            "format": "parquet",
            "split": "train",
            "provenance_url": "https://huggingface.co/datasets/EleutherAI/hendrycks_math/commit/7811dc4cf37bd3a0384adc84f33da0695629b4dc",
            "resolve_url": "https://huggingface.co/datasets/EleutherAI/hendrycks_math/resolve/7811dc4cf37bd3a0384adc84f33da0695629b4dc/geometry/train-00000-of-00001.parquet"
        },
        {
            "domain": "math",
            "dataset": "MATH",
            "repository": "EleutherAI/hendrycks_math",
            "revision": "7811dc4cf37bd3a0384adc84f33da0695629b4dc",
            "path": "intermediate_algebra/train-00000-of-00001.parquet",
            "size": 575154,
            "sha256": "0c87f3798ebdfb915b1f9b6fc13c1a8d064c3cb91631ccbe85b83ed5d71150f6",
            "license": "MIT",
            "format": "parquet",
            "split": "train",
            "provenance_url": "https://huggingface.co/datasets/EleutherAI/hendrycks_math/commit/7811dc4cf37bd3a0384adc84f33da0695629b4dc",
            "resolve_url": "https://huggingface.co/datasets/EleutherAI/hendrycks_math/resolve/7811dc4cf37bd3a0384adc84f33da0695629b4dc/intermediate_algebra/train-00000-of-00001.parquet"
        },
        {
            "domain": "math",
            "dataset": "MATH",
            "repository": "EleutherAI/hendrycks_math",
            "revision": "7811dc4cf37bd3a0384adc84f33da0695629b4dc",
            "path": "number_theory/train-00000-of-00001.parquet",
            "size": 308653,
            "sha256": "81c08649149b39811f2d1d7ddf5dfccf6c4c8044a2e169cfb24db09160c941f4",
            "license": "MIT",
            "format": "parquet",
            "split": "train",
            "provenance_url": "https://huggingface.co/datasets/EleutherAI/hendrycks_math/commit/7811dc4cf37bd3a0384adc84f33da0695629b4dc",
            "resolve_url": "https://huggingface.co/datasets/EleutherAI/hendrycks_math/resolve/7811dc4cf37bd3a0384adc84f33da0695629b4dc/number_theory/train-00000-of-00001.parquet"
        },
        {
            "domain": "math",
            "dataset": "MATH",
            "repository": "EleutherAI/hendrycks_math",
            "revision": "7811dc4cf37bd3a0384adc84f33da0695629b4dc",
            "path": "prealgebra/train-00000-of-00001.parquet",
            "size": 383626,
            "sha256": "765b526fb5c0b8385cb7be2c16bf4f6f28cf71f2bc15c826abfbb5fa7f8616cc",
            "license": "MIT",
            "format": "parquet",
            "split": "train",
            "provenance_url": "https://huggingface.co/datasets/EleutherAI/hendrycks_math/commit/7811dc4cf37bd3a0384adc84f33da0695629b4dc",
            "resolve_url": "https://huggingface.co/datasets/EleutherAI/hendrycks_math/resolve/7811dc4cf37bd3a0384adc84f33da0695629b4dc/prealgebra/train-00000-of-00001.parquet"
        },
        {
            "domain": "math",
            "dataset": "MATH",
            "repository": "EleutherAI/hendrycks_math",
            "revision": "7811dc4cf37bd3a0384adc84f33da0695629b4dc",
            "path": "precalculus/train-00000-of-00001.parquet",
            "size": 353745,
            "sha256": "28bb1ff95525c8d32521509bef91de76339659f5467a381e6e8deea204538f0e",
            "license": "MIT",
            "format": "parquet",
            "split": "train",
            "provenance_url": "https://huggingface.co/datasets/EleutherAI/hendrycks_math/commit/7811dc4cf37bd3a0384adc84f33da0695629b4dc",
            "resolve_url": "https://huggingface.co/datasets/EleutherAI/hendrycks_math/resolve/7811dc4cf37bd3a0384adc84f33da0695629b4dc/precalculus/train-00000-of-00001.parquet"
        },
        {
            "domain": "general",
            "dataset": "ARC-Challenge",
            "repository": "allenai/ai2_arc",
            "revision": "16644173ab25fa007c815e3204a8b59a4034ba1b",
            "path": "ARC-Challenge/train-00000-of-00001.parquet",
            "size": 189909,
            "sha256": "e488c1587ffdcfc8443f916c53488a95cd471c5790e0746c6bfe4cecf20962cb",
            "license": "CC-BY-SA-4.0",
            "format": "parquet",
            "split": "train",
            "provenance_url": "https://huggingface.co/datasets/allenai/ai2_arc/commit/16644173ab25fa007c815e3204a8b59a4034ba1b",
            "resolve_url": "https://huggingface.co/datasets/allenai/ai2_arc/resolve/16644173ab25fa007c815e3204a8b59a4034ba1b/ARC-Challenge/train-00000-of-00001.parquet"
        },
        {
            "domain": "code",
            "dataset": "APPS",
            "repository": "codeparrot/apps",
            "revision": "96f5ad5809536245073fa8180815a5bf108878cb",
            "path": "train.jsonl",
            "size": 107101272,
            "sha256": "45e82ef22ed8e7c0c04d881a21b923e9dd233157896b0b8d5b3493e887499cae",
            "license": "CC-BY-SA-3.0",
            "license_provenance": "https://arxiv.org/html/2105.09938#A1",
            "format": "jsonl",
            "split": "train",
            "provenance_url": "https://huggingface.co/datasets/codeparrot/apps/commit/96f5ad5809536245073fa8180815a5bf108878cb",
            "resolve_url": "https://huggingface.co/datasets/codeparrot/apps/resolve/96f5ad5809536245073fa8180815a5bf108878cb/train.jsonl"
        }
    ]
}


def artifact_path(root, artifact):
    return Path(root) / artifact["repository"].replace("/", "--") / artifact["revision"] / artifact["path"]


def validate_plan(plan=PLAN):
    require(plan["maximum_total_bytes"] == 128 * 1024 * 1024, "budget drift")
    require(len(plan["artifacts"]) == 9 and sum(a["size"] for a in plan["artifacts"]) <=
            plan["maximum_total_bytes"], "artifact budget/cardinality differs")
    require({a["dataset"] for a in plan["artifacts"]} == {"MATH", "APPS", "ARC-Challenge"},
            "training domains differ")
    for a in plan["artifacts"]:
        require(a["split"] == "train" and "train" in Path(a["path"]).name and
                "test" not in a["path"] and "validation" not in a["path"],
                "only audited TRAIN artifacts")
        require(a["size"] > 0 and len(a["sha256"]) == 64 and len(a["revision"]) == 40,
                "immutable sha/size/revision required")
        require(a["license"] and a["provenance_url"], "license/source provenance absent")
    return plan


def index_for(root):
    root = Path(root).resolve()
    require(root.is_relative_to(INPUT_ROOT.resolve()), "dataset bytes must remain outside Git")
    artifacts = []
    for a in validate_plan()["artifacts"]:
        path = artifact_path(root, a)
        require(path.is_file() and path.stat().st_size == a["size"] and
                file_digest(path) == a["sha256"], "missing or changed TRAIN artifact")
        artifacts.append(dict(a, artifact_path=str(path)))
    return dict(schema="damp-training-source-index/v1", artifacts=artifacts,
                total_bytes=sum(a["size"] for a in artifacts),
                provenance="publisher-pinned-train-only", download_scope="no-final-evaluation")


def download(root, mirror=None, transport="urllib"):
    root = Path(root).resolve()
    require(root.is_relative_to(INPUT_ROOT.resolve()) and root != INPUT_ROOT.resolve(),
            "refuse broad/outside data root")
    plan = validate_plan()
    require(not (root / "SOURCE_INDEX.json").exists(), "source index exists; never overwrite")
    require(all(not artifact_path(root,a).exists() for a in plan["artifacts"]),
            "partial/old artifacts require explicit audited recovery, not auto retry")
    if mirror is not None:
        require(mirror == "https://hf-mirror.com",
                "only explicit byte-identical mirror is admitted")
    require(transport in ("urllib", "curl"), "unsupported verified TLS transport")
    for a in plan["artifacts"]:
        url = a["resolve_url"] if mirror is None else a["resolve_url"].replace(
            "https://huggingface.co", mirror, 1)
        if transport == "curl":
            # Host urllib and libcurl use different TLS trust stores here.
            # Use the independently checked system curl, NEVER -k/unverified TLS.
            response = subprocess.run([
                "/usr/bin/curl", "-4", "--fail", "--location", "--silent",
                "--show-error", "--max-redirs", "3", "--connect-timeout", "5",
                "--max-time", "120", "--max-filesize", str(a["size"]), url],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=130)
            require(response.returncode == 0, "verified curl TRAIN fetch failed: " +
                    response.stderr.decode("utf-8", errors="replace"))
            payload = response.stdout
        else:
            request = urllib.request.Request(url, headers={"User-Agent": "model-tuning-lab-damp-train-v1"})
            with urllib.request.urlopen(request, timeout=30) as response:
                length = response.headers.get("Content-Length")
                require(length is None or int(length) == a["size"], "server size differs")
                payload = response.read(a["size"] + 1)
        require(len(payload) == a["size"] and hashlib.sha256(payload).hexdigest() == a["sha256"],
                "download hash/size differs; no unaudited corpus substitution")
        path = artifact_path(root,a)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(payload)
        print(json.dumps(dict(dataset=a["dataset"], path=a["path"], bytes=len(payload),
                              sha256=a["sha256"]), sort_keys=True))
    index = index_for(root)
    with (root / "SOURCE_INDEX.json").open("xb") as stream:
        stream.write(canonical(index) + b"\n")
    return index


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=PLAN["root"])
    p.add_argument("--download", action="store_true", help="explicit bounded TRAIN fetch; default metadata only")
    p.add_argument("--audit-local", action="store_true")
    p.add_argument("--mirror", choices=["https://hf-mirror.com"])
    p.add_argument("--transport", choices=["urllib", "curl"], default="urllib")
    a = p.parse_args()
    require(not (a.download and a.audit_local), "choose fetch or local audit")
    if a.download:
        result = download(a.root,a.mirror,a.transport)
    elif a.audit_local:
        result = index_for(a.root)
    else:
        result = validate_plan()
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
