"""Fixed G1 admission contract. No runtime import or device initialization."""
from g2_contract import FLAG,SCOPE
RAW_SCHEMA = 'bole.actual-c1-two-request-stream-service/v2'
REQUEST_SCHEMA = 'bole.actual-c1-stream-request-open/v2'
HTTP_SCHEMA = 'bole.actual-c1-two-request-stream-HTTP/v2'
RESERVE_BYTES = 64 * 2**20
CAP_BYTES = 2**30


def epoch(value):
    if type(value) is not int or value not in (1, 2):
        raise ValueError('G1 actual request generation must be 1 or 2')
    return value
