"""Thin serial TP4 short-GDN successor of actual008 Controller; default OFF."""
import argparse,ast,hashlib,importlib.util,json,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
LOW=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit')
DEPLOY=LOW/'_draft_damp_operator_reuse/NEW48H/mxr-working-domain-model-new48h-v1-043-repair2'
DONOR=LOW/'mxr-r118-proc-snapshot-repair-20261013-008'
OUT=Path('/opt/host/vnf/austinov/run-mxr-working-domain-model043-repair2-main-NEW48H_001')
START,CUT,PHASE=1791962297,1792135097,2700
AUTH=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/NEW48H_AUTHORITY_20261014.json')
AUTH_SHA='71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99'
HOST_REF=dict(path=str(DONOR/'host_ticket.py'),bytes=25508,sha256='c1a26afb164af8fcf4b88fef24a524c2c890be772f56f136b5edc5006b1ff066')
OBSERVER_REF=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/R162_protected_observer/observer.py',bytes=6275,sha256='fafdb2685481d3e1c77dad977156cf3ed4838e515d6c3a4a4d4042751f0c216f')
FROZEN_HELPER_REF=dict(path='/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py',bytes=33743,sha256='ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86')
def need(v,m):
 if not v:raise ValueError(m)
def exact(r):
 p=Path(r['path']);b=p.read_bytes();need(p.is_absolute()and not p.is_symlink()and set(r)=={'path','bytes','sha256'}and (len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'exact whole frozen Ref3');return b
def leaf(name):
 p=HERE/name;s=importlib.util.spec_from_file_location('_mxr042_host_'+name[:-3],p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def source(digest):
 b=(HERE/'SOURCE_MANIFEST.json').read_bytes();need(hashlib.sha256(b).hexdigest()==digest,'exact new042 source')
 m=json.loads(b);need(m['root']==str(HERE)and m['window']==dict(start=START,cutoff=CUT)and m['default_enabled']is False and m['schema']=='mxr.diag16.full-gdn-frame-bridge-source/v1','actual current R156 source')
 for r in[*m['files'].values(),*m['dependencies']]:exact(r)
 leaf('admit042.py').gate(m['actual042_owner_ref'])
 return m
def adapt(text,sr,pr):
 need((len(text.encode()),hashlib.sha256(text.encode()).hexdigest())==(HOST_REF['bytes'],HOST_REF['sha256']),'actual008 byte identity')
 identity=json.loads((HERE/'SOURCE_MANIFEST.json').read_bytes())['runtime_identity']
 need(set(identity)=={'owner','container_prefix','run_id'}and identity['owner']==identity['run_id']and identity['container_prefix'].endswith('-'),'registered complete identity')
 pairs=[
 ('DEPLOY = PREP / "lowbit/mxr-r118-proc-snapshot-repair-20261013-008"','DEPLOY = PREP / "lowbit/_draft_damp_operator_reuse/NEW48H/mxr-working-domain-model-new48h-v1-043-repair2"',1),
 ('OUT = PREP / "lowbit/run-mxr-r118-native-capture-20261013-008"','OUT = Path("/opt/host/vnf/austinov/run-mxr-working-domain-model043-repair2-main-NEW48H_001")',1),
 ('R118_NEW12H_AUTHORITY_20261013.json','NEW48H_AUTHORITY_20261014.json',1),
 ('32b3d57baa8f5f843d95675de57e0e8d5579dd8766c9d3d9bd320f834af05a72',AUTH_SHA,1),
 ('START, CUTOFF = 1791879730, 1791922930','START, CUTOFF = 1791962297, 1792135097',1),
 ('facade.CUT = "2026-10-13T20:22:10+00:00"','facade.CUT = "2026-10-16T07:18:17+00:00"',1),
 ('S.OWNER = "mxr-r118-native-capture008"','S.OWNER = '+json.dumps(identity['owner']),1),
 ('self.name = "mxr-r118-capture008-" + leaf.name','self.name = '+json.dumps(identity['container_prefix'])+' + leaf.name',1),
 ('need(free >= S.RESERVE + (S.WORKSPACE if initial else 0), "actual Docker root storage reserve")','_EXTERNAL.docker_gate(self, S, free, initial)',1),
 ('value = super().resources(initial)','value = super().resources(initial)\n            need(value["output_bytes"] <= 4*1024**3, "new short-GDN complete output cap4GiB; original free-disk reserve intact")',1),
 ('load(HERE / "protected_snapshot_policy.py", sha(HERE / "protected_snapshot_policy.py")','load(_DONOR / "protected_snapshot_policy.py", sha(_DONOR / "protected_snapshot_policy.py")',1),
 ('str(SOURCE3):(str(SOURCE3),False), str(DEPLOY):(str(DEPLOY),False), str(UP):(str(UP),False),','str(SOURCE3):(str(SOURCE3),False), str(DEPLOY):(str(DEPLOY),False), str(UP):(str(UP),False), **_READ_MOUNTS,',1),
 ('[str(DEPLOY / "guest_probe.py"), "--execute", "--mode", "cpu",\n            "--source3", str(SOURCE3), "--upstream", str(UP), "--output", str(cpu.out / "CPU.json")]','[str(DEPLOY / "parser_probe.py"), "--execute", "--source-ref", _SOURCE_JSON, "--prerequisite-ref", _PREREQUISITE_JSON,\n            "--source3", str(SOURCE3), "--upstream", str(UP), "--output", str(cpu.out / "CPU.json")]',1),
 ('[str(DEPLOY / "guest_probe.py"), "--execute", "--mode", "n1",\n            "--source3", str(SOURCE3), "--upstream", str(UP), "--output", str(ctl.out / "CANARY.json")]','[str(DEPLOY / "parser_probe.py"), "--execute", "--mode", "n1", "--source-ref", _SOURCE_JSON, "--prerequisite-ref", _PREREQUISITE_JSON,\n            "--source3", str(SOURCE3), "--upstream", str(UP), "--output", str(ctl.out / "CANARY.json")]',1),
 ('[str(SOURCE1 / "cold_entry.py"), "--source-root", str(SOURCE1),\n            "--installed-ascend-root", "/vllm-workspace/vllm-ascend/vllm_ascend"]','[str(DEPLOY / "software.py"), "--execute", "--source-ref", _SOURCE_JSON, "--output", str(cpu.out / "BRIDGE-SOFTWARE.json")]',1),
 ('result["cpu"] = dict(initial=initial, report=c.ref(cpu.out / "CPU.json"), cleanup=close_owned(cpu, c))','_bridge_sw = c.obj(c.ref(cpu.out / "BRIDGE-SOFTWARE.json"))\n        need(all(_bridge_sw["actual_IPC_controls"][k] is True for k in ("actual_Linux_AF_UNIX","direct_UUID4_scan_consume_pass","nested_original_rejection_pass","bad_basename_original_rejection_pass")) and _bridge_sw["external_output_cases"] == 8 and _bridge_sw["external_output_all_pass"] is True and _bridge_sw["actual_rootfs_write_errno"] == 30 and _bridge_sw["actual_cases"] == _SOFTWARE_CASES and _bridge_sw["all_pass"] is True and _bridge_sw["source"] == source_ref and _bridge_sw["Devices"] == [] and _bridge_sw["NPU"] is False, "current actual cold10 before model")\n        result["cpu"] = dict(initial=initial, bridge_software=c.ref(cpu.out / "BRIDGE-SOFTWARE.json"), report=c.ref(cpu.out / "CPU.json"), cleanup=close_owned(cpu, c))',1),
 ('need(canary["mode"] == "n1" and canary["pass_preflight"] and len(canary["canaries"]) == 4, "all4 actual tiny prerequisite")','need(canary["mode"] == "n1" and canary["pass_preflight"] and len(canary["canaries"]) == 4 and canary["source"] == source_ref and canary["component_prerequisite"] == _PREREQUISITE_REF and canary["runtime_parser_executed"] is True and canary["receiver_registered"] is True and canary["canary_preceded_parser"] is True, "actual all4 tiny then real parser/platform/receiver before weights")',1),
 ('run_id = "mxr-r118-native-capture008"','run_id = '+json.dumps(identity['run_id']),1),
 ('args = [str(DEPLOY / "server_boot.py"), "--execute", "--mode", "capture", "--capture-source", str(SOURCE1),','args = [str(DEPLOY / "entry.py"), "--execute", "--role", "guest", "--source-ref", _SOURCE_JSON, "--prerequisite-ref", _PREREQUISITE_JSON, "--capture-source", str(SOURCE1),',1),
 ('[str(SOURCE3 / "capture_client.py"), "--execute", "--model-config",','[str(DEPLOY / "entry.py"), "--execute", "--role", "client", "--source-ref", _SOURCE_JSON, "--prerequisite-ref", _PREREQUISITE_JSON, "--model-config",',1),
 ('case = c.obj(c.ref(worker / "case-000/CASE.json"))','case = c.obj(c.ref(worker / "frame-000/FRAME.json"))',1),
 ('not (worker / "case-000/FAILURE.json").exists()','not (worker / "frame-000/FAILURE.json").exists()',1),
 ('case=c.ref(worker / "case-000/CASE.json")','first_frame=c.ref(worker / "frame-000/FRAME.json")',1),
 ('[str(SOURCE1 / "consume_capture.py"), "--worker-root", row["worker_root"],\n                "--out-root", str(output), "--run-id", run_id, "--expected-cases", "1"]','[str(DEPLOY / "consume.py"), "--execute", "--source-ref", _SOURCE_JSON, "--prerequisite-ref", _PREREQUISITE_JSON, "--worker-root", row["worker_root"],\n                "--output", str(output), "--run-id", run_id]',1),
 ('report_ref = c.ref(output / "RESULT.json")','report_ref = c.ref(output / "BRIDGE_RESULT.json")',1),
 ('report["schema"] == "mxr.capture.independent-consumer/v1" and report["run_id"] == run_id\n                 and report["original_native_gate_pass"] is True and report["cases"] == 1\n                 and report["mxr_qualified"] is False and report["performance_ready"] is False',
  'report["schema"] == "mxr.observerless-once-GDN-independent/v1" and report["run_id"] == run_id\n                 and report["gdn_frame_gate_pass"] is True and len(report["layer_prefixes"]) == 48\n                 and report["model_logits_qualified"] is False and report["performance_ready"] is False',1),
 ('result["independent_FP64_original_solve_consumers"] = reports','result["actual48_GDN_output_state_consumers"] = reports\n        result["short_all4_48GDN_gate"] = _all4_layers(c, reports, capture_rows)',1),
 ('schema="mxr.actual-native-capture-host/v1"','schema="mxr.observerless-once-short48-owned-host/v1", component_prerequisite=_PREREQUISITE_REF',1),
 ('"NATIVE_FRAMES_AND_FP64_CONSUMED"','"ACTUAL004_ONCE_SHORT48_CONSUMED_NOT_MODEL"',1)]
 out=text
 for old,new,count in pairs:need(out.count(old)==count,'registered thin008 delta '+old[:48]);out=out.replace(old,new)
 inverse=out
 for old,new,count in reversed(pairs):need(inverse.count(new)==count,'unique inverse delta');inverse=inverse.replace(new,old)
 need(inverse==text,'whole008 byte inverse; resource/identity/cleanup/math other guards unchanged')
 return out,pairs
def all4_layers(c,reports,bindings):
 need([x['rank']for x in reports]==[0,1,2,3]and [x['rank']for x in bindings]==[0,1,2,3],'complete distinct actual TP4 groups')
 values=[c.obj(x['result'])for x in reports]
 need(all(v['pid']==b['namespace_pid']and v['worker_root']==b['worker_root']and v['gdn_frame_gate_pass']is True for v,b in zip(values,bindings)),'CPU consume anchored actual loaded-worker PID/root')
 sets=[set(v['layer_prefixes'])for v in values];need(all(len(s)==48 and s==sets[0]for s in sets),'all4 actual same48 GDN layer prefixes')
 return dict(scope='all4-one129-prefill48GDN-output-state',passed=True,graph_qualified=False,long32768_qualified=False,full_physical_cache_qualified=False,model_logits_qualified=False)
def bind(sr,pr,readset):
 text,pairs=adapt(exact(HOST_REF).decode(),sr,pr)
 h=types.ModuleType('_mxr042_actual008_private');h.__file__=str(HERE/'host_ticket.py');h._DONOR=DONOR;h._EXTERNAL=leaf('external_output_policy.py');h._SOURCE_JSON=json.dumps(sr,separators=(',',':'));h._PREREQUISITE_REF=pr;h._PREREQUISITE_JSON=json.dumps(pr,separators=(',',':'));h._all4_layers=all4_layers;h._SOFTWARE_CASES=leaf('ownership_observation.py').SOFTWARE_CASES
 # Tight RO parent mounts, collapsing descendants. Only the three original
 # owner-created leaves retain RW. No extra broad experiment-root mount.
 parents={Path(r['path']).parent for r in readset};parents.add(DONOR)
 parents={p for p in parents if not any(q!=p and q in p.parents for q in parents)}
 h._READ_MOUNTS={str(p):(str(p),False)for p in parents}
 exec(compile(text,HOST_REF['path'],'exec'),h.__dict__)
 need(h.START==START and h.CUTOFF==CUT and h.PHASE==PHASE and h.CLEANUP_TOTAL==270 and h.HERE==HERE and h.DEPLOY==DEPLOY and h.OUT==OUT,'actual private cold globals')
 previous=h.frozen_directory
 def current(root,digest):
  if root!=h.HERE:return previous(root,digest)
  value=source(digest)
  for r in readset:exact(r)
  return value
 h.frozen_directory=current;return h,pairs
def protect_cleanup(h):
 """Install AFTER original008 snapshot signature proof, in same private F.
 No ownership scope/CPU/RAM/FD/time/cleanup predicate is removed or replaced.
 """
 original=h.safety
 def safety(sr,policy,started):
  base,S,Owned,state=original(sr,policy,started)
  manifest=json.loads((HERE/'SOURCE_MANIFEST.json').read_bytes())
  state['scoped_cap48_provider']=leaf('cap48_provider.py').prepare(S,base)
  state['stage_resource_contract']=leaf('stage_resources.py').install(S,Owned,base,manifest['ownership_observation_refs']['safety'])
  state['external_output_policy']=leaf('external_output_policy.py').install(S,Owned,base,h.OUT,manifest['ownership_observation_refs']['safety'])
  state['stage_resource_contract'].update(model_initial_GiB=56.5,CPU_initial_GiB=16.5,model_guest_GiB=48,host_GiB=.5,reserve_GiB=8,original64GiB_immutable=True)
  audit=leaf('ownership_observation.py')
  state['ownership_preassert_diagnostic']=audit.install(S,base,manifest['ownership_observation_refs']['safety'],manifest['ownership_observation_refs']['helper'])
  state['actual_memory_observer']=leaf('memory_observer.py').install(Owned,base,S)
  exact(OBSERVER_REF);observer=h.load(OBSERVER_REF['path'],OBSERVER_REF['sha256'],'_mxr043_MAIN_protected_observer')
  actors=[];init=Owned.__init__
  def tracked(self,leaf):init(self,leaf);actors.append(self)
  Owned.__init__=tracked
  # h.OUT is MAIN's already-created sole root. The source-qualified helper
  # writes expired-row proof here; no source or foreign output becomes RW.
  state['protected_observer']=observer.install(S.H,FROZEN_HELPER_REF,h.OUT,base.write,lambda:([h.os.getpid()],[c.cid for c in actors if c.cid]))
  chain=audit.validate_chain(S,Owned,state['ownership_preassert_diagnostic'])
  state['ownership_observation_chain']=base.write(h.OUT/'OWNERSHIP_OBSERVER_CHAIN.json',chain)
  return base,S,Owned,state
 h.safety=safety;return h
def main(argv=None):
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--source-sha256');p.add_argument('--prerequisite-ref');a=p.parse_args(argv)
 if not(a.execute or a.source_audit):print(json.dumps(dict(enabled=False,NPU=False,hardware_ready=False)));return 0
 m=source(a.source_sha256);R=leaf('prerequisite.py');need(a.prerequisite_ref,'actual prior039 whole consumed Ref required');pr=json.loads(a.prerequisite_ref);passed=R.gate(pr)
 sr=dict(path=str(HERE/'SOURCE_MANIFEST.json'),bytes=(HERE/'SOURCE_MANIFEST.json').stat().st_size,sha256=a.source_sha256)
 refs=[sr,pr,*m['files'].values(),*m['dependencies'],*passed['readset']]
 for r in refs:exact(r)
 h,pairs=bind(sr,pr,refs);protect_cleanup(h)
 if a.source_audit:
  need('torch'not in sys.modules and 'torch_npu'not in sys.modules,'only source/actual-original consumer, no runtime');print(json.dumps(dict(source=sr,component_prerequisite=pr,readset=len(refs),registered_inverse_deltas=len(pairs),NPU=False,resource_admitted=False)));return 0
 need(HERE==DEPLOY,'actual Linux new scope; no local Docker')
 return h.main(['--execute','--source-sha256',a.source_sha256])
if __name__=='__main__':raise SystemExit(main())
