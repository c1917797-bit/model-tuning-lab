# R10 seeded-prefix successor after R9 state-shadow failure

R9 fe6ca087/06f7 is terminalexit1 and NOTpromoted.0707 independently checked
118 sourcebindings,173clean physical samples, exact132e8354 CID removal,
8233free,physical0–3empty;0/16 successful responses. No actual state writes or
finite gate receipt occurred in failed rank/step/layer groups. Original rawroot
and SHA evidence immutable. Ranks0/1/2 at layer0 step9 have state maxscaled
2.286/5.814/3.598; output andconv pass. Rank3 failing receipt not observed,
do NOT invent it. Context070c: firstfailedrequest computed10240/scheduled22528,
second computed11776/scheduled18428. Earlier prefixes had advanced native state.

## Testable mechanism
R9 derives live prefix T/S from zero/identity passes, then applies T@H+S to
nonzero incoming state before seeding suffix. A finite-precision native chunk
kernel need not be exactly affine as a function of H because internal rounding
is not linear. This additional approximation is unnecessary for the supported
one-cached-body/two-live-window geometry. It is a HYPOTHESIS, not a diagnosis
proven by aggregate residuals; retain possible grouped-head/varlen effects.

## Independent successor
Keep packed conv, shared WY, source binding, materialleases, native1 batching,
C2 and default-off delivery. Replace live affine reconstruction only:
1. Construct initial seeds: actual private incoming H for each prefix/native
   window (zero when has_initial=False), zero dummy states for suffix windows.
2. One packed H pass obtains actual prefix terminal states. Apply the SAME
   cached body T/S as serialized incumbent to those actual prefix states.
3. Use those states as suffix seeds, keep actual prefix seeds unchanged; one
   second packed H/output pass returns outputs and actual terminal states.
   No-suffix requests apply cached body once after actual prefix terminal.
This uses2 H passes rather than3 and no identity-width U/T approximation.
Require bounded exact plan shape and full private-buffer finite/commit gate.

## Gates
FP64 linear recurrence, grouped unequal K/V, exact conv/ownership/material
generation; add a nonlinear rounding simulator with nonzero continuation state
which falsifies R9 affine reconstruction and verifies seeded-prefix route
against serialized execution. Preserve source failure and tolerance .01/.003.
Freeze R10 config/manifest/independent auditor (state_passes=2 plus seed mode),
new rawroot, CPU/runtime shadow/disabled/lifecycle gates. Only then fresh
direct/physical0–3/ports/source/newroot admission. No standalone GDN NPU job,
no repeated unchangedR9. The prepared R9 disabled contract is WITHDRAWN as an
immediate device plan because its enabled prerequisite failed.

Full matrix/quality/lifecycle/29Skill goal remains incomplete. Fixed deadline
2026-10-15T19:04:09Z unchanged. No speed or quality inference from this failure.
