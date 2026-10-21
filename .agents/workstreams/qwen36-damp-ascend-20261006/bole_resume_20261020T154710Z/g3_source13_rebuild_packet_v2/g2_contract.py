"""Explicit new streaming diagnostic protocol; default OFF, fixed profiles."""
PROFILE_NAME = 'fixed1024'
PROFILES = {'fixed1024': 1024}
FLAG = 'BOLE_G3_STREAM_ENABLE'
RAW_CAP = 2**30
METADATA_CAP = 64*2**20
# Bound two serialized/loaded copies plus the retained cross-step checkpoint.
FRAME_LOGICAL_CAP = 384*2**20
CHECKPOINT_CAP = 128*2**20
FRAME_WIRE_CAP = 448*2**20
REPORT_CAP = 4000
RELEASE_CAP = 1536
EVENT_METADATA_CAP = 2048 + 3072 + RELEASE_CAP + REPORT_CAP
CALIBRATION_ALLOCATION = 16*2**20
OTHER_EVIDENCE_ALLOCATION = 3*2**20
FINAL_EVIDENCE_ALLOCATION = 16*2**20
POLL_SECONDS = .05
ACK_TIMEOUT_SECONDS = 300
BOOT_TIMEOUT_SECONDS = 900


def scope(name=PROFILE_NAME):
    if name not in PROFILES:
        raise ValueError('one explicitly frozen G3 profile')
    output = PROFILES[name]
    return dict(schema='bole.c1-single-request-fixed1024-stream-service/v3', profile=name,
        prefix=131, request_count=1, max_steps_per_request=output-1,
        max_output_tokens=output, capture_protocol='every-frame-independent-CPU-ACK/v1')


SCOPE = scope()
MAX_OUTPUT = SCOPE['max_output_tokens']


def capacity(length, allocated_kernel_pages, *, budget=MAX_OUTPUT):
    if type(length)is not int or not 131<=length<=131+budget-2:
        raise ValueError('exact current native length for fixed output budget')
    # Three private branch rows are required even if only root is admitted.
    if length+3>128*allocated_kernel_pages:
        raise ValueError('initial actual allocation cannot hold padded tree')
    return dict(committed_length=length, private_end_exclusive=length+3,
        initial_kernel_capacity=128*allocated_kernel_pages,
        active_kernel_pages=(length+2+127)//128,
        physical_allocation_growth_proven=False)
