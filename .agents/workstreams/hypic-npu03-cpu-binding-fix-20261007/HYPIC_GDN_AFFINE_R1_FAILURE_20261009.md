# HYPIC GDN affine r1 — device-initialization failure

The one-shot pinned-image NPU0 probe is terminal and invalid as an operator
result. `torch.npu.set_device(0)` raised ACL `507008` before the first GDN
operator call; the container log reports failed SoC discovery and
`rtGetDevMsg` feature unsupported. No GDN residual or HYPIC causal conclusion
exists from r1. The controller observed 12 clean physical NPU0-3 guard samples,
no owned NPU process, and exact owned-container release. The original raw root
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/gdn-affine-20261009-r1`
is immutable; source controller commit is `0b8ac14563edb468b7c1f4a2e4736672ad6e55ef`.

Raw SHA256: `terminal.json` a97e7620097ca690f3a22c92b6b63336d8f621eb927193768489077af7494adc;
`container.log` ebed2eac81df4ec93789a88b0cf137567ae18cdfe87090aaf2954781da28e073;
`container-inspect.json` be4295225b448d10ffbec089720fb4f07ba59eade28c747efa714e8ee2a07788;
`lane-guard.json` d6ea282f52fd0d77d959c31ad1ae6a22abfd4aba4e9fda1d9c130be36413b020.

The r1 container mapped only physical `/dev/davinci0` plus shared management
nodes. The previously successful HYPIC quality/profiler service mapped physical
`/dev/davinci0-3` in the same pinned image. This difference is a plausible
device-discovery cause, **not a proven root cause**. Successor r2 changes only
that functional mapping and uses a distinct immutable root. It must pass the
same real-PID/continuous-isolation/exact-release gates. Neither success nor
failure of this microdiagnostic changes the frozen r13 quality rejection.
