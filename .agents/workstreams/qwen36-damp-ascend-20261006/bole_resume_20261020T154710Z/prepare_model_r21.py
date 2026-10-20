"""Create immutable r21: explicit FP16 private native-AR control, fixed reader."""
from pathlib import Path
import ast,hashlib,json,shutil,subprocess
BASE=Path('/opt/host/vnf/austinov')
TASK=BASE/'model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z'
OLD=BASE/'bole-model-fa64-fp16-20261020T154710Z-r20'
NEW=BASE/'bole-model-fa64-fp16-20261020T154710Z-r21'
def ref(p):
 p=Path(p);b=p.read_bytes()
 return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 assert not NEW.exists();shutil.copytree(OLD,NEW,ignore=shutil.ignore_patterns('__pycache__'))
 (NEW/'SOURCE_BOUND.json').rename(NEW/'PARENT_SOURCE_BOUND_R20.json')
 p=NEW/'contract090.py';s=p.read_text()
 assert s.count('run-bole-model-fa64-fp16-20261020T154710Z-r20')==2
 p.write_text(s.replace('run-bole-model-fa64-fp16-20261020T154710Z-r20','run-bole-model-fa64-fp16-20261020T154710Z-r21'))
 edits=json.loads((TASK/'MODEL_R21_EDITS.json').read_bytes())['edits']
 for edit in edits:
  p=NEW/edit['file'];s=p.read_text()
  assert s.count(edit['before'])==1,edit['file']+' nonunique delta '+edit['before'][:60]
  p.write_text(s.replace(edit['before'],edit['after']))
 for p in(TASK/'r21_additions').glob('*.py'):shutil.copyfile(p,NEW/p.name)
 freezer=(TASK/'freeze_model_r20.py').read_text().replace('-r20','-r21').replace('150','154')
 ar=next(e for e in edits if e['file']=='model_entry.py')
 marker='actual=(NEW/"model_entry.py").read_text()'
 assert freezer.count(marker)==1
 freezer=freezer.replace(marker,marker+'\nassert actual.count('+repr(ar['after'])+')==1\nactual=actual.replace('+repr(ar['after'])+','+repr(ar['before'])+')')
 needle='"test_observer_race_repair.py")'
 assert freezer.count(needle)==2
 freezer=freezer.replace(needle,'"test_observer_race_repair.py","ar_fp16_boundary.py","test_native_ar_boundary.py","ar_model_consumer.py")')
 extra="""evidence_root=Path('/opt/host/vnf/austinov/run-bole-native-ar-fia-20261020T154710Z-v1')
evidence=dict(numeric=ref(evidence_root/'data/RESULT.json'),owner=ref(evidence_root/'RESULT.json'),cleanup=ref(evidence_root/'CLEANUP.json'))
m['native_ar_boundary_repair']=dict(schema='bole.explicit-private-AR-precision-repair/v1',evidence=evidence,
 original_control=ref(Path('/opt/host/vnf/austinov/bole-model-fa64-fp16-20261020T154710Z-r20/model_entry.py')),
 implementation=ref(NEW/'ar_fp16_boundary.py'),independent_consumer=ref(NEW/'ar_model_consumer.py'),
 original_parameters_unchanged=True,inner_precise=0,original_bounds_unchanged=True,
 actual_production_vllm_dispatch_changed=False,whole_model_qualified=False)
m['dependencies'] += [*evidence.values(),ref(Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/native_ar_replay_v1/replay.py'))]
"""
 assert freezer.count('for f in NEW.rglob("*.py")')==1
 freezer=freezer.replace('for f in NEW.rglob("*.py")',extra+'for f in NEW.rglob("*.py")')
 f=TASK/'freeze_model_r21.py';f.write_text(freezer)
 q=subprocess.run(['/usr/bin/python3','-B',str(f)],capture_output=True,text=True);print('FREEZE',q.returncode,q.stdout,q.stderr);assert q.returncode==0
 cmd=json.loads((NEW/'COMMANDS.json').read_bytes())['bind']
 parent=json.loads((OLD/'SOURCE_BOUND.json').read_bytes())
 cmd[cmd.index('--component-refs-json')+1]=json.dumps(parent['component_refs'])
 q=subprocess.run(cmd,cwd=NEW,capture_output=True,text=True,timeout=25);print('BIND',q.returncode,q.stdout,q.stderr);assert q.returncode==0
 sr=ref(NEW/'SOURCE_BOUND.json');print('SOURCE_REF',json.dumps(sr))
 submit=(TASK/'submit_r17_owned_unit.py').read_text().replace('-r17','-r21')
 start=submit.index('SOURCE=');end=submit.index('\nOUT=',start)
 submit=submit[:start]+'SOURCE='+repr(sr)+submit[end:]
 (TASK/'submit_r21_owned_unit.py').write_text(submit)
 for p in NEW.rglob('*.py'):ast.parse(p.read_bytes(),filename=str(p))
 print('AST',len(list(NEW.rglob('*.py'))))
if __name__=='__main__':main()

