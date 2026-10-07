# H8 full-v3 controller abort and exact-owned recovery

Actual operation MA0f9d ended exit1 after173679ms. The intended full11520
numerical/graph/lifecycle experiment did not complete. Frozen source173:
ff9eb41b3cda2adaf75dbee429cdf672d30846a58f5f3c30b92d8d51632893d3.
Production/candidate SO3f7cc and previous warm1280+1 prerequisite are unchanged.

The observed infrastructure failure was summed MAIN + all four concurrent
Docker CLI RSS262624KiB,480KiB above the256MiB whole-controller limit.
A per-Python VAS limit and the aggregate concurrent-controller budget are
different ledgers. The same latched peak check ran after cleanup inspect
commands and prevented their results from being consumed for exact-owned stop.
Consequently the original cleanup explicitly reports failure; neither it nor
the original RESULT is rewritten.

Original result Ref:
- /cache/cch/qwen36-paper-preparation-20261007/recurrent/MAIN-h8-full-runtime-v3-fenced-20261007-001/RESULT.json
  SHA c7ab728b20fd09d646fca07ff7352350c7a997fdfb7133bdefa3f04288abf7a7
- Same output cleanup.json SHA b4512de41e33e6992dfa49759827623b8455ed540dbbbf73bbe6260ef2448717.

Exact four owned CIDs were stopped, not deleted, by MA0fad after all four
full inspect validations and re-inspection before each action:
- physical4 eaa8c7c80331755818abe75ad71824e069bb1384862ca855b687f33700cf47ac
- physical5 9b92824bf0c2a2c22689fbc48b5aa1c7ce9fc2f2f179bf94d8764791e1d3c503
- physical6 a095f987e5e1de212e54f8e592d1a0e36dc2ef61da9645772b2989bb1f727a05
- physical7 35ced55290fec4d9cf87db67c5f086eb7b41f94e28e2d3ec940449e165e75f27

Recovery parent exit1 remains genuine: after all stops, after-SMI and protected
identity comparison, MAIN's final optional observer called nonexistent F.compute.
The complete original envelope is retained; no claim that this parent passed.
Independent READ-ONLY MA0fbd exit0/1387ms revalidated all four retained/Pid0/
noExec/noOOM, actual4–7 no compute PID + idle HBM/AICore baseline, protected0–3
same PID/start/cgroup/argv, and unchanged original failed RESULT. It used the
source-defined process_rows and idle_one APIs. No stop was repeated.

This evidence supports a controller-only successor with explicit concurrent
512MiB aggregate RSS accounting while per-Python VAS256MiB stays unchanged,
40.5GiB ordinary floor, real child-process resource regressions, and an
ownership-preserving cleanup lane that records resource errors but does not
treat latched ordinary admission failure as permission to skip stopping exact
owned jobs. It does not support a tolerance increase, kernel repair, paper-wide
no-go, unfenced model-runtime proof, performance gain, or task accuracy claim.
Original11520 and cutoff remain fixed. All source-only preparation is pending
MAIN review/admission; do not rerun the old source.
