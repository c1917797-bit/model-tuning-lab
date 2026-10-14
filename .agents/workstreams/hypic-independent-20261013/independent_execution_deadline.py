"""Explicit UTC execution deadline; absence preserves old immutable contracts."""
from datetime import datetime,timezone

def deadline_epoch(value):
    if value is None:return None
    if not isinstance(value,str) or not value.endswith("Z"):
        raise ValueError("explicit UTC deadline required")
    result=datetime.fromisoformat(value[:-1]+"+00:00")
    if result.tzinfo!=timezone.utc:raise ValueError("UTC deadline required")
    return result.timestamp()

def deadline_reached(deadline,now):
    return deadline is not None and now>=deadline
