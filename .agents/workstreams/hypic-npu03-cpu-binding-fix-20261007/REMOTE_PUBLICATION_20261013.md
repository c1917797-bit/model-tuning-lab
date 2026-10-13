# Workstream publication restored — 2026-10-13

## Verified outcome
GitHub work/hypic-npu03-cpu-binding-fix-20261007 contains exact code checkpoint
b5d9c9398f7fd4571c76b163490f83d609ced96f. Remote main remains
ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2. This is branch publication,
not main integration or all29 Skill acceptance.

New evidence supersedes the previous remote-unknown blocker:
- mc0098: DNS resolved and HTTPS GitHub home returned200.
- mc009b: bounded non-interactive ls-remote returned exact main. No credential
  helper was configured and no userinfo was in origin URL. This does not
  identify the write credential source or explain the earlier timeout.
- mc009e: exact workstream push dry-run succeeded with no mutation.
- mc009f: normal push succeeded; fresh ls-remote proved code checkpoint
  equality and unchanged main.

No credential store/global config was changed or secret disclosed. A separate
Windows Git probe failed at getaddrinfo thread initialization; it is not evidence
of target-host networking. No Windows networking change was made.

## Resume
Read current HANDOFF/task and REMOTE_PUBLICATION_RECEIPT_20261013.json.
Do not retain authentication as a current blocker. Refresh remote refs before
integration; this successful snapshot does not guarantee future connectivity.
Next is a named, remote-start-checkpointed integration workstream from fetched
main. Validate the planning-schema and runtime-template minimal repairs against
their source/target hashes and validate the combined final tree if integrating
together. Keep unaccepted HYPIC active code and observer/native packages out.
Use serialized integration and target-owned merged state before validation.
The original experiment workstream remains in-progress/not-ready as a whole.

No quality, performance or profiling rerun. Additional device lifecycle work
awaits the human choice because the earlier device deadline has passed.
Counts remain12 bounded/17 partial; no NPU work in this publication stage.

## Publication boundary
The receipt pins the tested published code checkpoint. The later ledger commit
is separate, not a claim that the receipt proved its own future commit identity.
