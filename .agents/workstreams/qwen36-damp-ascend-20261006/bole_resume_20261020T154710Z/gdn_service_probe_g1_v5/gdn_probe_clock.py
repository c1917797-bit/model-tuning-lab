"""Original main-entry/callee clock and inherited MAIN flock; no admission."""
import ast
import os
from pathlib import Path
import stat
import time

LOCK='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/MAIN_ADMISSION.lock'

PHASE=3600
CLEANUP=180
CREATE_CAP=60
CUTOFF=1792597630


def phase_admission(C,entry_start):
    C.need(type(entry_start)in(int,float)and C.CUT==CUTOFF,'original fixed source-owned cutoff')
    now=time.monotonic();remaining=min(entry_start+PHASE-now,C.CUT-time.time())-CLEANUP
    C.need(now>=entry_start and remaining>=CREATE_CAP,'cold source/readset work consumes original3600; original180cleanup and create60 must still fit, never reset')
    return remaining


def controller_admission(C,c,S,ctl,entry_start):
    C.need(S.PHASE==PHASE and S.CLEANUP==CLEANUP and c.CUTOFF==CUTOFF and
        ctl.created_monotonic==entry_start and ctl.deadline==entry_start+PHASE,
        'same actual main entry reaches original Joint/controller deadline and fixed cutoff')
    # Exact original remaining() already subtracts CLEANUP. Do not reserve it twice.
    C.need(ctl.remaining(cap=CREATE_CAP)==CREATE_CAP,'before create original capped60 must fit after original cleanup reserve; no renewed start')


def validate(text):
    tree=ast.parse(text);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
    need=lambda v,m:None if v else(_ for _ in()).throw(ValueError(m))
    need(ast.dump(main.body[0],include_attributes=False)==ast.dump(ast.parse('entry_start=time.monotonic()').body[0],include_attributes=False),'actual first main statement cold entry before parser/source/predecessor/hash')
    stores=[n.id for n in ast.walk(main)if isinstance(n,ast.Name)and isinstance(n.ctx,ast.Store)]
    need(stores.count('entry_start')==stores.count('start')==1,'exact one entry and one start alias, no clock renewal')
    alias=[n for n in ast.walk(main)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='start'for t in n.targets)]
    need(len(alias)==1 and isinstance(alias[0].value,ast.Name)and alias[0].value.id=='entry_start','source hashing cannot reset start')
    calls=[n for n in ast.walk(main)if isinstance(n,ast.Call)]
    rendered=[ast.unparse(n)for n in calls]
    for wanted in('H.Joint(start)','H.controller(S, joint)(argparse.Namespace(output_dir=leaf), start)',
                   'controller_admission(C, c, S, ctl, entry_start)','phase_admission(C, entry_start)',
                   'ctl.cleanup()','S.formal_time_failures(joint.deadline)','held_main_lock(C)'):
        need(wanted in rendered,'exact original shared time/lifecycle seam '+wanted)
    before=next(n for n in calls if ast.unparse(n)=='phase_admission(C, entry_start)')
    source=next(n for n in calls if ast.unparse(n.func)=='C.source')
    load=next(n for n in calls if ast.unparse(n.func)=='load')
    need(source.lineno<before.lineno<load.lineno,'cold prehash admission before actual ownership helpers')
    ctl_for=next(n for n in ast.walk(main)if isinstance(n,ast.FunctionDef)and n.name=='ctl_for')
    local=[n for n in ast.walk(ctl_for)if isinstance(n,ast.Call)]
    observe=next(n for n in local if ast.unparse(n.func)=='ctl.observe')
    admit=next(n for n in local if ast.unparse(n.func)=='controller_admission')
    create=next(n for n in local if ast.unparse(n.func)=='create')
    need((observe.lineno,observe.col_offset)<(admit.lineno,admit.col_offset)<(create.lineno,create.col_offset),'observe then same remaining gate then create; no early cpu/expected reads')
    elapsed=next(n for n in calls if ast.unparse(n.func)=='dict'and any(k.arg=='elapsed'for k in n.keywords))
    need(next(ast.unparse(k.value)for k in elapsed.keywords if k.arg=='elapsed')=='time.monotonic() - start','reported elapsed uses original main entry, not retrofitted historical data')
    return dict(schema='bole.GDN-probe-actual-main-cold-clock-source/v3',phase_seconds=PHASE,shared_cleanup_seconds=CLEANUP,fixed_cutoff=CUTOFF,create_cap_seconds=CREATE_CAP,one_main_entry_clock=True,source_hashes_in_phase=True,deadline_renewal_forbidden=True,NPU=False)


def held_main_lock(C):
    """Observe the inherited outer flock; never open/acquire/create a new lock."""
    path = Path(LOCK)
    C.need(path.is_file() and not any(p.is_symlink() for p in (path, *path.parents)) and
           stat.S_IMODE(path.stat().st_mode) == 0o600, 'actual ordinary0600 MAIN lock')
    identity = path.stat()
    fds = []
    for descriptor in Path('/proc/self/fd').iterdir():
        try:
            value = descriptor.stat()
            if (value.st_dev, value.st_ino) == (identity.st_dev, identity.st_ino) and os.readlink(descriptor) == LOCK:
                fds.append(int(descriptor.name))
        except FileNotFoundError:
            continue
    lines = []
    for line in Path('/proc/locks').read_text().splitlines():
        values = line.split()
        if len(values) >= 8 and values[1:4] == ['FLOCK', 'ADVISORY', 'WRITE'] and values[4] == str(os.getpid()):
            parts = values[5].split(':')
            if len(parts) == 3 and int(parts[0], 16) == os.major(identity.st_dev) and int(parts[1], 16) == os.minor(identity.st_dev) and int(parts[2]) == identity.st_ino:
                lines.append(line)
    C.need(fds and len(lines) == 1, 'outer MAIN flock --no-fork inherited by this exact owner PID')
    return dict(path=LOCK, host_pid=os.getpid(), inherited_FDs=sorted(fds), actual_proc_locks=lines,
                lock_acquired_by_this_helper=False, inherited_MAIN_lock_verified=True)
