# 074repair2 — Docker-client AS inheritance only

Original074R1 failure remains unchanged: no output/container was created. MAIN actual read-only0a8f observed Docker Go `failed to reserve page summary memory` under inherited512MiB AS, while the exact same command with `/usr/bin/prlimit --as=unlimited --` returned0. This packet has not itself executed same-image Docker.

Both real Docker child entry points are now wrapped: every metadata/create/inspect/stop call via run(), and start --attach Popen. Only an argv beginning exact `/usr/bin/docker` is eligible; Python/arbitrary/wrapped commands are rejected. Host softAS512MiB/unlimited hard, guest8GiB, ordinary RAM16.5GiB floor,600child/1000whole/90cleanup, output1GiB and sealed80/100 ledger policy unchanged. No new resource controller.

Every run() response now records requested/actual argv, exit, original stdout/stderr and elapsed. Once output exists it is an exclusive DOCKER-CALL receipt; before output admission, nonzero output is retained as MAIN_DOCKER_CLIENT_FAILURE in the original operation stderr, so the assertion cannot mask Go root cause. Attach stderr remains the original child.stderr file. No retry or weak success gate.

diagnose.py and cpu_entry.py are exact074R1 bytes. Diagnostic inputs, independent recurrence, raw RO mount tree, seed/mathematics and qualification=false remain unchanged. Five software controls passed locally (including exact wrapper/reject non-Docker and checking both real subprocess callsites); this is not a Docker/NPU result. MAIN alone source-audits and runs.
