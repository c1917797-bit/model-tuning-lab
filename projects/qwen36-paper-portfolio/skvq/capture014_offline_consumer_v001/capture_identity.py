"""Strict independent observation comparison; no device/framework imports.

The source-qualified RankProvider records time.time_ns on EACH observation.
Loader/raw are observed before Session identity. Time is ordered evidence, not
a stable process/group/source attribute. No original identity field is omitted.
"""
IDENTITY_KEYS=frozenset(("schema","observed_utc_ns","pid","pid_start_ticks",
 "proc_cmdline_sha256","parallel_source","torch_source","distributed_source",
 "native_group_class","public_TP_rank","groups","physical_card_lease_pending",
 "post_rope_origin_pending","actual_calibration_pending","native_ready","model_ready"))
def require(value,message):
    if not value:raise ValueError(message)
def exact(value,other):
    """No coercion: bool/int, float/int, unknown keys and list order differ."""
    if type(value)is not type(other):return False
    if type(value)is dict:
        return set(value)==set(other)and all(exact(value[k],other[k])for k in value)
    if type(value)is list:return len(value)==len(other)and all(exact(a,b)for a,b in zip(value,other))
    return value==other
def observation(value,rank,consume_identity):
    require(type(value)is dict and set(value)==IDENTITY_KEYS,"complete original actual observed identity field set")
    require(type(rank)is int and 0<=rank<4,"true original TP rank")
    require(type(value["observed_utc_ns"])is int and value["observed_utc_ns"]>0,
      "positive true-int original observation UTC nanoseconds")
    consume_identity(value,rank) # Exact source-qualified original TP/group oracle.
    return value
def pair(before,after,rank,consume_identity):
    observation(before,rank,consume_identity);observation(after,rank,consume_identity)
    require(before["observed_utc_ns"]<after["observed_utc_ns"],
      "original loader/raw observation strictly before Session/install")
    require(all(exact(before[k],after[k])for k in IDENTITY_KEYS if k!="observed_utc_ns"),
      "complete stable original process/TP/ProcessGroup/source identity")
    return {"schema":"skvq.ordered-same-worker-observations/v1","rank":rank,
      "before_observed_utc_ns":before["observed_utc_ns"],"after_observed_utc_ns":after["observed_utc_ns"],
      "elapsed_observation_ns":after["observed_utc_ns"]-before["observed_utc_ns"],
      "all_stable_fields_recursively_type_exact":True,"stable_keys":sorted(IDENTITY_KEYS-{"observed_utc_ns"}),
      "original_identity_oracle_called_on_both":True,"not_native_or_algorithm_pass":True}
