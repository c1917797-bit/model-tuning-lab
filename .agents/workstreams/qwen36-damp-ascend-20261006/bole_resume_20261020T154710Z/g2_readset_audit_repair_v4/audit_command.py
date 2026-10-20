"""Print actual authorized read-only argv; execute nothing."""
import argparse
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--audit-path',required=True,type=Path);a=p.parse_args()
    if not a.audit_path.is_absolute():raise ValueError('absolute actual host audit path')
    source=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v3/SOURCE_BOUND.json',
      bytes=220181,sha256='91002bf0dbda04826db5a1c4d3264b36da0bfaf4f4464feb50ce8ee05435c874')
    print(json.dumps(['/usr/bin/python3','-I','-B',str(a.audit_path),'--execute','--source-ref',json.dumps(source)]))


if __name__=='__main__':main()
