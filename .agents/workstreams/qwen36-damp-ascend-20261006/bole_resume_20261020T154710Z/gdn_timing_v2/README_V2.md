# Timing source-resolution repair v2

V1 actually compiled a candidate but failed before any timing sample because
inspect.getsourcefile(class) cannot resolve Triton's dynamically loaded ascend
module when absent from sys.modules. V1 output and sources remain immutable.
V2 checks the exact same installed compiler source Ref via four methods defined
on that actual AscendBackend class. It retains their class/name/module checks.
No numerical code, measured paths, thresholds, samples, order or resource limits
change. The owner pins the new timing source hash. Parent manifests/checks are
historical only. Actual new sameimage and NPU qualification are pending.
