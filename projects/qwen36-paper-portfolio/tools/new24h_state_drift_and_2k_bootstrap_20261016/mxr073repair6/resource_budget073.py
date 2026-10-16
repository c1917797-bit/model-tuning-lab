"""Source-bound smaller hard cgroup trial, never a proven new2K peak."""
MODEL_GUEST_GIB=32
CPU_GUEST_GIB=8
HOST_GIB=.5
RESERVE_GIB=8
MODEL_INITIAL_GIB=MODEL_GUEST_GIB+HOST_GIB+RESERVE_GIB
HISTORICAL_PEAK_BYTES=16895430656
NEW_COMPLETE_OUTPUT_CAP_BYTES=12*2**30
def contract():
 return dict(model_guest_GiB=MODEL_GUEST_GIB,CPU_guest_GiB=CPU_GUEST_GIB,host_GiB=HOST_GIB,reserve_GiB=RESERVE_GIB,model_initial_GiB=MODEL_INITIAL_GIB,historical_peak_bytes=HISTORICAL_PEAK_BYTES,new_complete_output_cap_bytes=NEW_COMPLETE_OUTPUT_CAP_BYTES,incremental_trial_headroom_bytes=MODEL_GUEST_GIB*2**30-HISTORICAL_PEAK_BYTES-NEW_COMPLETE_OUTPUT_CAP_BYTES,new2K_peak_proved=False,OOM_is_hard_failure=True,protected_0_3_unchanged=True)
