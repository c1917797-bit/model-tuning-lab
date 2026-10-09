"""Exact current ANN component-to-model handoff; stdlib, never a native PASS.
Binds complete native source bytes, original whole operation and explicit CLI.
No old27/v4/v7/partial witness or old aggregate grants model authority.
"""
import ast,json,re
from pathlib import Path
import source_contract as c
CURRENT=dict(path=str(c.KERNEL/"SOURCE_MANIFEST.json"),sha256="eb7ed908879c6bdea7fab670bcf83e570a7439045e2d8e5c4535c6a41611f528")
PINNED={
 "consume_numeric.py": "d670f4aabc53ac22d1a020501487e6274cc5d2ce7e2e01b65800250216a8cd13",
 "ann_matrix_consumer.py": "e7e8a7c03992d26cbf9277d3515d570880ccd83e5246b84aa5e69ce3e34b1a87",
 "matrix.py": "02484f6fecd08548f4eebac5eb39e6552affc4b0fc2c3a8591fff86eac3f56d4",
 "receipt.py": "689f7c4fab787af26a09d75fb193bde952790ebfb6931c9aba52cb9a7f3be9e7",
 "host.py": "7bb55de8fe25f07a401bf202b5d3e4517da8116fb02fafcf77acd999b4cebe59",
 "original_terminal.py": "ed085d5c90aaceaa430a09211b1d85e2f5fc3d270e73319a11d3d04191378fb1",
 "ann_workspace.py": "3393fbd9552a2ec7fb914b472cb5ec00aa95025de9051433e372fe0b2e92e46e",
 "literal_author.py": "1468b55c25aa99132d3f7d7dcbd9ead7b0b88c4707d08d999a9754312eb21602",
 "independent_oracle.py": "6ed5f73deffc1790f6c6c54806181956248a6042080ca10ead8116abb7e4e945",
 "cpu_smoke.py": "aefa644f72ec7db1bdd7550bc3d7941f9f092f587d4a2af000211014d292bfa6"
}
PROPOSED=dict(CURRENT) # Byte review of actual frozen source; not numerical authority.
CONSUME_ARGS=("root","terminal_path","terminal_sha","proof_path","peer","source","files","host_result","host_result_sha")
def signature(raw):
 node=next(x for x in ast.parse(raw).body if isinstance(x,ast.FunctionDef) and x.name=="consume")
 c.require(not node.args.posonlyargs and not node.args.kwonlyargs and not node.args.defaults and
  node.args.vararg is None and node.args.kwarg is None and tuple(x.arg for x in node.args.args)==CONSUME_ARGS,
  "actual exact nine-argument source consumer; no guessed/union interface")
 return CONSUME_ARGS
def manifest(m,source):
 c.require(source==CURRENT and c.KERNEL_SHA==CURRENT["sha256"] and
  m["schema"]=="sparq.token-preparation/v9-author-ann-FP32-compensation" and m["source_count"]==42 and len(m["files"])==31 and
  all(m["files"].get(n)==s for n,s in PINNED.items()) and
  m["registered_author_successor"]["protocol"]==c.AUTHOR_PROTOCOL and
  m["registered_author_successor"]["stage_equality"]=="strict original two torch.equal predicates; independent fixed-capacity per-request FP32 SUM layout explicitly registered; no tolerance/epsilon" and
  m["execution_clock"]==c.NATIVE_EXECUTION_CLOCK and
  m["original_relative_rms"]==.005 and m["original_cosine"]==.99998 and m["graph_trials"]==3 and
  m["portfolio_cutoff"]=="2026-10-09T11:17:31Z" and m["paper_cutoff"]=="2026-10-08T19:00:00Z" and
  m["registered_author_successor"]["original_author_BF16_dual_gate"].startswith("FAILED") and
  m["registered_author_successor"]["protocol"]==c.AUTHOR_PROTOCOL,
  "current byte-bound native41/31, exact original math/limits/trials/cutoff; no dynamic old manifest union")
 return dict(source=source,source_count=42,own_count=31,precision_contract=c.AUTHOR_PROTOCOL,cases=128,steps=20480,ready=False)
def proposed_source_interfaces():
 """Byte-audit only: this Ref is not the actual canonical manifest or PASS."""
 m=c.obj(PROPOSED);out=manifest(m,CURRENT)
 out.update(proposed_only=True,canonical_applied_verified=False,model_permission=False)
 return out
def source_interfaces():
 m=c.obj(CURRENT);out=manifest(m,CURRENT)
 for n,s in PINNED.items():c.bound(c.KERNEL/n,s)
 out["consume_args"]=list(signature((c.KERNEL/"consume_numeric.py").read_text()))
 original=ast.parse((c.KERNEL/"original_terminal.py").read_text())
 c.require(any(isinstance(x,ast.FunctionDef) and x.name=="original_terminal" for x in original.body),
  "whole original reader exists, not flattened fabricated receipt")
 return out
def exact_consumer_cli(host_ref,terminal_ref,output):
 """For MAIN after genuine native terminal success; does NOT execute or grant.
 Full independent consume_numeric must still execute and emit its v8 artifact.
 """
 source_interfaces()
 host=c.obj(host_ref);c.require(host["execution_clock"]==c.NATIVE_EXECUTION_CLOCK,"exact new source-bound native repair clock")
 from original_terminal import original_terminal
 origin=original_terminal(c.obj(terminal_ref),"lgw_a6109c51076a4a2c9d2674ca5a8704a0")
 record=origin["record"];root=Path(host["output_dir"]);proof=host["source_device_proof"]
 c.require(host["schema"]=="sparq.token-host-result/v4" and host["status"]=="kernel_numerics_checked" and
  host["source_manifest"]==CURRENT and host["primary_error"] is None and host["secondary_errors"]==[] and
  host["sources_before"]==host["sources_after"]==c.obj(CURRENT)["files"] and
  host_ref["path"]==str(root/"RESULT.json") and root.resolve()==root and Path("/cache/cch") in root.parents,
  "actual new original complete numeric host result only")
 expected=["/usr/bin/python3","-B",str(c.KERNEL/"numeric_gate.py"),"--host-execute","--source-manifest",CURRENT["path"],
  "--source-manifest-sha256",CURRENT["sha256"],"--output",str(root)]
 c.require([record["command"],*record["args"]]==host["actual_host_argv"]==host["expected_host_argv"]==expected,
  "whole original exact native producer CLI -> immutable host result")
 marks=[x for x in record["stdout"].splitlines() if x.startswith("MAIN_SPARQ_TOKEN_V5_HOST ")]
 m=c.obj(CURRENT)
 c.require(len(marks)==1 and json.loads(marks[0].split(" ",1)[1])==dict(result=host_ref,status="kernel_numerics_checked",
  source_manifest=CURRENT,host_script_sha256=m["files"]["host.py"],entry_script_sha256=m["files"]["numeric_gate.py"]),
  "original complete terminal marker, not extracted/flattened boolean")
 c.bound(proof["path"],proof["sha256"]);p=Path(output)
 c.require(p.is_absolute() and p.resolve()==p and Path("/cache/cch") in p.parents and p.parent.is_dir() and
  not p.exists() and not p.is_symlink() and ".." not in p.parts,"new exclusive actual numerical consumer output")
 argv=["/usr/bin/python3","-B",str(c.KERNEL/"consume_numeric.py"),"--execute","--shard",str(root/"gate"),
  "--terminal",terminal_ref["path"],"--terminal-sha256",terminal_ref["sha256"],"--proof",proof["path"],
  "--source-manifest",CURRENT["path"],"--source-manifest-sha256",CURRENT["sha256"],
  "--expected-peer","lgw_a6109c51076a4a2c9d2674ca5a8704a0","--host-result",host_ref["path"],
  "--host-result-sha256",host_ref["sha256"],"--output",str(p)]
 return dict(argv=argv,host_result=host_ref,original_terminal=terminal_ref,source=CURRENT,
  original_operation_id=origin["operation_id"],numerical_consumer_not_executed=True,model_permission=False,ready=False)
def readonly_component_mounts(component_ref):
 """Exact four original authority Refs plus complete prior owned output tree.
 Uses c.component() FIRST; mounts are data access, never device permission.
 """
 x=c.component(component_ref,replay=False);host=c.obj(x["host_result"]);prior=Path(host["output_dir"])
 c.require(prior.resolve()==prior and prior.is_dir() and Path("/cache/cch") in prior.parents and not prior.is_symlink(),
  "exact actual previous owned native output, no broad cache mount")
 refs=[component_ref,*[x[n] for n in ("original_terminal","host_result","actual_report","native_no_device_abi")]]
 mounts={str(prior):(str(prior),False)}
 for r in refs:
  c.bound(r["path"],r["sha256"]);p=Path(r["path"])
  if prior not in p.parents:mounts[str(p)]=(str(p),False)
 return mounts
