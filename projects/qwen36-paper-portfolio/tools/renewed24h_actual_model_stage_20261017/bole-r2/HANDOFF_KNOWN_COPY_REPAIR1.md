# Root-repeat known-copy identity repair1

Original1341 source/FAIL/raw and observer-secondary effects remain unchanged.
Actual patch imports QwenGatedDeltaNetAttention as _GDNBaseCls, then copies
AscendGatedDeltaNetAttention.forward onto that target. Both inherit the same
GatedDeltaNetAttention; the receiver is not an Ascend instance. Original plain's
isinstance predicate is invalid for this known-copy installation. Its other
checks do not repair that mismatch. There is no evidence requiring unwrap.

Only GDN now uses gdn_copy_identity.validate. Original plain/native-model and
decoder identity, capture boundaries, four forwards, math, resources/clock and
independent readers remain. The new validator checks all four canonical module
identities/sources, actual target class/direct common-base MRO, exact patch
aliases, target.forward is original Ascend.forward, exact bound target receiver,
absence of instance override/wrapper, exact original function globals/qualname
and compiled complete-source body. A bounded <=16KiB primitive identity receipt
is exclusively persisted per rank/PID/layer BEFORE aggregate rejection.

Evidence qwen_gdn_linear_attn68663/885c... and gdn_base2072/7fec... are exact
previously copied actual660 sources, not claims of current worker binding.
Runtime compares installed paths/hash/object identities. The software producer
test executes the real patch's non310p assignment AST and original forward body;
hardware constructors/decorators are explicitly software shells. It reproduces
old plain failure while all other old predicates pass; no backend/model PASS.
Negative target/receiver/module/globals/code/wrapper/source cases all reject
after a primitive report. Actual worker construction source selects Qwen class.

119 complete controls remain mandatory on actual same-image CPU frontdoor.
No NPU run or qualification is performed here. R1341 model loaded/health/raw
completion is not numerical FAIL/PASS: root witnesses had not entered. No
controller, numerical epsilon, calibration, artifact writer or alias guard is
weakened. New output/owner identities retain whole3600/cleanup180/window bounds.
COMMANDS actual bound SOURCE must be filled only after real bind; no old result
or prepared source is accepted as a new PASS. CPU and model original workflows
are reused. This scope is root attribution only, not publication/performance.
