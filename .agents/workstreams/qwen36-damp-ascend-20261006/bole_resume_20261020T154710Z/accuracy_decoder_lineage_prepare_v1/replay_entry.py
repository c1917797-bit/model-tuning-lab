"""Default-OFF CPU token replay only. No HTTP, model, accelerator or generated-code execution."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import decoder_replay_contract as R

def write(path,value):
    raw=R.canonical(value)+b'\n'
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return R.ref(path)

@contextmanager
def source_modules(m):
    # Reuse original source-owned objects, restoring all public names exactly.
    names=('cohort_contract','lineage_http_common','generation_provenance','task_contract','postprocess','decoder','score_tokens')
    sentinel=object();old={n:sys.modules.get(n,sentinel)for n in names};old_path=list(sys.path)
    texts={n:R.checked(m['files'][n+'.py']).read_bytes()for n in names}
    loaded={}
    try:
        sys.path.insert(0,m['root'])
        for name in names:
            path=m['files'][name+'.py']['path'];spec=importlib.util.spec_from_file_location(name,path)
            mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod
            exec(compile(texts[name],path,'exec'),mod.__dict__);loaded[name]=mod
        yield loaded
    finally:
        sys.path[:]=old_path
        for name,value in old.items():
            if value is sentinel:sys.modules.pop(name,None)
            else:sys.modules[name]=value

def execute(source_ref,binding_ref,output):
    m=R.obj(source_ref)
    R.need(m['decoder_replay_source_schema']=='bole.current-CPU-decode-replay-source/v1'and
           m['root']==str(HERE)and m['default_enabled']is False and
           m['files']['replay_entry.py']==R.ref(__file__)and
           m['files']['decoder_replay_contract.py']==R.ref(R.__file__),'actual complete source-owned CPU replay entry')
    R.validate_current(m,binding_ref,seconds=300)
    R.need(output.is_absolute()and output.parent.is_dir()and not output.exists()and
           not any(p.is_symlink()for p in output.parents),'fresh own replay output leaf')
    output.mkdir(mode=0o700)
    try:
        with source_modules(m)as modules:
            R.need(modules['score_tokens'].C is modules['task_contract']and
                   modules['score_tokens'].D is modules['decoder']and
                   modules['score_tokens'].S is modules['postprocess'],'same actual source-owned scorer/decoder helper namespace')
            with R.execution(m,source_ref,binding_ref)as context:
                derived=R.envelope(context['raw'],source_ref)
                R.need(R.inverse_envelope(derived,context['binding']['historical_task_source_ref'])==context['raw'],
                       'complete reversible raw envelope; original generation bytes not overwritten')
                raw_ref=write(output/'REPLAY_ENVELOPE.json',derived)
                grades=modules['score_tokens'].replay(source_ref,raw_ref,full_provenance=False)
                R.need(grades['human_eval_code_executed']is False,'pure decoding/component grades never execute generated HE code')
                R.validate_current(m,binding_ref)
                result=dict(schema='bole.actual-current-CPU-token-replay/v1',source_ref=source_ref,
                    binding_ref=binding_ref,historical_task_source_ref=context['binding']['historical_task_source_ref'],
                    original_generation_raw_ref=context['binding']['raw_ref'],derived_replay_raw_ref=raw_ref,
                    original_generation_authority_unchanged=True,current_CPU_execution_separate=True,
                    component_grades=grades,HumanEval_model_code_executed=False,HTTP=False,NPU=False,
                    independent_native_lifecycle_proven=False,BOLE_activation_accepted=False,
                    formal_task_accuracy_accepted=False,performance_ready=False)
        return write(output/'RESULT.json',result)
    except BaseException as error:
        write(output/'FIRST-FAULT.json',dict(error=repr(error),source_ref=source_ref,binding_ref=binding_ref,
            HTTP=False,NPU=False,formal_task_accuracy_accepted=False))
        raise

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--source',type=Path);p.add_argument('--binding-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:
        R.need(not any((a.source,a.binding_ref,a.output)),'explicit mode required')
        print('{"enabled":false,"HTTP":false,"NPU":false,"generated_code_executed":false}');return
    R.need(a.source and a.binding_ref and a.output,'actual current source/binding/fresh output required')
    print(json.dumps(dict(result_ref=execute(R.ref(a.source),json.loads(a.binding_ref),a.output),HTTP=False,NPU=False)))
if __name__=='__main__':main()
