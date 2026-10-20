"""Post-binding command closure, avoiding a SOURCE_TEMPLATE hash cycle."""
import json
from pathlib import Path
import sourceio as C


def expected(root,output,sr,template,components):
    root=Path(root)
    def host(cpu):
        return ['/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1',
            '/usr/bin/python3','-I','-B',str(root/'host_service.py'),'--execute',
            *(['--cpu-only']if cpu else[]),'--source-ref',json.dumps(sr),
            '--output',output+('-CPU'if cpu else'')]
    return dict(model=host(False),CPU=host(True),bind=[
        '/usr/bin/python3','-I','-B',str(root/'bind_model.py'),'--execute',
        '--reviewed-template-ref',json.dumps(template),
        '--component-refs-json',json.dumps(components)])


def validate_value(value,m,sr,template,historical):
    C.need(value['schema']=='bole.G1-actual-bound-commands/v2' and
           value['source']==template and value['bound_source']==sr and
           value['required_sameimage_software_cases']==m['service_required_sameimage_software_cases'] and
           value['historical_required_sameimage_software_cases']==historical['required_sameimage_software_cases']==154,
           'actual current command/source/test scope and separate exact historical154 lineage')
    C.need(value['G2_stream_protocol']is True and value['actual_G2_execution_claimed']is False,
           'explicit new untimed stream command scope, no execution inferred from source')
    target=expected(m['root'],m['output_root'],sr,template,m['component_refs'])
    C.need(all(value[key]==argv for key,argv in target.items()),
           'exact current runnable model/CPU/bind commands, source Refs and new output leaves')
    C.need(value['actual_G1_execution_claimed'] is False and
           value['legacy_entrypoints_retained_for_inverse_tests_only'] is True,
           'commands are source operands, not a fabricated same-image result')
    return True


def validate(C_,sr,m):
    C_.need(C_.ref(__file__)==m['files']['command_contract.py'] and
            Path(m['root'])==Path(__file__).resolve().parent,
            'exact source-owned command closure helper')
    scope=m['command_scope']
    C_.need(scope['schema']=='bole.post-binding-command-readset/v2' and
            scope['file']=='COMMANDS.json' and scope['generated_after_binding'] is True and
            scope['included_in_actual_host_readset'] is True and
            'COMMANDS.json'not in m['files'], 'explicit acyclic command scope')
    template=C_.ref(Path(m['root'])/'SOURCE_TEMPLATE.json')
    reference=C_.ref(Path(m['root'])/'COMMANDS.json')
    value=C_.obj(reference);historical=C_.obj(scope['historical_ref'])
    validate_value(value,m,sr,template,historical)
    mirror=C_.ref(Path(m['root'])/scope['compatibility_file']);compat=C_.obj(mirror)
    C_.need(compat['source']==sr and compat['template']==template and
            compat['commands']==reference and compat['model']==value['model'] and
            compat['CPU']==value['CPU'] and
            compat['required_sameimage_software_cases']==m['service_required_sameimage_software_cases'],
            'actual G1 compatibility commands point at current canonical commands/source/output')
    return [reference,mirror,scope['historical_ref']]
