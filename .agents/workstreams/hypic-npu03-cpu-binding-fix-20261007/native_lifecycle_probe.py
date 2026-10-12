#!/usr/bin/env python3
"""Process-local installed/uninstalled identity, no plugin registration or NPU work."""
import argparse, hashlib, importlib.metadata as md, importlib.util, json
from pathlib import Path
def probe(expect):
    try:
        dist=md.distribution("hypic-vllm-ascend-plugin")
    except md.PackageNotFoundError:
        dist=None
    spec=importlib.util.find_spec("hypic_vllm_ascend")
    eps=[(x.name,x.value) for x in md.entry_points(group="vllm.general_plugins")
         if x.name=="hypic_vllm_ascend"]
    installed=dist is not None and spec is not None
    if expect=="installed":
        assert installed and dist.version=="0.8.5"
        assert str(Path(spec.origin).resolve())=="/opt/hypic/hypic_vllm_ascend/__init__.py"
        assert eps==[("hypic_vllm_ascend","hypic_vllm_ascend:register")]
    else:
        assert dist is None and spec is None and eps==[], "plugin still discoverable"
    base=Path(importlib.util.find_spec("vllm_ascend").origin).parent
    runner=base/"worker/model_runner_v1.py"
    manifest=Path("/opt/hypic/MANIFEST.json")
    return dict(expect=expect, installed=installed, entrypoints=eps,
                module_origin=spec.origin if spec else None,
                framework_runner=str(runner),
                framework_runner_sha256=hashlib.sha256(runner.read_bytes()).hexdigest(),
                manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
                versions={n:md.version(n) for n in ["vllm","vllm-ascend","torch","torch-npu"]},
                live_worker_object_probe=False)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--expect",choices=["installed","absent"],required=True)
    p.add_argument("--output",required=True);a=p.parse_args()
    result=probe(a.expect)
    with open(a.output,"x") as f: json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps(result))
