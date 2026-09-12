# T22 upstream retirement audit

## Decision

Do not infer quality from the fact that an optimization once existed upstream.
The target vLLM-Ascend v0.23.0 image contains weight prefetch and
MatmulAllReduce paths, but newer upstream history explicitly retires both
areas. Their code remains usable only as pinned evidence for target-version
experiments; neither feature is automatically eligible for final delivery.

The next bounded-prefill experiment must ablate MLP weight prefetch. The
official v0.23.0 MatmulAllReduce path remains the decode control because prior
exact-shape measurements show it is about twice as fast as decomposed
MatMul+AllReduce for decode M=1. Do not revive the deleted
MatmulAllReduceAddRMSNorm graph pass.

## Authoritative upstream evidence

At audited vLLM-Ascend HEAD
`5cb98caaadeff42b5b62b996e34bb2aaa29d20fd`:

- `e77502ef715f612f2cc6f3c833174431f26cb765` / PR `#11949`
  removes weight prefetch implementation, configuration, documentation,
  support-matrix claims, and tests. The upstream-stated reason is
  `underutilized and low-value`; the removal records no runtime test.
- `2ee50f3847e4873e61d280911b2a24d85f5278d6` / PR `#12119`
  removes the MatmulAllReduce configuration, linear dispatch, fused
  AllReduce-RMSNorm graph pass, custom operator, documentation, and tests. The
  upstream-stated reason is that these paths were `deprecated/internal`.
- Both removals are on main and later release branches but are not ancestors of
  the pinned v0.23.0 release. Therefore they explain lifecycle status without
  changing what is physically present in the target image.
- The surviving dense Qwen prefetch E2E functions in the audited tree are
  marked `skip(reason="test is broken, fix me")`. This is a direct negative
  evidence signal, not a working validation result.

## Consequences for this workstream

1. Separate upstream-stated facts from inference. The recorded removal reasons
   above are facts; whether either feature regresses Qwen3.5-27B BF16 on 910B4
   is still unknown until locally measured.
2. Treat the current runtime monkeypatch's prefetch hooks as an experimental
   compatibility carryover, not a quality-assured optimization. Require an
   on/off ablation against identical bounded-prefill settings.
3. If disabling prefetch is neutral or faster, remove those hooks from the
   final candidate. If it is faster, retain it only with exact-shape,
   repeated-run, all-357 quality, and rollback evidence that outweighs the
   upstream retirement signal.
4. Keep stock v0.23.0 MatmulAllReduce for decode. The bounded-prefill
   decomposition remains a narrow TTFT experiment because T20 showed an 87.193%
   c1 TTFT improvement, but it cannot be generalized to decode or promoted
   before the complete gate.
5. Do not port deleted graph/operator code from a later branch into the final
   monkeypatch. Prefer a currently supported upstream replacement if one is
   found; otherwise record the gap rather than recreating retired machinery.

## Quality guarantee boundary

No process can guarantee borrowed code merely because it is upstream. This
project guarantees a defensible adoption decision through pinned provenance,
documented acceptance or non-acceptance reasons, exact target-stack testing,
paired semantic validation, stress and performance gates, and reversible
startup-time loading. Unknown upstream rationale blocks promotion.
