"""Default-OFF pure CPU lifecycle+decoder replay. No HTTP/model/HE execution."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import transport_decoder_bridge as B
def execute(source_ref,decoder_source_ref,binding_ref,output):
 q,m,b=B.packet(source_ref,decoder_source_ref,binding_ref)
 B.need(q['files']['transport_decoder_entry.py']==B.ref(__file__),'actual whole current public bridge entry')
 names=('decoder_replay_contract','_current_decoder_entry','transport_decoder_bridge','_transport_lifecycle_replay')
 with B.isolated(names):
  sys.modules['transport_decoder_bridge']=B
  R=B.load_module(m['files']['decoder_replay_contract.py'],'decoder_replay_contract')
  E=B.load_module(m['files']['replay_entry.py'],'_current_decoder_entry')
  R.validate_current(m,binding_ref,seconds=300)
  B.need(output.is_absolute()and output.parent.is_dir()and not output.exists()and
         not any(p.is_symlink()for p in output.parents),'exclusive new CPU replay output')
  output.mkdir(mode=0o700)
  try:
   with E.source_modules(m)as modules:
    with R.execution(m,decoder_source_ref,binding_ref):
     with B.transport_context(q,R,m,binding_ref,decoder_source_ref,modules,output)as c:
      L=B.load_module(q['files']['consume_lifecycle_replay.py'],'_transport_lifecycle_replay')
      g=c['generation'];owner=R.obj(g['owner_ref']);summary=owner['summary']
      result=L.run(q['HTTP_source_ref'],g['client_ref'],summary['journals_ref'],summary['process_binding_ref'],g['owner_ref'])
      B.need(result['HumanEval_model_code_executed']is False and result['formal_task_accuracy_accepted']is False,
             'unchanged pure component/lifecycle result, no formal task promotion')
      result.update(decoder_source_ref=decoder_source_ref,current_CPU_binding_ref=binding_ref,
        transport_decoder_source_ref=source_ref,historical_generation_authority_unchanged=True,
        current_CPU_execution_separate=True,HTTP_executed=False,NPU=False,formal_task_accuracy_accepted=False)
      R.validate_current(m,binding_ref)
      return E.write(output/'RESULT.json',result)
  except BaseException as e:
   E.write(output/'FIRST-FAULT.json',dict(error=repr(e),source_ref=source_ref,HTTP=False,NPU=False,formal_task_accuracy_accepted=False));raise
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for n in('source-ref','decoder-source-ref','binding-ref'):p.add_argument('--'+n)
 p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:
  B.need(not any((a.source_ref,a.decoder_source_ref,a.binding_ref,a.output)),'explicit mode')
  print('{"enabled":false,"HTTP":false,"NPU":false,"generated_code_executed":false}');return 0
 B.need(a.source_ref and a.decoder_source_ref and a.binding_ref and a.output,'all exact source/current binding/output operands')
 refs=[json.loads(x)for x in(a.source_ref,a.decoder_source_ref,a.binding_ref)]
 print(json.dumps(dict(result_ref=execute(*refs,a.output),HTTP=False,NPU=False)));return 0
if __name__=='__main__':raise SystemExit(main())
