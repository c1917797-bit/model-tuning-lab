"""Reversible 2k qualification-only taps and independent consumer. No source binding."""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,s):
 if not v:raise ValueError(s)
def once(t,a,b):
 need(t.count(a)==1,'one exact numeric2k operand '+a[:80]);return t.replace(a,b,1)
OBSERVER_METHODS="""
    def _actual_digest(self,value):
        import short_state_digest as D
        need(self.C.ref(D.__file__)==self.m['files']['short_state_digest.py'],'actual full-byte NPU witness helper')
        return D.tensor_digest(self.t,value)

    def fa_operands(self,b,kwargs,record):
        need(self.current is not None and b['index']==self.current['order'][-1]and
             b['kind']=='fa'and b['index']not in self.current['captures'],'one real BEFORE-FIA operand event')
        need(all(isinstance(kwargs[k],self.t.Tensor)and kwargs[k].device.type=='npu'
             for k in('query','key','value','atten_mask','block_table')),'actual NPU call operands, no CPU fixtures')
        proof=dict(schema='bole.actual-2k-FIA-operands/v1',owner=clone(self.t,self.current['owner']),
            layer=b['index'],source=record['source'],stage='original',boundary_completed=False,
            query_BF16_digest=self._actual_digest(kwargs['query']),
            native_before=self._capture({k:kwargs[k]for k in('key','value','atten_mask','block_table')}))
        self.current['captures'][b['index']]=dict(kind='fa',actual_2k_FIA_operands=proof)

    def fa_converted(self,b,converted):
        proof=self.current['captures'][b['index']]['actual_2k_FIA_operands']
        need(proof['stage']=='original','one actual pre-delegate conversion event')
        proof['converted_before']={k:self._actual_digest(converted[k])for k in('query','key','value','atten_mask','block_table')}
        proof['stage']='converted'

    def fa_returned(self,b,converted):
        proof=self.current['captures'][b['index']]['actual_2k_FIA_operands']
        need(proof['stage']=='converted','same actual real delegate return')
        proof['converted_after']={k:self._actual_digest(converted[k])for k in('query','key','value','atten_mask','block_table')}
        need(proof['converted_before']==proof['converted_after'],'actual full converted operator inputs remain unchanged')
        proof['stage']='returned'

    def fa_completed(self,b,record):
        proof=self.current['captures'][b['index']]['actual_2k_FIA_operands']
        need(proof['stage']=='returned'and record['completed']is True and
             record['source']==proof['source']and record['prefix_length']==proof['owner']['length'],
             'same actual finished source-owned FIA boundary')
        proof['boundary_completed']=True

"""
def adapt(files):
 before=dict(files);out=dict(files)
 def edit(name,a,b):out[name]=once(out[name].decode(),a,b).encode()
 edit('fastpath_numeric_consumer.py',
  "    need(C.ref(__file__)==m['files']['fastpath_numeric_consumer.py'],'actual source-owned independent consumer')",
  "    need(C.ref(__file__)==m['files']['fastpath_numeric_consumer.py'],'actual source-owned independent consumer')\n    import numeric_prefix_2k as PREFIX\n    need(C.ref(PREFIX.__file__)==m['files']['numeric_prefix_2k.py'],'actual source-owned independent 2k numeric domain')\n    PREFIX.require_runtime_admission(C,m,frame)\n    PREFIX.frame_domain(frame)")
 edit('fastpath_numeric_consumer.py',
  "            before=before_f[i];after=after_f[i];N.fa_owner(before,after,row,owner)",
  "            before=before_f[i];after=after_f[i];N.fa_owner(before,after,row,owner)\n            _D,_digest=actual_cpu_digest(C,m)\n            metric['actual_private_scratch']=PREFIX.scratch(t,C,m,row,before,owner,_digest)")
 edit('fastpath_numeric_consumer.py',
  "    if previous is not None:",
  "    if previous is not None:\n        PREFIX.fixed_pages(previous,frame)")
 edit('fastpath_numeric_observer.py','input_tokens=131,output_tokens=','input_tokens=2048,output_tokens=')
 edit('fastpath_numeric_observer.py',"type(p['output_tokens'])is int and p['output_tokens']in(8,160,1024)",
  "type(p['output_tokens'])is int and p['output_tokens']==1024")
 edit('fastpath_numeric_observer.py',
  "        p=m['fastpath_numeric_qualification']",
  "        import numeric_prefix_2k as PREFIX\n        need(C.ref(PREFIX.__file__)==m['files']['numeric_prefix_2k.py'],'source-owned 2k independent domain')\n        PREFIX.require_runtime_admission(C,m,None)\n        p=m['fastpath_numeric_qualification']")
 edit('fastpath_numeric_observer.py',
  "        self.current['captures'][b['index']]=self._capture(dict(kind='fa',query=query,key=key,value=value,\n            output=output,actual_physical_pages=physical_pages,actual_cache_identities=cache_identities))",
  "        row=self.current['captures'][b['index']]\n        need(row['actual_2k_FIA_operands']['stage']=='returned'and row['actual_2k_FIA_operands']['boundary_completed']is True,'actual operand witness before completed FA capture')\n        row.update(self._capture(dict(kind='fa',query=query,key=key,value=value,\n            output=output,actual_physical_pages=physical_pages,actual_cache_identities=cache_identities)))")
 edit('fastpath_numeric_observer.py',"    def close(self):",OBSERVER_METHODS+"    def close(self):")
 edit('service_bridge.py',
  " out,_=self.A.native(t,boundary,trial,actual_fia,sparse_mode=1)",
  " if qual is not None:boundary.qualification_probe=(qual,b)\n out,_=self.A.native(t,boundary,trial,actual_fia,sparse_mode=1)")
 edit('service_fia.py',
  "  converted=dict(kwargs);before={}",
  "  probe=getattr(self,'qualification_probe',None)\n  if probe is not None:probe[0].fa_operands(probe[1],kwargs,self.record)\n  converted=dict(kwargs);before={}")
 edit('service_fia.py',
  "  result=self.delegate.npu_fused_infer_attention_score(**converted)",
  "  if probe is not None:probe[0].fa_converted(probe[1],converted)\n  result=self.delegate.npu_fused_infer_attention_score(**converted)\n  if probe is not None:probe[0].fa_returned(probe[1],converted)")
 edit('service_fia.py',
  "  self.record['completed']=True",
  "  self.record['completed']=True\n  if probe is not None:probe[0].fa_completed(probe[1],self.record)")
 out['numeric_prefix_2k.py']=(P/'numeric_prefix_2k.py').read_bytes()
 for n,b in out.items():
  if n.endswith('.py'):compile(b,n,'exec')
 changed={n:dict(before=before.get(n),after=b)for n,b in out.items()if n not in before or before[n]!=b}
 result=dict(files=out,originals=before,delta=changed,runtime_admitted=False,NPU=False)
 inverse(result);return result
def inverse(bundle):
 restored=dict(bundle['files'])
 for n,d in bundle['delta'].items():
  need(restored[n]==d['after'],'whole numeric2k after operand')
  if d['before']is None:restored.pop(n)
  else:restored[n]=d['before']
 need(restored==bundle['originals'],'complete131 original numerical/observer source restored')
 return restored
def read_actual():
 root=P.parent/'formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole'
 files={n:(root/n).read_bytes()for n in('model_entry.py','service_bridge.py','service_runner.py','service_fia.py')}
 # Reuse the exact qualification tap source already audited; no candidate math rebuilt.
 path=P.parent/'fastpath_numeric_bridge_prepare_v1/qualification_tap_delta.py'
 raw=path.read_bytes();need(hashlib.sha256(raw).hexdigest()=='349bd1da965eca33df950f6817d88d9e9a3759771ce589f9b901c62302fe27da','exact existing observer tap renderer')
 ns={'__file__':str(path)};exec(compile(raw,str(path),'exec'),ns)
 strings=ns['render']({n:b.decode()for n,b in files.items()});files={n:s.encode()for n,s in strings.items()}
 for n in('fastpath_numeric_consumer.py','fastpath_numeric_observer.py'):
  files[n]=(P.parent/'fastpath_numeric_bridge_prepare_v1'/n).read_bytes()
 return files
if __name__=='__main__':
 import sys
 if sys.argv[1:]!=['--check']:
  need(not sys.argv[1:],'explicit source-only --check');print('{"enabled":false,"NPU":false}')
 else:
  b=adapt(read_actual());print(json.dumps(dict(changed=sorted(b['delta']),whole131_inverse=True,
    original_math_thresholds_unchanged=True,runtime_admitted=False,NPU=False)))
