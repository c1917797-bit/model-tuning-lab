"""One foreground CPU8 phase AFTER replayed actual capture stop-retain.
Existing host controller/child only. CPU checks never require a new NPU job idle.
"""
import argparse,json,os,sys,time
from pathlib import Path
import model_contract as c
from host_common import Joint,controller,child,fresh_leaf,outputs
def run(a,refs,m,model,start):
 import safety_host as S
 role=lambda name:m["runtime_roles"][name]
 core=c.module(role("release_core")["path"],role("release_core")["sha256"],"_mixed_cpu_release_core")
 release=c.module(role("release_replay")["path"],role("release_replay")["sha256"],"_mixed_cpu_release")
 capture_ref=c.bound(a.capture_result,a.capture_result_sha256);r=c.obj(capture_ref)
 term_ref=c.bound(a.capture_terminal,a.capture_terminal_sha256)
 whole_row=role("whole_cpu_consumer")
 whole=c.module(whole_row["path"],whole_row["sha256"],"_mixed_cpu_terminal_replay")
 actual,original=whole.terminal(core,capture_ref,term_ref,a.capture_peer,a.capture_operation,
  a.capture_command,core.decode(a.capture_args),5400)
 c.require(actual==r,"same complete original capture result")
 c.require(r["schema"]=="kivi.actual-mixed-owned-capture-host/v2" and
  r["status"]=="ALL16_CAPTURED_RELEASED_NUMERIC_PENDING" and r["source"]==refs["source"]
  and r["primary"]is None and r["secondary"]==[],"actual complete same-source capture terminal")
 markers=[]
 for line in original["stdout"].splitlines():
  try:v=core.decode(line)
  except(ValueError,TypeError):continue
  if type(v)is dict and set(v)=={"result","status"}:markers.append(v)
 c.require(markers==[dict(result=capture_ref,status=r["status"])],"original full terminal binds exact result")
 c.require(r["unchanged_source_after"]=={q["path"]:q["sha256"]for q in m["files"]},"capture source unchanged")
 ctx=release.make_context(refs["source"],core=core,core_ref=role("release_core"))
 npu=r["npu"];owned=c.obj(npu["owned"])
 stopped=ctx.cleanup(npu["cleanup"],owned,r["actual_host_process"]["pid"])
 cr=c.obj(npu["client_report"]);recipe=c.obj(npu["recipe"])
 c.require(cr["status"]=="ALL16_RAW_AND_NATIVE_FINAL_OBSERVED" and len(cr["capture_receipt_refs"])==16
  and len(cr["rank_final_refs"])==4 and cr["cpu_numeric_during_lease"]is False,"complete raw not sampled")
 seal=c.module(role("capture_receipt")["path"],role("capture_receipt")["sha256"],"_mixed_cpu_seal")
 for i,q in enumerate(cr["capture_receipt_refs"]):
  seal.validate(q,stage=i,plan_ref=recipe["capture_plan_ref"],identities=cr["rank_identities"],document=c.obj)
 capture_root=Path(capture_ref["path"]).parent
 c.require(capture_root.parent==c.PREP/"lowbit" and capture_root.name.startswith("run-kivi-mixed-")
  and capture_root.resolve()==capture_root and not capture_root.is_symlink(),"exact read-only actual capture root")
 c.CAPTURE_ACCOUNTING_ROOT=capture_root
 base_mounts=c.required_source_mounts
 def mounts():return sorted(set(base_mounts()+[str(capture_root)]))
 c.required_source_mounts=mounts
 co=Joint(start);Owned=controller(S,co);ctl=None;primary=None;clean=None;ch=None;result_ref=None;peer=None;recipe_ref=None
 try:
  leaf=fresh_leaf(a.output/"cpu-numeric");outputs(leaf)
  ctl=Owned(argparse.Namespace(output_dir=leaf),start)
  ctl.observe("independent-CPU8-preflight",initial=True)
  ctl.create(refs,dict(files={Path(q["path"]).name:q["sha256"]for q in m["files"]}),model,"cpu-preflight")
  actual,inspect_ref=ctl.inspect();core.raw_after_release(stopped,actual)
  peer=c.peer_module().publish(ctl,refs["source"],c.write)
  # Immutable lease is immediately visible to MAIN; another device job needs a
  # real peer-aware consumer and fresh summed admission, not this ref alone.
  print(json.dumps(dict(independent_CPU_peer_lease=peer,NPU_released=True)),flush=True)
  offline=c.module(role("offline_consume")["path"],role("offline_consume")["sha256"],"_mixed_offline_recipe_only")
  source_refs={name:role(name)for name in offline.ROLES}
  inputs=dict(schema="kivi.mixed-offline-numeric-recipe/v2",producer_ref=refs["source"],
   portfolio_cutoff_epoch=c.CUTOFF,cpu_deadline_epoch=min(c.CUTOFF,time.time()+ctl.remaining(cap=43200)),
   capture_plan_ref=recipe["capture_plan_ref"],rank_identities=cr["rank_identities"],
   capture_receipt_refs=cr["capture_receipt_refs"],rank_final_refs=cr["rank_final_refs"],
   npu_cleanup_ref=npu["cleanup"],npu_owned_ref=npu["owned"],
   actual_host_pid=r["actual_host_process"]["pid"],cpu_started_inspect_ref=inspect_ref,
   cpu_owned_ref=c.ref(leaf/"OWNED.json"),source_refs=source_refs,
   installer_sha256=role("installer")["sha256"],capture_sha256=role("provenance")["sha256"],
   observer_sha256=role("stage_observer")["sha256"])
  recipe_ref=c.write(leaf/"OFFLINE-RECIPE.json",inputs)
  args=[str(c.BASE/"cpu_entry.py"),"--execute","--source-manifest-sha256",refs["source"]["sha256"],
   "--recipe",recipe_ref["path"],"--recipe-sha256",recipe_ref["sha256"],"--output-dir",str(leaf)]
  ch=child(ctl,"independent-all16",args,43110,observe=True)
  result_ref=c.ref(leaf/"RESULT.json");result=c.obj(result_ref)
  c.require(result["status"]=="ALL16_STAGES_NUMERIC_AND_SCALAR_CONSUMED_AFTER_RELEASE","whole independent matrix")
  ctl.observe("independent-CPU8-complete")
 except BaseException as error:primary=error
 finally:
  if ctl is not None and ctl.cid:
   ctl.primary=primary
   try:clean=ctl.cleanup()
   except BaseException as error:co.secondary.append(repr(error))
   co.secondary.extend(ctl.secondary)
  co.secondary.extend(S.formal_time_failures(co.deadline))
  if co.cleanup_used>90:co.secondary.append("CPU joint cleanup90 exceeded")
  c.require(c.required_source_mounts is mounts,"exact owned mount adapter");c.required_source_mounts=base_mounts
  after={q["path"]:c.sha(q["path"])for q in m["files"]}
  report=dict(schema="kivi.actual-mixed-independent-cpu-host/v2",
   status="ALL16_CPU_CONSUMED_STOPPED_RETAINED"if primary is None and not co.secondary and result_ref else"failed",
   source=refs["source"],capture_result=capture_ref,capture_original_terminal=term_ref,
   exact_NPU_release_replayed=True,peer_lease=peer,offline_recipe=recipe_ref,CPU_phase_seconds=43200,cleanup_seconds=90,
   elapsed_seconds=time.monotonic()-start,cumulative_cleanup_seconds=co.cleanup_used,
   primary=repr(primary)if primary else None,secondary=co.secondary,child=ch,independent_result=result_ref,
   cpu_owned=c.ref(ctl.out/"OWNED.json")if ctl and ctl.cid else None,cpu_cleanup=clean,
   observations=ctl.observations if ctl else[],unchanged_source_after=after,
   actual_host_argv=["/usr/bin/python3","-I","-B",*sys.argv],
   actual_host_process=S.H.frozen().gate_process(os.getpid()),
   actual_memory_before=c.ref(ctl.out/"MEMORY-BEFORE.json")if ctl and (ctl.out/"MEMORY-BEFORE.json").is_file()else None,
   actual_memory_after=c.ref(ctl.out/"MEMORY-AFTER.json")if ctl and (ctl.out/"MEMORY-AFTER.json").is_file()else None,
   Devices=[],NPU_release_claim=False,raw_deleted=False,
   original_whole_CPU_terminal_consumer_required=True,model_ready=False,performance_ready=False,run_authority=False)
  rr=c.write(a.output/"RESULT.json",report)
 print(json.dumps(dict(result=rr,status=report["status"])),flush=True)
 if primary:raise primary
 c.require(not co.secondary and result_ref,"actual CPU failures retained");return rr
