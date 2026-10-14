"""Frozen bounded receipt budgets; never unbounded logging or silent truncation."""
def evidence_limits(spec=None):
    spec={} if spec is None else dict(spec)
    defaults={"max_events":10000,"max_bytes":33554432,"max_requests":128}
    if set(spec)-set(defaults):raise ValueError("unknown evidence limit")
    values=dict(defaults,**spec)
    bounds={"max_events":100000,"max_bytes":134217728,"max_requests":4096}
    for name,value in values.items():
        if type(value) is not int or not 1<=value<=bounds[name]:
            raise ValueError("bounded integer evidence limits required")
    return values
