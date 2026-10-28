"""Use the reviewed actual constructor with R44 owner; intercept Docker allocation."""
from unittest.mock import patch
from host_audits import r43_launch_capsule as retained
from host_audits import r44_profile_controller as owner
from host_audits import r44_profile_policy as policy
def capture_contract(c):
 with patch.object(retained,"owner",owner):report=retained.capture_contract(c)
 argv=report["argv"]
 import json,re
 if argv.count("--profiler-config")!=1 or json.loads(argv[argv.index("--profiler-config")+1])!=policy.PROFILE:raise ValueError("actual launch not exact count2 profiler")
 compute={int(m[1])for arg in argv for m in [re.search(r"(?:^|=)/dev/davinci([0-9]+)(?::|$)",arg)]if m}
 if compute!={0,1,2,3}or"--privileged"in argv:raise ValueError("constructor physical0-3/nonprivileged mapping required")
 report.update(schema="hypic-r44-actual-launch-capsule/v1",r44_host_source_sha256=c["r44_host_source_sha256"],scope="Actual retained base/R43 owner with R44 count2 and receipt; no Docker allocation; scratch-only raw path and mocked physical/port admission. Fresh real admission still required.")
 return report
