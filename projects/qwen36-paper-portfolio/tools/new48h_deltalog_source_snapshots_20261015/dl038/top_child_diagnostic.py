"""Proposed narrow departure predicate; NOT installed into old/live scope."""
def departed(pid,ppid,init_pid,selected_pids,proven_owned_parents,snapshots,fresh_top,fresh_smi):
 if pid==init_pid or pid in selected_pids:raise ValueError('never retire init/selected NPU PID')
 if ppid not in proven_owned_parents:raise ValueError('original top child not linked to proven owned parent')
 if len(snapshots)!=2 or any(s.get('status')!='missing'for s in snapshots):raise ValueError('live/unreadable/reused PID is not proven departed')
 if pid in fresh_top or pid in fresh_smi:raise ValueError('still observed process')
 return dict(classification='original-top-transient-child-confirmed-departed',pid=pid,ppid=ppid,owned_release_authority=False,protected_boundary_waived=False)
