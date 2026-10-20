"""Persist the first host failure before unchanged cleanup; no recovery/admission."""
import json,os,traceback
from pathlib import Path


def persist(root,source,error,phase):
    path=Path(root)/'HOST-FIRST-FAULT.json'
    value=dict(schema='bole.first-host-fault/v131r5',source=source,
        phase=dict(phase),error_type=type(error).__module__+'.'+type(error).__qualname__,
        error_repr=repr(error),errno=getattr(error,'errno',None),
        filename=None if getattr(error,'filename',None)is None else os.fsdecode(error.filename),
        filename2=None if getattr(error,'filename2',None)is None else os.fsdecode(error.filename2),
        traceback=''.join(traceback.format_exception(type(error),error,error.__traceback__)),
        fail_closed=True,recovery_attempted=False,cleanup_not_started=True)
    data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode('utf8')
    with path.open('xb')as f:
        if f.write(data)!=len(data):raise OSError('incomplete first-fault receipt')
        f.flush();os.fsync(f.fileno())
    fd=os.open(str(path.parent),os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return dict(path=str(path),bytes=len(data))
