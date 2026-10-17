# R20 source-only memory/metadata repair

R19 failed before any create at the unchanged cumulative host+CLI 512 MiB
predicate. Its exact owner, source, empty payload inode and reservation journal
are reopened by prior_empty_r19; they are never deleted, rewritten or promoted.
The old control bytes remain charged by the complete original P scan. R20 has a
distinct output, payload leaf and journal; legacy generation 23 is unchanged.

The two large historical tree JSON arrays are streamed with complete SHA,
schema, ordered unique paths, exact root, EOF and stable file identity. Their
initial/final retained data SHA checks remain complete. Initial original13
validation and final original13 verifier remain the exact original bodies.
This is not a claim that original13 validation is now fully streaming.

Under the held original storage lock, complete15 strong metadata is sampled
BEFORE original full validation and AFTER it, with equality required. Only then
is the PID/source/lock-bound immutable baseline created. Hot checks compare the
complete15 directory inventory and dev/inode/type/mode/size/mtime/ctime/uid/gid/
nlink; no rebaseline is allowed. Original accounting, P scan, legacy history,
capacity/free-space, journal and original new2/fourCID writer checks remain.
The old13 CID/writer checks remain at original full entry/final boundaries;
they were not all hot checks in R19 and are not falsely described as such here.
This equivalence is scoped to ordinary local VFS/nonprivileged mutation, not
root/raw-device/NFS attacks. Final full content hashes are not cached away.

Original RSS gate and exception retain priority. A bounded best-effort report
records actual self/child highwaters on failure; inability to write that report
cannot mask the original error. No actual R19 self/child numeric split existed.

Whole2700/cleanup270/postverify900, model32 GiB, CPU8 GiB, host .5+reserve8,
512 MiB cumulative host+CLI, P80/free100, P30+opt2=combined32, all numerical
thresholds and the renewed UTC cutoff remain unchanged. Firstdecode is only a
diagnostic; intentional stop preserves parent/client FAIL. No numerical,
model, performance, task, slot-reuse or long160 qualification is granted.

Synthetic real Lease.open controls prove assembly order and rejection paths,
not actual15 data revalidation or whole-owner512 fit. The 135520-row parser
pressure test is synthetic and bounded; its RSS is not an owner fit estimate.
Actual same-image full software/IPC/HTTP, full closed validation and initial
owner RSS must still pass under MAIN's fresh exclusive admission. No resources
have been launched by this preparation.
