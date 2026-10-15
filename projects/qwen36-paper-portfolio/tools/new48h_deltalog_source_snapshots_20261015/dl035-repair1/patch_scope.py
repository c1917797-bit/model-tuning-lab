"""Exact reversible source transform; old module and observer002 untouched."""
import ast,hashlib
OLD_SHA='432f5cc1613ef5faf43aca11e68c17c3957919d45978cdff04003b82598a5157'
BEFORE="""                for pid in pids:
                    proof=lane.h.gate_process(pid);m.require(lane.active in proof['cgroup'],'actual top PID owned cgroup')
"""
AFTER="""                top_ppids={int(line.split()[0]):int(line.split()[1]) for line in top_receipt['stdout'].splitlines() if len(line.split())>=2 and line.split()[0].isdigit() and line.split()[1].isdigit()}
                owned_parents={x['State']['Pid']}
                forbidden={row[2] for row in lane.h.legacy().process_rows(raw)}
                forbidden.update(p['pid'] for p in lane.pid_proofs.values())
                for pid in pids:
                    proof=_adapter_top_guard.classify(lane,pid,top_ppids[pid],x['State']['Pid'],owned_parents,forbidden,m)
                    if proof is None:continue # separately proven departed child, never owned release
                    m.require(lane.active in proof['cgroup'],'actual top PID owned cgroup')
                    owned_parents.add(pid)
"""
def transform(raw):
 assert hashlib.sha256(raw).hexdigest()==OLD_SHA,'exact original scope source'
 text=raw.decode();assert text.count(BEFORE)==1
 changed=text.replace(BEFORE,AFTER);assert changed.replace(AFTER,BEFORE)==text
 ast.parse(changed);return changed
def install(adapter,helper):
 """Call on freshly loaded private scope before host wires _adapter_protected.

 Caller must source-check helper and this patch in new029 manifest/readset.
 No shared module/runtime mutation; only this private adapter function object.
 """
 import inspect,pathlib
 raw=pathlib.Path(adapter.__file__).read_bytes();changed=transform(raw);tree=ast.parse(changed)
 fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='protected_observation')
 ns=dict(adapter.__dict__,_adapter_top_guard=helper);code=ast.Module(body=[fn],type_ignores=[]);ast.fix_missing_locations(code);exec(compile(code,str(adapter.__file__)+':registered-top-child028','exec'),ns)
 adapter.protected_observation=ns['protected_observation']
 return dict(original_sha256=OLD_SHA,mechanical_inverse=True,protected_observer002_unchanged=True)
