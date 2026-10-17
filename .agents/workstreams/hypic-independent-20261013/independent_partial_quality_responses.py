"""Recover interrupted full-quality responses without promoting partial acceptance."""
import json,re
from pathlib import Path

def recover_quality_responses(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("regular immutable journal required")
    if path.stat().st_size>512*1024**2:
        raise ValueError("bounded journal required")
    records=[];identities=set();request_ids=set()
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            event=json.loads(line)
            if not isinstance(event,dict):
                raise ValueError("journal object required")
            if event.get("event")!="quality-scored-response":
                continue
            if event.get("scored") is not True:
                raise ValueError("explicit scored response required")
            index=event.get("index");repetition=event.get("repetition")
            if type(index)is not int or not 0<=index<127 or type(repetition)is not int or not 1<=repetition<=3:
                raise ValueError("frozen127x3 response identity required")
            identity=(index,repetition)
            if identity in identities:
                raise ValueError("duplicate scored identity")
            identities.add(identity)
            if type(event.get("ok"))is not bool or not isinstance(event.get("sample_id"),str) or not event["sample_id"]:
                raise ValueError("response outcome/sample identity required")
            if not isinstance(event.get("segment_sha256"),str) or not re.fullmatch(r"[0-9a-f]{64}",event["segment_sha256"]):
                raise ValueError("segment identity required")
            if event["ok"]:
                rid=event.get("request_id")
                if not isinstance(rid,str) or not rid or rid in request_ids:
                    raise ValueError("unique successful request identity required")
                request_ids.add(rid)
            records.append({k:v for k,v in event.items() if k not in ("event","scored")})
    return records
