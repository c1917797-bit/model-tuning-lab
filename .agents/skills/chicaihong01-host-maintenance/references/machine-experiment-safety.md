## Machine and experiment safety

- Re-prove physical NPU/process/container ownership in the same session as each
  action. HTTP health or container existence alone is insufficient.
- Resolve physical devices from Docker `HostConfig.Devices.PathOnHost`, then
  cross-check physical `npu-smi` process/memory state and the collaboration
  lock. Container-local `ASCEND_RT_VISIBLE_DEVICES=0,1,2,3` and logical NPU
  numbers do not prove that physical NPU0-3 are occupied; they can represent
  physical NPU4-7 after remapping.
- Report container device declarations together with container state. By
  default, running containers and live processes are active occupancy claims;
  exited containers are historical provenance that still requires owner and
  cleanup review but does not by itself prove current device use. If the user
  or experiment contract explicitly says any declaration blocks allocation,
  apply that stricter gate without reinterpretation.
- Treat NPU0-3, NPU4-7, ports, and running services as leased resources, not
  permanent assignments.
- For a long or repeated device experiment, check active jobs that can
  intermittently enter the target physical cards; one empty `npu-smi` snapshot
  does not establish an interference-free window. Keep a continuous
  physical-device process guard during the run. If an unexpected PID appears,
  invalidate that arm, capture its cgroup/container identity at detection time
  before a short-lived PID exits, preserve the PID/time and raw artifacts,
  release only owned resources, and re-establish isolation before any new-root
  retry. Container identity is not proof of the human launcher; a vanished PID
  without retained cgroup evidence does not prove its owner.

For a multi-minute or multi-hour controller, do not set the remote executor's
process timeout shorter than the campaign. Prefer asynchronous execution with
a campaign-length timeout and poll the stable operation ID. If the connector
or executor times out, treat that as control-plane ambiguity: inspect the same
operation, exact container labels, device processes, port, and immutable root
before retrying. A detached owned container can outlive its controller; never
blindly relaunch, and release only the exact resources proven to belong to the
failed attempt.
- Do not stop, restart, or replace a workload until its owning workstream and
  rollback instructions are identified.
- Inspect 1 GiB HugeTLB sysfs state and consumers before any memory-pool change.
  Free pages inside the pool are not ordinary free RAM or permission to release
  them.
- Keep datasets, weights, checkpoints, credentials, raw profiles, and large
  generated artifacts outside Git.

For performance work, also use `ascend-npu-environment-orientation`,
`ascend-inference-tuning-loop`, and `ascend-benchmark-evidence`.

For Qwen3.x BF16 runtime work on the pinned vLLM-Ascend v0.23 family, read
[qwen35-v023-runtime-lessons.md](qwen35-v023-runtime-lessons.md)
before allocating NPUs. It records which upstream and built-in routes were
measured, retired, rejected, or retained as partial components. Treat it as
candidate-screening knowledge, not as proof of current host state or final
performance attainment.
