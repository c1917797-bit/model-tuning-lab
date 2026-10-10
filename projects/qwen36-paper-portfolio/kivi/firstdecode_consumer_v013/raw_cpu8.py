"""One CPU8 invocation of the original full64 raw consumer after exact TP4 release.
No Controller implementation or numerical/reference code is copied here.
"""
import os,resource,sys,time
from pathlib import Path
def run(a,ctx,core,start):
 c=ctx.c;p=core.producer_only(a,ctx);r=p["r"]
 core.need(time.time()+5400<=c.CUTOFF,"independent full raw5400 fit before fixed total cutoff")
 # Bind only exact already SHA-qualified real modules, never stubs/foreign aliases.
 core.need("model_contract"not in sys.modules,"foreign raw host model_contract namespace")
 sys.modules["model_contract"]=c
 srow=ctx.own["safety_host.py"];hrow=ctx.own["host_run.py"]
 S=core.source_module(srow,"safety_host")
 H=core.source_module(hrow,"_kivi_raw_existing_host")
 output=c.ordinary(a.raw_phase_output)
 core.need(output.parent==c.PREP/"lowbit"and output.name.startswith("run-kivi-firstdecode-independent-raw-")
  and not output.exists(),"one fresh exact independent raw output")
 core.need(a.output.parent==output,"entry output belongs to exact new raw packet")
 # Original model/readonly source audit, no Torch/candidate math/model load.
 model=c.model(r["model_manifest"])
 host=H.c.module(c.H8,c.DEPS[str(c.H8)],"_sparq_tp4_frozen_host").cpu_view(os.getpid())
 os.sched_setaffinity(0,{min(host["effective_cpus"])})
 soft,hard=resource.getrlimit(resource.RLIMIT_AS)
 core.need(hard==resource.RLIM_INFINITY,"original Docker child AS hard restore")
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,hard))
 source_map=dict(files={Path(q["path"]).name:q["sha256"]for q in ctx.m["files"]})
 refs=dict(source=ctx.producer,component=r["component"],software=r["software"])
 refs["model-manifest"]=r["model_manifest"]
 co=H.Joint(start);Owned=H.controller(S,co);ctl=None;primary=None;raw=None;child=None;clean=None
 original_mounts=c.required_source_mounts
 input_root=Path(p["rr"]["path"]).parent
 core.need(input_root.resolve()==input_root and not input_root.is_symlink()and input_root.is_dir()
  and input_root.parent==c.PREP/"lowbit"and input_root.name.startswith("run-kivi-model-firstdecode-"),
  "exact actual producer packet readonly, no broad parent mount")
 def required_raw_mounts():
  # Only this already fully consumed immutable model packet. Raw nested binaries
  # cannot be discovered from a shallow one-file RESULT mount.
  return sorted(set(original_mounts()+[str(input_root)]))
 c.required_source_mounts=required_raw_mounts
 try:
  H.fresh_leaf(output);leaf=H.fresh_leaf(output/"cpu-preflight");H.outputs(leaf)
  ctl=Owned(type("RawArgs",(),dict(output_dir=leaf))(),start)
  ctl.observe("raw-CPU8-preflight",initial=True)
  ctl.create(refs,source_map,model,"cpu-preflight")
  after_create=ctl.inspect()[0]
  core.raw_after_release(p["npu_stopped"],after_create)
  client_json=leaf/"CLIENT_REF.json";c.write(client_json,p["npu"]["client_report"])
  args=[str(c.BASE/"consume_raw.py"),"--execute","--source-manifest-sha256",ctx.producer["sha256"],
        "--client-ref-json",str(client_json),"--output",str(leaf/"RAW_RESULT.json")]
  # Original no-device CPU child path: all source/full64 scalar work unchanged.
  # No per-row sampling, no candidate import. Original whole bound reserves90cleanup.
  child=H.child(ctl,"raw-full64",args,5310,observe=False)
  raw=c.ref(leaf/"RAW_RESULT.json")
  core.raw_result(c.obj(raw),ctx.producer,p["npu"]["client_report"],p["client"],ctx.m)
  ctl.observe("raw-CPU8-complete")
 except BaseException as error:primary=error
 finally:
  if ctl is not None and ctl.cid:
   ctl.primary=primary
   try:clean=ctl.cleanup()
   except BaseException as error:co.secondary.append(repr(error))
   co.secondary.extend(ctl.secondary)
  co.secondary.extend(S.formal_time_failures(co.deadline))
  if co.cleanup_used>90:co.secondary.append("independent raw joint90cleanup exceeded")
  core.need(c.required_source_mounts is required_raw_mounts,"own raw source-mount adapter identity")
  c.required_source_mounts=original_mounts
  meta=dict(schema="kivi.actual-firstdecode-raw-owned-host/v1",
   source=ctx.producer,consumer_source=core.ref(Path(__file__).parent/"SOURCE_MANIFEST.json"),
   original_model_result=p["rr"],original_model_terminal=p["tr"],
   status="RAW_FULL64_WITH_EXACT_CPU8_CLEANUP"if primary is None and not co.secondary and raw else"failed",
   primary=repr(primary)if primary else None,secondary=co.secondary,phase_seconds=5400,cleanup_seconds=90,
   elapsed_seconds=time.monotonic()-start,cumulative_cleanup_seconds=co.cleanup_used,
   readonly_input_root=str(input_root),original_raw_result=raw,original_raw_child=child,
   raw_cpu8_owned=c.ref(ctl.out/"OWNED.json")if ctl and ctl.cid else None,raw_cpu8_cleanup=clean,
   actual_host_process=S.H.frozen().gate_process(os.getpid()),
   actual_host_argv=["/usr/bin/python3","-I","-B",*sys.argv],
   raw_observations=ctl.observations if ctl else[],
   producer_source_after={q["path"]:c.sha(q["path"])for q in ctx.m["files"]},
   raw_checker_full64_unchanged=True,model_ready=False,performance_ready=False,run_authority=False,whole176=False)
  mr=c.write(output/"RAW_OWNER_RESULT.json",meta)
 if primary:raise RuntimeError("original raw first-fault retained "+str(mr))from primary
 core.need(meta["status"]=="RAW_FULL64_WITH_EXACT_CPU8_CLEANUP","raw secondary/cleanup failure "+str(mr))
 return mr

