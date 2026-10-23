"""Narrow command-Ref serialization repair; no owner, authority or device work."""
import copy,json,sys
from pathlib import Path
PARENT=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole2k_runtime_complete_prepare_v3/prepared-source-short8-qualifier")
HELPER="""def canonical_ref_arguments(argv):
    out=list(argv)
    def unique(pairs):
        value={}
        for key,item in pairs:
            C.need(key not in value,'duplicate command Ref key')
            value[key]=item
        return value
    for index,operand in enumerate(argv[:-1]):
        if operand in ('--source-ref','--template-ref'):
            value=json.loads(argv[index+1],object_pairs_hook=unique)
            C.need(type(value)is dict and set(value)=={'path','bytes','sha256'} and
                   type(value['path'])is str and type(value['bytes'])is int and
                   value['bytes']>0 and type(value['sha256'])is str,
                   'complete typed command Ref operand')
            out[index+1]=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    return out

"""
OLD="all(value[key]==argv for key,argv in target.items())"
NEW="all(canonical_ref_arguments(value[key])==canonical_ref_arguments(argv) for key,argv in target.items())"
def need(v,s):
 if not v:raise ValueError(s)
def adapt(raw):
 s=raw.decode();need(s.count(OLD)==1 and s.count('def validate_value(')==1,'exact command comparer seam')
 out=s.replace('def validate_value(',HELPER+'def validate_value(',1).replace(OLD,NEW,1).encode()
 compile(out,'command_contract.py','exec');return out
def inverse(raw):
 s=raw.decode();need(s.count(HELPER)==1 and s.count(NEW)==1,'exact inverse command seam')
 return s.replace(HELPER,'',1).replace(NEW,OLD,1).encode()
def check():
 raw=(PARENT/'command_contract.py').read_bytes();derived=adapt(raw);need(inverse(derived)==raw,'entire original command bytes restored')
 before=list(sys.path);sys.path.insert(0,str(PARENT))
 try:
  old=dict(__file__=str(PARENT/'command_contract.py'),__name__='_original_command')
  new=dict(__file__=str(PARENT/'command_contract.py'),__name__='_derived_command')
  exec(compile(raw,old['__file__'],'exec'),old);exec(compile(derived,new['__file__'],'exec'),new)
  C=new['C'];sr=C.ref(PARENT/'SOURCE_BOUND.json');m=C.obj(sr);tr=C.ref(PARENT/'SOURCE_TEMPLATE.json')
  value=C.obj(C.ref(PARENT/'COMMANDS.json'));hist=C.obj(m['command_scope']['historical_ref'])
  need(old['validate_value'](value,m,sr,tr,hist)is True,'actual original canonical command')
  events=['actual_original_command_pass','full_source_inverse']
  reordered=dict(reversed(list(sr.items())))
  try:old['validate_value'](value,m,reordered,tr,hist)
  except ValueError:pass
  else:raise AssertionError('original serialization defect not reproduced')
  need(new['validate_value'](value,m,reordered,tr,hist)is True,'same actual source Ref independent of serialization order')
  events.append('actual_old_failure_and_derived_equivalent_ref_pass')
  tests=[]
  bad=copy.deepcopy(value);bad['model'].remove('BOLE_MODEL131_MAIN_ENABLE=1');tests.append(('missing_optin',bad))
  bad=copy.deepcopy(value);bad['model'][-1]+='-wrong';tests.append(('wrong_output',bad))
  bad=copy.deepcopy(value);i=bad['model'].index('--source-ref')+1
  bad['model'][i]=json.dumps(dict(sr,sha256='0'*64));tests.append(('wrong_source_hash',bad))
  bad=copy.deepcopy(value);i=bad['model'].index('--source-ref')+1
  bad['model'][i]=bad['model'][i][:-1]+', "bytes": '+str(sr['bytes'])+'}';tests.append(('duplicate_ref_key',bad))
  for label,bad in tests:
   try:new['validate_value'](bad,m,sr,tr,hist)
   except ValueError:events.append(label+'_rejected')
   else:raise AssertionError('accepted '+label)
  need('torch'not in sys.modules and 'torch_npu'not in sys.modules,'source-only check')
  print(json.dumps(dict(events=events,source_bound=False,NPU=False,qualification=False,math_unchanged=True)))
 finally:sys.path[:]=before
if __name__=='__main__':
 if sys.argv[1:]==['--check']:check()
 else:
  need(not sys.argv[1:],'only explicit source check')
  print('{"enabled":false,"NPU":false}')
