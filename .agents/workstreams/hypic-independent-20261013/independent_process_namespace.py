"""Parse Linux's explicit host-to-inner PID chain; never infer ordering."""
def namespace_pids(status,host_pid):
    lines=[x for x in status.splitlines() if x.startswith("NSpid:")]
    if len(lines)!=1:raise ValueError("explicit NSpid chain unavailable")
    try:values=tuple(int(x) for x in lines[0].split()[1:])
    except ValueError:raise ValueError("invalid namespace PID chain") from None
    if not values or any(x<=0 for x in values) or values[0]!=host_pid:
        raise ValueError("NSpid host identity mismatch")
    return values
