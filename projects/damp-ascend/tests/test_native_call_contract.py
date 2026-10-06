#!/usr/bin/env python3
"""No torch/container/device required; catches the retained v1 call-ABI defect."""
import argparse
import hashlib
import json
from pathlib import Path
from native_call_contract import cpu_signature_checks, validate_native_schema


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--schema-report', type=Path,
                        help='optional retained native_schema JSON; CPU torch parser, no library/device')
    args = parser.parse_args()
    result = cpu_signature_checks(Path(__file__).resolve().parent)
    if args.schema_report is not None:
        import torch
        text = json.loads(args.schema_report.read_text())['native_schema']
        result['retained_torch_schema_parser'] = validate_native_schema(torch._C.parse_schema(text))
        result['retained_schema_report_sha256'] = hashlib.sha256(args.schema_report.read_bytes()).hexdigest()
        result['retained_schema_scope'] = 'CPU parser of retained schema, not actual loaded-library verification'
    print(json.dumps({'status': 'signature_guard_pass', **result}, sort_keys=True))
