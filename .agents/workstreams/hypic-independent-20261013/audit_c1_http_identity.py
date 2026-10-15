"""Strict post-run transport/runtime identity join, never a coverage substitute."""
def resolve_http_ids(api_ids, runtime_ids, *, expected_count):
    if type(expected_count) is not int or expected_count < 1:
        raise ValueError("positive frozen denominator required")
    def checked(values, label):
        if not isinstance(values, (list, tuple)):
            raise ValueError(label + " must be a sequence")
        if any(type(v) is not str or not v.strip() or v != v.strip() for v in values):
            raise ValueError(label + " must contain nonblank exact strings")
        if len(set(values)) != len(values):
            raise ValueError(label + " duplicates")
        return list(values)
    apis = checked(api_ids, "HTTP IDs")
    runtimes = checked(runtime_ids, "runtime IDs")
    if len(apis) != expected_count:
        raise ValueError("frozen HTTP denominator changed")
    mapping = {}
    for api in apis:
        matches = [rid for rid in runtimes if rid.startswith(api + "-") and len(rid) > len(api) + 1]
        if len(matches) != 1:
            raise ValueError("missing or ambiguous runtime identity")
        mapping[api] = matches[0]
    if len(set(mapping.values())) != expected_count:
        raise ValueError("runtime identity collision")
    return mapping
