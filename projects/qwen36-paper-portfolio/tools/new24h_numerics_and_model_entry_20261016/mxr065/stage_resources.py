"""Source-bound CPU8GiB vs scoped model48GiB admission; original model/swap guards."""
import ast,hashlib,textwrap
def derive(body):
 if(len(body),hashlib.sha256(body).hexdigest())!=(22569,'8c83e08318b530c4d022b91bbacd34b12121b3380e1a14d32262c9a3875f6fa7'):raise ValueError('whole actual011 source')
 text=body.decode();tree=ast.parse(text);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='Controller');node=next(x for x in cls.body if isinstance(x,ast.FunctionDef)and x.name=='resources')
 original=textwrap.dedent('\n'.join(text.splitlines()[node.lineno-1:node.end_lineno]))
 changed=original;pairs=[(' mem={',' profile=self._mxr_resource_profile\n if profile not in (\'cpu-preflight\',\'model\'):raise ValueError(\'registered stage resource profile required\')\n guest_budget=8*c.GIB if profile==\'cpu-preflight\'else MEM\n mem={'),('(MEM if initial else 0)','(guest_budget if initial else 0)'),('actual ordinary RAM73GiB initial/9GiB live floor; HugeTLB never additive','actual registered CPU16.5GiB/model56.5GiB initial/9GiB live AND global swap-free; see actual memory fields'),('return dict(actual_output_scan_ref=','return dict(resource_profile=profile,guest_budget_bytes=guest_budget,host_budget_bytes=HOST_MEM,reserve_bytes=RESERVE,global_swap_free=(mem["SwapTotal"]==mem["SwapFree"]),actual_output_scan_ref='),(' c.require(mem["SwapTotal"]',' c.write(self.out/("RESOURCE-ADMISSION-%d.json"%time.time_ns()),dict(resource_profile=profile,memory=mem,guest_budget_bytes=guest_budget,host_budget_bytes=HOST_MEM,reserve_bytes=RESERVE,required_ordinary_bytes=RESERVE+HOST_MEM+(guest_budget if initial else 0),global_swap_free=(mem["SwapTotal"]==mem["SwapFree"]),initial=initial))\n c.require(mem["SwapTotal"]')]
 for before,after in pairs:
  if changed.count(before)!=(2 if before=='(MEM if initial else 0)'else 1):raise ValueError('exact resource function delta')
  changed=changed.replace(before,after)
 inverse=changed
 for before,after in reversed(pairs):inverse=inverse.replace(after,before)
 if inverse!=original:raise ValueError('whole resource function inverse')
 return original,changed,pairs
def install(S,Owned,c,ref):
 from pathlib import Path
 p=Path(ref['path']);raw=p.read_bytes()
 if str(Path(S.__file__).resolve())!=ref['path']or len(raw)!=ref['bytes']or c.sha(p)!=ref['sha256']:raise ValueError('actual immutable safety source')
 original,changed,pairs=derive(raw);scope=dict(S.Controller.resources.__globals__)
 exec(compile(changed,ref['path']+'#registered-stage-resource062','exec'),scope)
 S.Controller.resources=scope['resources']
 init=Owned.__init__;create=Owned.create_native
 def tracked(self,leaf):
  if leaf.name not in('cpu-preflight','cpu-consumer','candidate'):raise ValueError('registered exact owned stage')
  self._mxr_resource_profile='model'if leaf.name=='candidate'else'cpu-preflight'
  init(self,leaf)
 def create_stage(self,model,cpu):
  if type(cpu)is not bool or cpu!=(self._mxr_resource_profile=='cpu-preflight'):raise ValueError('create/admission stage mismatch')
  return create(self,model,cpu)
 Owned.__init__=tracked;Owned.create_native=create_stage
 return dict(schema='mxr.actual-stage-resources/v1',source=ref,CPU_initial_GiB=16.5,model_initial_GiB=56.5,live_GiB=9,global_swap_gate_unchanged=True,original_create_inspect_8_or64GiB_unchanged=False,actual_model_guest_GiB=48,actual_CPU_guest_GiB=8,actual_host_GiB=.5,actual_reserve_GiB=8,registered_function_deltas=len(pairs))
