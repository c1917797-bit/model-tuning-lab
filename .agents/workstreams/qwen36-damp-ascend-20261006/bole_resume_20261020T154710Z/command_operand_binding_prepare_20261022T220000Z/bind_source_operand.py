"""Pure source-Ref binding. No source edit, approval, owner or execution."""
import json
import re

def need(value, why):
    if not value:
        raise ValueError(why)

def parse_ref(raw):
    def pairs(items):
        out={}
        for key,value in items:
            need(key not in out,'duplicate source operand key')
            out[key]=value
        return out
    def bad(value):
        raise ValueError('nonfinite source operand')
    value=json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
    need(type(value)is dict and set(value)=={'path','bytes','sha256'} and
         type(value['path'])is str and value['path'].startswith('/') and
         type(value['bytes'])is int and value['bytes']>0 and
         type(value['sha256'])is str and
         re.fullmatch('[0-9a-f]{64}',value['sha256']),
         'complete typed source Ref operand')
    return value

def source_ref_from_commands(commands, reviewed_source_ref, manifest, template_ref, expected):
    """Return only the ordered source Ref already embedded in frozen commands.

    expected is the caller's actual checked source-owned command_contract.expected,
    never a newly reimplemented command generator. The caller remains responsible
    for opening/checking the complete commands/source/template/contract Refs.
    """
    need(type(commands)is dict and callable(expected),'actual command object and source-owned expected')
    operands=[]
    for key in ('model','CPU'):
        argv=commands[key]
        need(type(argv)is list and all(type(x)is str for x in argv) and
             argv.count('--source-ref')==1,'one original source operand in '+key)
        index=argv.index('--source-ref')
        need(index+1<len(argv),'source operand present')
        operands.append(argv[index+1])
    need(operands[0]==operands[1],'MODEL and CPU retain identical source operand bytes')
    result=parse_ref(operands[0])
    need(result==reviewed_source_ref and commands['bound_source']==reviewed_source_ref,
         'frozen operands join reviewed actual source Ref')
    bind=commands['bind']
    need(type(bind)is list and all(type(x)is str for x in bind) and
         bind.count('--reviewed-template-ref')==1,'one original binding template operand')
    index=bind.index('--reviewed-template-ref')
    need(index+1<len(bind),'template operand present')
    ordered_template=parse_ref(bind[index+1])
    need(ordered_template==template_ref and commands['source']==template_ref,
         'original binding template joins reviewed actual template Ref')
    target=expected(manifest['root'],manifest['output_root'],result,ordered_template,manifest['component_refs'])
    need(set(target)=={'model','CPU','bind'} and
         all(commands[key]==target[key]for key in target),
         'actual original model/CPU/bind literal command closure')
    need(json.dumps(result)==operands[0],
         'source operand serialization retained exactly; do not canonical-sort')
    return result

def main():
    print(json.dumps(dict(enabled=False,source_ref_returned=False,
                          approvals_written=False,NPU=False,commands_executed=False)))
    return 0
if __name__=='__main__':
    raise SystemExit(main())
