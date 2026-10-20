"""Fixed G1 admission contract. No runtime import or device initialization."""
from g2_contract import FLAG,SCOPE
RAW_SCHEMA = 'bole.actual-c1-single-request-fixed1024-stream-service/v3'
REQUEST_SCHEMA = 'bole.actual-c1-fixed1024-stream-request-open/v3'
HTTP_SCHEMA = 'bole.actual-c1-single-request-fixed1024-stream-HTTP/v3'
RESERVE_BYTES = 64 * 2**20
CAP_BYTES = 2**30


def epoch(value):
    if type(value) is not int or value != 1:
        raise ValueError('sole actual G3 request generation must be 1')
    return value
