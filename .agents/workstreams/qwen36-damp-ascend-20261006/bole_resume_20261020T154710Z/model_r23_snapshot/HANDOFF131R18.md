# R18: source-qualified frontend executable namespace repair

R17 remains a failed original experiment. Its real first fault followed valid
snapshots/HTTP/raw capture: host identity_owner used Path('/proc/PID/exe').resolve
and tried to resolve the executable's container-absolute target on the host.
This new source/output repairs that identity seam only. Original103 controls,
publication donor, mathematics, input131/tree3/spec8/HTTP10, commonutil0.8,
memory32+host.5+reserve8, HBM3GiB, whole3600/cleanup180 are retained.

`identity_owner.frontend` retains exact Docker source-validated live inspection,
Docker top, PID/NSpid/start/cgroup and stable full raw argv checks. It adds a
second inspection and inspected-init lifetime check. It no longer resolves the
magic link as a host path, and does not accept a basename.

`frontend_namespace131r18.verify` uses original025's source-bound exact interpreter
`/usr/local/python3.12.13/bin/python3`. It opens only the designated kernel
`/proc/PID/root` and `/proc/PID/exe` magic links. Ordinary path components are
walked with openat and O_NOFOLLOW from a pinned root FD. Relative and absolute
symlinks are resolved *inside that root*, with40-link cap, no parent components
(including foo/../bar, which cannot be safely canceled before resolving foo),
stable symlink/component stat and explicit deletion rejection. It opens both
the actual kernel executable and expected interpreter/current exe target inside
that root, verifies regular executable files, matching dev/inode/complete stream
hash/size/mode/mtime/ctime/nlink, then rewalks/rechecks after streaming.

Frontend and the freshly inspected container init must share PID and mount
namespace identifiers and the same root identity. Those observations and the
exe link must remain stable. Host argv, NSpid, start/cgroup and init/container
lifetime are checked again. No '(deleted)' executable or identity race passes.
Binary hashing is bounded64MiB and hashes are observed evidence tied to exact
immutable-image+interpreter identity; there is no invented pre-registered binary
SHA or relaxed generic Ref3 reader.

New tests execute the complete actual frontend function using an explicitly
software proc/controller fixture (not actual Docker proof), with exact R17
container-absolute failure shape and pre/post identity mutations. Linux-only
controls exercise real /proc/self magic links, real namespace-root openat path
walk including absolute symlinks, escape/loop/stat mutation, executable bit,
unlinked-open-inode and full streamed hash. They are mandatory in the immutable
Linux guest. Windows reports three new Linux controls skipped, never simulated
PASS; original snapshot Linux durability control remains separately mandatory.

Full discovery expects108=original103+5. Source checks/CLI and declared-only
payload reconstruction must run before MAIN admission. This package performs
no remote action or device operation. Linux/kernel identity, whole independent
model correctness and production/performance remain pending actual execution.

R18→R17 identity body edits are recorded independently; inherited budget test
first reverses that layer, then originalR17→R16 and originalR16→R15 exactly.
Original snapshot/native handlers and publication_common bytes remain unchanged.
