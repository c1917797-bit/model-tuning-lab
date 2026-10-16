"""One opt filesystem reservation, not two independent bookings of same free bytes."""
GIB=2**30
CONTROL=3*GIB
RAW=216*GIB
RESERVE=int(8.5*GIB)
INITIAL=CONTROL+RAW+RESERVE

def check(free,control_used,raw_used,initial=False):
 if any(type(x)is not int or x<0 for x in(free,control_used,raw_used)):raise ValueError('actual nonnegative filesystem byte ledger')
 if control_used>CONTROL or raw_used>RAW:raise ValueError('original control3/raw216 payload caps')
 if free<RESERVE or(initial and free<INITIAL):raise ValueError('one opt fresh227.5GiB / shared8.5GiB reserve')
 return dict(free=free,control_used=control_used,raw_used=raw_used,shared_reserve=RESERVE,initial_floor=INITIAL,initial=initial,capacity_reserved_elsewhere=False)
