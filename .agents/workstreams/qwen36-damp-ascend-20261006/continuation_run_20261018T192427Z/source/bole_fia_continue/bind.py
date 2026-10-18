"""Bind one new fixed-frame source after exact complete read-only closure checks."""
import argparse
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import common as C


def main():
    parser=argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--template-ref')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if not args.execute:
        print('{"enabled":false,"NPU":false,"resource_admitted":false}');return 0
    template_ref=json.loads(args.template_ref)
    C.need(template_ref['path']==str(HERE/'SOURCE_TEMPLATE.json'),'exact new preregistered template')
    template=C.obj(template_ref)
    C.validate(template,prepared=True);C.window(template)
    C.need(template['files']['bind.py']==C.ref(__file__),'actual binder identity')
    C.need('prepared_template'not in template,'unbound template cannot carry a claimed prior bind')
    C.need(args.output==HERE/'SOURCE_MANIFEST.json'and not args.output.exists(),
           'new source only; no replacement of any frozen source')
    for filename,reference in template['files'].items():
        if filename.endswith('.py'):
            compile(C.checked(reference).read_bytes(),reference['path'],'exec')
    bound=dict(template,prepared_only=False,prepared_template=template_ref)
    before=C.readset(bound)
    source_ref=C.write(args.output,bound)
    C.source(source_ref)
    for reference in before:C.checked(reference)
    print(json.dumps(dict(source=source_ref,prepared_only=False,default_enabled=False,
          full_readset_count=len(before)+1,NPU=False,resource_admitted=False,
          actual_same_source_CPU_preflight_required=True,
          current_authority_cutoff=C.CUT,whole_model_phase_unchanged=True)))
    return 0


if __name__=='__main__':raise SystemExit(main())
