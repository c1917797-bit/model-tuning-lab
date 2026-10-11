# HYPIC r19/c32 versus r20/c1 — read-only load/state localization

This report replays existing immutable r19 and r20 samples and HYPIC event
logs. It does **not** create device work, change a frozen decision, or prove
causality. Parent paired audits are r19 SHA256
`40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b`
and r20 SHA256
`44bd68b877f941af24422160941ca5006b8deabe5b3396f8e038fc3d6f41ae15`.

## Paired r19 rows, not just aggregate score

The 381 matched r19 scored rows contain 23 control-correct/HYPIC-wrong
losses and 15 control-wrong/HYPIC-correct gains, net -8 (227 versus 219).
The candidate had 134 requests with per-request four-worker hot proof;
the remaining 247 are **unproved**, not proven cold.

| r19 paired outcome | Hot proven | Hot unproved | Total |
| --- | ---: | ---: | ---: |
| Control correct, HYPIC wrong | 8 | 15 | 23 |
| Control wrong, HYPIC correct | 4 | 11 | 15 |
| Both correct | 75 | 129 | 204 |
| Both wrong | 47 | 92 | 139 |

Among the 23 losses, 16 HYPIC responses hit the 2048-token length cap:
7 hot-proven and 9 unproved. Among 15 gains, 3 hit the cap (all unproved).
The other 7 losses and 12 gains stopped without a cap. Hence extra
length-limited responses are a strong *association* with net quality loss,
but neither the cap nor missing hot proof alone is a sufficient explanation.
One hot-proven, naturally stopped loss is sample 082 repetition 1.

## Concrete load contrast, sample 059

In r19 c32, control sample 059 is 3/3 correct with natural stops. HYPIC is
0/3 correct with three length caps. Its first wrong response is not a cold
fallback: all four workers logged `worker_hot_request_verified`, each with
`skipped_prefix_tokens=16376` and
`complete_hybrid_repair_validated=true`. The second and third wrong responses
lack four-worker proof. During the first request's admission-to-hot interval,
the event stream reports five material evictions and five pending-gate
events; that interval is 242.42 s. These are contemporaneous global events,
not a victim/request-level causal attribution.

In r20 c1 with the same model, source, prompt/boundary and cap, both arms
are 3/3 correct on 059; HYPIC is 3/3 hot-proven, naturally stopped, and
has no length caps. For its first hot request, admission-to-hot is 5.73 s,
with zero material evictions and pending-gate events during the interval.
Across the whole runs, r19 HYPIC logged 126 material-ready and 116 evicted
segments, whereas r20 logged 3 ready and 0 evicted. Different workload size
and concurrency prevent treating these counts as a controlled effect.

The first r19 hot-proven wrong response diverges from its paired control
after 339 characters and contains local repetitions such as
`particles particles`; another 059 repetition contains `tactile tactile`.
This is a response-divergence signal, not a validated KV/position-state
fault. In r20, the first 059 paired responses share 3497 characters before
diverging but both answer correctly.

## What the evidence excludes, and what remains

- Missing four-worker hot proof cannot be the *sole* quality explanation:
  eight r19 losses, including a natural-stop loss, are hot-proven.
- A 2048-token cap cannot be the *sole* explanation: seven r19 losses stop
  without hitting it.
- Cache eviction cannot be assigned as the root from current logs: events
  lack victim/request identity, and hot-proven loss requests do not show a
  simple monotonic eviction exposure compared with other hot outcomes.
- The c1/c32 contrast supports prioritizing load-sensitive HYPIC
  decode/position-state and scheduler/materialization interaction. It does
  not separate these factors, and r20's post-hoc three-sample success does
  not overturn r19 `REJECT_OR_QUALIFY`.

Next device experiment, if performed, must be prospectively frozen with a
fresh root, matched source/model/prompt/2048 cap, explicit boundary, real
physical NPU0–3 isolation and one declared intervention. It should expose
request-level material victim/state identity or compare native versus
HYPIC decode state under the same c32 wave, rather than merely repeat r19
or broaden to unrelated operator tests. A subsequent new full matched
127×3 pair is required for any revised population-quality decision.
