"""No proof means bounded waiting, never ownership acceptance or lease renewal."""
def match_or_wait(device,proofs,*,expected_argv,cid,child_running,now,deadline):
 if not child_running or now>=deadline:raise ValueError('same live child and original handshake deadline')
 ticks=int(device['stat'][device['stat'].rfind(')')+2:].split()[19])
 if not proofs:return None
 matches=[v for v in proofs if v['namespace_pids']and v['namespace_pids'][-1]==device['pid']and v['physical']==4 and v['start_ticks']==ticks and cid in v['cgroup']and v['argv']==expected_argv]
 if not matches or len({(v['pid'],v['start_ticks'])for v in matches})!=1:raise ValueError('actual precise PID/start/cgroup/argv ownership')
 return matches[-1]
