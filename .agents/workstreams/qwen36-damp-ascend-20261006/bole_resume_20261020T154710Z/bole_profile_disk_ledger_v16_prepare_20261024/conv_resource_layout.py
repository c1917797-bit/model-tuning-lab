"""Native full conv-slot derivation and same-current-frame resource check, no budget growth."""
import copy
NATIVE_SHAPE=dict(path='/vllm-workspace/vllm/vllm/model_executor/layers/mamba/mamba_utils.py',bytes=11750,sha256='aa9b7dc46725a012fc61b83a7181baaddad7ab4b0eb8e4144350799697ad6a42')
SLOT_SHAPE=(11,2560)
SLOT_BYTES=11*2560*2
def need(v,s):
 if not v:raise ValueError(s)
def once(body,a,b):
 need(body.count(a)==1,'one exact conv resource seam '+a[:60]);return body.replace(a,b,1)
def profile(P,m):
 old=P.validate(m['input_resource_profile32k']);spec=m['native_speculative_config']
 need(spec==dict(method='mtp',num_speculative_tokens=8),'same source MTP8 allocation; tree nodes are not native state length')
 keys=('input_tokens','output_tokens','native_pages','conv_slot_bytes','other_capture_bound','oracle_temporary_bound','serializer_temporary_bound')
 args={k:old[k]for k in keys};args['conv_slot_bytes']=SLOT_BYTES;new=P.plan(**args)
 allowed={'conv_slot_bytes','conv_before_after','logical_lower_bound','previous_after'}
 need({k for k in old if old[k]!=new[k]}<=allowed,'all outer RAM/disk/HBM/logical/wire reserves unchanged')
 return new
def preflight(C,m,sr,actual_spec):
 import torch
 from vllm.model_executor.layers.mamba import mamba_utils as U
 need(C.ref(U.__file__)==NATIVE_SHAPE,'same actual image native StateShapeCalculator bytes')
 config=C.obj(m['checkpoint_config_ref'])['text_config']
 names=('linear_num_key_heads','linear_num_value_heads','linear_key_head_dim','linear_value_head_dim','linear_conv_kernel_dim')
 values=tuple(config[k]for k in names)
 need(values==(16,48,128,128,4),'same actual checkpoint GDN head/channel/kernel shape')
 expected=m['native_speculative_config']
 need(expected==dict(method='mtp',num_speculative_tokens=8)and actual_spec in(None,expected),
      'actual parser spec agrees with source candidate allocation')
 shape,state=U.MambaStateShapeCalculator.gated_delta_net_state_shape(4,*values[:4],values[4],expected['num_speculative_tokens'])
 need(tuple(shape)==SLOT_SHAPE,'actual native SD full slot includes all8 speculative entries')
 tensor=torch.empty(shape,dtype=torch.bfloat16,device='meta')
 size=tensor.numel()*tensor.element_size()
 need(size==m['input_resource_profile32k']['conv_slot_bytes']==SLOT_BYTES,'native full conv shape exactly matches declared profile; old32KiB refused')
 return dict(schema='bole.actual-native-conv-resource-preflight/v1',source=sr,Devices=[],NPU=False,
  actual_native_calculator=True,calculator_ref=NATIVE_SHAPE,TP=4,shape=list(shape),dtype='bfloat16',
  full_slot_bytes=size,num_speculative_tokens=8,actual_parser_spec=actual_spec,
  measured_NPU_shape=False,measured_peak=False,numerical_qualified=False)
def receipt(value,m,sr):
 need(type(value)is dict and value.get('schema')=='bole.actual-native-conv-resource-preflight/v1'and
      value.get('source')==sr and value.get('Devices')==[]and value.get('NPU')is False and
      value.get('actual_native_calculator')is True and value.get('calculator_ref')==NATIVE_SHAPE and
      value.get('shape')==list(SLOT_SHAPE)and value.get('dtype')=='bfloat16'and
      type(value.get('full_slot_bytes'))is int and value['full_slot_bytes']==m['input_resource_profile32k']['conv_slot_bytes']==SLOT_BYTES,
      'actual sameimage native full-slot preflight receipt, not an inherited parser PASS')
 return value
def adapt(files):
 out=dict(files)
 text=out['resource32k_runtime.py'].decode()
 text=once(text,"    runtime=c['runtime'];runtime.identity(32768)","""    runtime=c['runtime']
    owner=runtime.bridge._bole_live.current()
    C.need(runtime.active is None or runtime.active==owner,'same active or just-ACKed still-open frame Owner')
    runtime.identity(owner.length)""")
 text=once(text,'slot=runtime.bridge._physical_slot(b,runtime.initial)','slot=runtime.bridge._physical_slot(b,owner)')
 text=once(text,"            C.need(x.numel()*x.element_size()<=profile['conv_slot_bytes']", """            C.need(tuple(x.shape)==(1,11,2560)and x.dtype==c['t'].bfloat16,
                   'actual source-derived full SD conv slot geometry including speculative bytes')
            C.need(x.numel()*x.element_size()<=profile['conv_slot_bytes']""")
 out['resource32k_runtime.py']=text.encode()
 text=out['preflight114.py'].decode()
 text=once(text," return dict(input_preflight=actual_input,",""" import conv_resource_layout as CR
 C.need(C.ref(CR.__file__)==m['files']['conv_resource_layout.py'],'source-owned native resource preflight')
 conv_geometry=CR.preflight(C,m,sr,expected)
 return dict(native_conv_geometry=conv_geometry,input_preflight=actual_input,""")
 out['preflight114.py']=text.encode()
 text=out['host_service.py'].decode()
 marker="summary['CPU_report']=owned_ref.file_ref(C,c,cpu.out/'CPU.json');summary['CPU_release']=close(cpu)"
 replacement="""summary['CPU_report']=owned_ref.file_ref(C,c,cpu.out/'CPU.json')
  import conv_resource_layout as CR
  C.need(C.ref(CR.__file__)==m['files']['conv_resource_layout.py'],'source-owned CPU geometry receipt consumer')
  CR.receipt(report['native_conv_geometry'],m,sr)
  summary['CPU_release']=close(cpu)"""
 text=once(text,marker,replacement);out['host_service.py']=text.encode()
 delta={n:dict(before=files[n],after=out[n])for n in out if files[n]!=out[n]}
 need(set(delta)=={'resource32k_runtime.py','preflight114.py','host_service.py'},'exact resource/preflight/controller-only delta')
 return out,delta
def inverse(files,delta):
 out=dict(files)
 for n,r in delta.items():
  need(out[n]==r['after'],'exact conv resource inverse');out[n]=r['before']
 return out
