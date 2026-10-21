"""Actual client-process opt-in before the unchanged source-bound native CLI."""
import argparse
import os
from pathlib import Path
import runpy
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import http_common as C

CLIENT_BYTES=7071
CLIENT_SHA='624b40c06bc7373f620e0ba655d74fe7077f0189ef15fb18d575b05e42f3d31f'


def dispatch(source_ref,url,output):
    m=C.source(source_ref,seconds=1800)
    own=C.ref(__file__);C.need(m['files']['client_entry.py']==own,'actual source-owned client-process shim')
    original=C.checked(m['files']['http_client.py']);actual=C.ref(original)
    C.need(original==P/'http_client.py'and(actual['bytes'],actual['sha256'])==(CLIENT_BYTES,CLIENT_SHA),
        'fixed exact original http_client complete source; no alternate executable/path')
    # The same Python process now executes the exact original CLI. Server env
    # is irrelevant: this assignment precedes runpy and the original execute.
    old_argv=list(sys.argv);before=os.environ.get('BOLE_TASK_HTTP_MAIN_ENABLE')
    sys.argv=[str(original),'--execute','--source-ref',C.canonical(source_ref).decode(),
        '--url',url,'--output',str(output)]
    os.environ['BOLE_TASK_HTTP_MAIN_ENABLE']='1'
    try:return runpy.run_path(str(original),run_name='__main__')
    finally:
        sys.argv[:]=old_argv
        if before is None:os.environ.pop('BOLE_TASK_HTTP_MAIN_ENABLE',None)
        else:os.environ['BOLE_TASK_HTTP_MAIN_ENABLE']=before


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--url');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"HTTP_executed":false}');return 0
    C.need(a.source_ref and a.url and a.output,'explicit actual source/loopback/output required')
    dispatch(C.parse(a.source_ref),a.url,a.output);return 0


if __name__=='__main__':raise SystemExit(main())
