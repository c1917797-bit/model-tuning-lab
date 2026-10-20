"""Fixed G1 admission contract. No runtime import or device initialization."""
FLAG = 'BOLE_G1_MULTI_REQUEST_ENABLE'
SCOPE = dict(schema='bole.c1-two-request-service/v1', prefix=131,
             request_count=2, max_steps_per_request=1, max_output_tokens=2)
RAW_SCHEMA = 'bole.actual-c1-two-request-service/v1'
REQUEST_SCHEMA = 'bole.actual-c1-two-request-item/v1'
HTTP_SCHEMA = 'bole.actual-c1-two-request-service-HTTP/v1'
RESERVE_BYTES = 64 * 2**20
CAP_BYTES = 2**30


def epoch(value):
    if type(value) is not int or value not in (1, 2):
        raise ValueError('G1 actual request generation must be 1 or 2')
    return value
