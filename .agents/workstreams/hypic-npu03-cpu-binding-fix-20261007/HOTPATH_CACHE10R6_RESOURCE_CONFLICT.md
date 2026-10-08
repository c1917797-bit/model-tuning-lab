# cache10r6 full HYPIC arm — actual NPU2 collision before health

- Target: chicaihong01/ma, physical NPU0–3 only; original full 127-sample, 2048-token HYPIC arm. Passive Docker device mappings were not used as an exclusion criterion.
- AWMCP direct-peer operation: `exec-000000000000150a`. The watcher observed ten consecutive actual-idle checks and launched at `2026-10-08T16:20:00Z`.
- Artifact root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r6-full-hypic`.
- Startup guard observed actual physical NPU2 PID `1426552` at `2026-10-08T16:21:22.619779Z` and again at `16:21:23.925701Z`. It belonged to foreign container `efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6`, not the owned service. Probe errors: none.
- Guard stopped before service health or scoring: `0/127`; controller exited 1 at `16:22:26Z`. This is an environment/isolation-invalid attempt, **not** a HYPIC quality or algorithm verdict. Do not reuse its root or pair it with a baseline.
- Owned container `ab5de0baf21efb068fad9b58539b2a52cf426532d17dfa2dffe3a224b8621164` was removed; stop receipt confirms physical NPU0–3 released and port 8223 free. Foreign container was not modified.

Immutable raw-artifact SHA-256:

| Artifact | SHA-256 |
| --- | --- |
| `contract.json` | `89490d2b45967cffe3296242e16292f61004a58005f50e6fab13e7893545fa48` |
| `arm-result.json` | `e29c5fb4321728e21bc561ac42ceacb711888e520fc4971b363c84bd7f02a2c3` |
| `hypic-only/lane-guard.json` | `86641f18d3647d1f015167395657e0c9100b3c70f49a10283cae7a937d392565` |
| `hypic-only/service-stop.json` | `df9c7619ccd28a7b251ac7be55ba846a3589df1530dd6b3ddebe16e2edc8382b` |

On the next run, gate on **actual** physical NPU0–3 processes plus the experiment port, not Docker mappings. Continue the startup and scoring guard; abort on a real foreign PID or probe error, retaining a new unique root and exact-owned cleanup evidence.
