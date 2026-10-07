# H8 full-v5 actual no-device admission failure

MAIN operation exec-000000000000104b exited1 after42.334s; this is a source/resource-observation failure, NOT an algorithm or NPU numerical result. Whole original terminal is preserved in H8_FULL_V5_SOURCE_ORIGINAL_TERMINAL_20261007.json.

Frozen v5 source manifest:86094070a68f37c8fe3453f8a7a87c5869db387605ad04911cf4020281a3b12c. Actual SOURCE_ADMISSION_RESULT.json:ad88592f527d9fb2238ebab1d98c790d7683400bde92ef21d079677efb216e21. Original source-exec:c0f08afbe8ba4d5054915a3e2ab8ea5fb5f085b5f19f4a8f9f067c805be1f3d7. Exact cleanup:57160b9d3818485f09d11d86e3cdd2b5187d2b2a529459f0a5d3f0a47492589f.

The actual child reached source_inputs, artifact validation, original warm consumer,238-source readonly closure, pinned image source and native library byte checks, then failed in namespace_admission.inside cpu_view: hidden cgroup ancestors are not admission proof. No Torch/NPU was imported or initialized by this stage. No full11520/model/E2E/task authority exists.

Do NOT call the cause a private cgroup namespace. Independent read-only exec-0000000000001053 proves actual HostConfig.CgroupnsMode=host already, with cgroupv1/kernel5.10. The default container filesystem exposes controller leaf roots; the host mounts expose full root=/ ancestors. A host namespace flag alone does not repair that filesystem view.

CID4df8090b9612c5b04d8aefbe2ef748613875e426ca8157fedbf86603002c1515 was stopped and retained by the original controller. Independent1053 proves Running=false/Pid0/noExecIDs/noOOM/Devices[]/nonprivileged/cap-drop ALL. No second stop and no foreign/physical0–3 mutation occurred. Controller sampled peak93596KiB within512MiB; source cleanup has no secondary error.

Next is an independent source successor: only exact CPU,cpuset,memory controller root readonly binds and actual mountroot=/+ro validation, while preserving all ancestor resource gates and all numerical source/11520/threshold/SO/lease/cutoff bytes. Do not use an entire recursive cgroup bind (kernel5.10 can retain writable submounts), expose cgroup writes/PID/network, remove the ancestor gate, or rerun immutable v5.

Separately, SparQ004 canonical three-file safety repair was source-verified and actual MAIN84 stdlib tests/source27 passed in1047. This is software-only; actual Devices[] ABI and NPU/model/E2E/task remain pending. W4native001 was NOT admitted: MAIN caught literal backslash-zero command-hash separator, CID persistence ordering, and release-SMI RSS recovery issues; isolated002 is preparing. No newly accepted non-HYPIC technique exists.
