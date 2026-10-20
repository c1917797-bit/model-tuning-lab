# R17 exact snapshot publication dependency closure

R16 failed and its source/output remain immutable. This successor adds the
previously missing dependencies/publication_common.py, byte-for-byte from the
actual repository donor:
/opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-deltalog/reproducibility/performance037-repair5/dependencies/publication_common.py
SHA256 996122e469ec64fc2c8bc1c0bfb077c1b675cb07c157206c697e02feb67a3dde.
MAIN read that exact file and mirrored its bytes locally. Its local bytes/SHA
were independently checked before copying, not recreated from a remembered API.

The existing snapshot_publication.publish body and native_receipt090 handler
remain byte-identical R16. Source.files, binder readset and original exact file
RO mounts now include the actual dependency at its required relative path.
No external import, module alias, fake snapshot or fallback publisher is added.

Entry software now discovers ALL test*.py and requires exactly103 cases: all98
inherited cases plus5 publication controls. The inherited full R16 inverse test
first reverses the two unique R17 identity changes, then executes the unchanged
R16-to-R15 full inverse; old before/after fingerprints are not rewritten.

Actual source-only controls exercise the unchanged publisher's real tempfile,
file fsync, exclusive hardlink, retained staging and strict standard JSON.
They cover duplicate destination, NaN/size rejection, injected OS link/file-fsync
failure and incomplete extent. The Linux-only cold subprocess control executes
actual file AND directory fsync and verifies hardlink inode, glob-visible final,
retained staging and exact Ref/JSON roundtrip. Windows must SKIP that positive
durability control, never emulate directory fsync and call it actual PASS.
MAIN must run the full103/noSkip in the immutable Linux image Devices[] stage
before any TP4 launch. The ordinary source/cold checks are not HAL/model proof.

DefaultOFF and actual component prerequisites, all mathematical bodies/oracles,
strict dtype/finite rules, raw/state/retirement gates and HBM3GiB remain unchanged.
Container32GiB, host.5, reserve8, common utilization0.8, C1/131, nodes3,
num_speculative_tokens8, HTTP10, whole3600/cleanup180 and renewed cutoff unchanged.
New outputs are unique and no-overwrite. No resources launched by this packet;
successful publication alone grants no mathematical, lifecycle or model PASS.
