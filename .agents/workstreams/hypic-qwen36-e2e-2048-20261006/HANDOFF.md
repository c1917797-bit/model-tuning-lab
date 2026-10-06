# HYPIC Qwen3.6 TP4 2048-token E2E validation

## Objective

Complete a fresh HYPIC Paper-to-Ascend validation on physical NPU0-3 within
24 hours. The historical 1024-token quality evidence is reference-only; this
workstream owns a new 2048-token baseline and treatment.

## Frozen resources

- Branch: `work/hypic-qwen36-e2e-2048-20261006`
- Clone: `/cache/cch/model-tuning-lab-hypic-e2e-20261006`
- Artifact root: `/cache/cch/hypic-qwen36-e2e-2048-20261006`
- Physical devices: NPU0-3 only
- CPU set: 112-191
- Service port: 8223
- HCCL port range: 27000-27100
- NPU4-7 and their containers are protected.

## Commands

Static no-side-effect gate:

```sh
bash .agents/workstreams/hypic-qwen36-e2e-2048-20261006/run_hypic_e2e_2048.sh --self-test
```

Resumable full controller:

```sh
bash .agents/workstreams/hypic-qwen36-e2e-2048-20261006/run_hypic_e2e_2048.sh
```

The controller validates existing units before skipping them. A completed
baseline is reusable only when baseline-contract.json matches and every run
passes its raw-artifact check. Do not delete or overwrite partial JSONL files;
incomplete indexes are the resume boundary.

## Current state

Running on chicaihong01 through AWMCP direct peer
lgw_a6109c51076a4a2c9d2674ca5a8704a0. Active exec operation:
exec-0000000000000277. The owning controller PID was 1219649 at launch.
Poll that exact operation and controller-status.json; do not start a second
controller while it remains live. Goal deadline is 2026-10-07 11:39:37 UTC;
the timeout wrapper stops the controller about 15 minutes earlier and its
EXIT trap stops its owned container.

The baseline contract was frozen at
219e766d817442471b160598167bcca71191a62399706cf96558921beb147621
for physical NPU0-3 and the 2048-token quality ruler. At 2026-10-06
12:21 UTC both real-weight Canaries passed. They used identical 32,768-token
prompt hashes and returned the same full response with answer ZEBRA-41729.
The canary-gate.json SHA256 is
e539f53b309fd3ec691877d85c5ca13472d140e1579cbe142670c167721850f3.
The disabled-control event file is empty (SHA256
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855);
the enabled event file SHA256 is
2c350a2c58e5f5d6fc87250fcd7e2d81e90f5e100eca4b85da3fbe75569a2bca.
The enabled Canary emitted plugin activation in seven service processes and
an independent segment reuse event. Raw event files are under the artifact
root as no-cache/canary.hypic-evidence.jsonl and
hypic-only/canary.hypic-evidence.jsonl. The current phase is authoritative
only when read from controller-status.json.

An initial controller operation, exec-0000000000000263, was stopped before
service readiness after an escaped E2E_GATES variable entered the historical
sequence. It produced no performance or quality result. Its exit code was
124; owned baseline container exited and NPU0-3 were verified process-free.
Commit 9d9acf2 corrected the variable; the active operation above is the
first valid measurement attempt. Do not count the stopped attempt as an
algorithm failure or as a reusable baseline.

The supported vLLM general-plugin entry point is the removable runtime
delivery path; see DELIVERY.md. Final independent audit, rollback exercise,
resource-release proof, optimization iteration, terminal classification and
report are still pending.

After the controller finishes, run the historical 18-unit audit produced by
the wrapper, then record the measured optimization iteration and execute the
post-treatment disabled-control rollback. Store optimization-iteration.json
and rollback-evidence.json plus their raw files under the artifact root.
Use verify_hypic_rollback.py from this workstream with --root pointing at the
artifact root and --canary-script pointing at the historical workstream's
hypic_semantic_canary.py. Run it only after the controller operation is
terminal. The script refuses to proceed while controller.lock is held, checks
the exact two owned container identities and one-switch equivalence, executes
a real disabled request, stops the baseline, and records NPU/port release.
Pass --remove-owned-containers only after all experiment arms are terminal
and their evidence is preserved; it removes only those two named containers.
Finally run audit_e2e_closure.py from this workstream with root
/cache/cch/hypic-qwen36-e2e-2048-20261006 and output
/cache/cch/hypic-qwen36-e2e-2048-20261006/e2e-closure-audit.json.

The closure audit currently reports missing performance, quality, iteration,
and rollback evidence, as expected while the first performance run is live.
Do not treat this partial audit as a failure of the paper technique.
