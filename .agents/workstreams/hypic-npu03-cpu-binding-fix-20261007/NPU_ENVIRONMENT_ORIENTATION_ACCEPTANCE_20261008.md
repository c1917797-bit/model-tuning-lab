# Ascend NPU environment orientation: bounded partial real-task evidence

Current main Skill identity: `ascend-npu-environment-orientation` blob
`f0c22149753c29765110eb1f0532c216220ef79c`, registry blob
`2611864bbcf719d57920aae03ff9eb85521526b4`, main commit
`ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2`.

Real task: establish and protect the physical NPU0–3 HYPIC quality lane
on chicaihong01/ma, distinguishing declared container mappings from
actual device execution. The cache10r5 frozen contract SHA256
`89490d2b45967cffe3296242e16292f61004a58005f50e6fab13e7893545fa48`
pins source commit `3ad0967589304cd8fc4e7cff02f48ecc6125c89f`,
container image digest `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`,
model index checksum, dataset/evaluator checksums, TP4 physical device IDs,
cpuset, context/output limits, concurrency and material-cache controls.
These are immutable/hash-backed identity fields rather than an image tag
or HTTP response alone. The external contract is at
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r5-full-hypic/contract.json`.

The earlier paired canary report `HOTPATH_CANARY_RESULT.md` records a
controlled-side HYPIC worker-hot event on four physical NPU0–3 workers
for one explicitly segmented 2048-max-output request, with a matched
no-cache control and clean guard. The cache10r5 start used a different
material-cache setting, so that canary is *related device-side proof*,
not a current cache10r5 inference/quality pass. During cache10r5 model
loading, `HOTPATH_CACHE10R5_STARTUP_GUARD_RESULT.md` records a real
foreign NPU2 PID whose live cgroup belonged to `cannbench_ds`, distinct
from the exact owned service. The service was removed before health and
0/127 samples; this is a sound environment/isolation rejection, not a
model result. Passive Docker mapping alone did not veto admission.

Long-term Skill decision: **partial-evidence**, not verified. The full
`ascend-npu-environment-orientation` workflow calls for a unified
`.agents/experiments/<id>.yaml` environment section, complete software
stack/driver/firmware/compiler/interconnect/power identity or explicit
unavailability markers, a same-identity successful inference canary,
material-drift comparison to the previous baseline, and a clean pushed
orientation checkpoint. This bounded task has several pinned fields,
a historical device canary and exact conflict/cleanup evidence, but not
those complete gates. Do not transfer the historical canary or an idle
snapshot into a cache10r5 quality claim. Revalidate if the main Skill
blob, source/image/model identity, device mapping or measured software
stack changes.
