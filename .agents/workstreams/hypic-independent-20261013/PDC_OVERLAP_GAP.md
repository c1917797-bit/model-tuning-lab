# PDC/PIC overlap gap — host evidence only

CORRECTION from reviewed benchmark generator023e: relocation is private bridge
AFTER native8192, not absolute PIC start. Measured layout A+bridge+B+tail puts
PIC at9216-15360; ordinary8192 PDC hit therefore does NOT overlap B.
The overlap controls below remain valid unsupported-shape diagnostics, but
are NOT evidence that the successful-case ruler requires overlap handling.
Current smoke recipe lacks A and must not replace the formal matched ruler.
Independent formal_layout records geometry without copying benchmark code;
tokenized distinct streams, warmups and actual hits still require integration.

Operation0238 passes7 controls including four-rank formal-scale cases.
For total32768, PIC16384, relocation1024/4096/7168, an ACTUAL computed
prefix8192 overlaps the selected PIC. Current plan_mixed_queries returns
NativeQueryPlan(reason=pdc-overlap), skips0 and preserves all remaining rows.
An actual computed prefix ending at PIC start allows16376 body omission
with correct absolute causal endpoints. This is planner proof, not NPU proof.

Native-prefix workload parameter8192 is NOT proof of actual8192 PDC hits.
Current synthetic_compact_workload uses prefix length equal to relocation;
it does not yet encode or prove the successful-case8192 native-prefix ruler.
Do not silently relabel it or shift PIC positions to obtain easier hot coverage.

Required next work: recover the supplied successful-case exact token layout,
freeze G1-G4 identical request recipes, observe actual computed-prefix lengths,
and implement/validate overlap handling with correct incoming GDN and owned
KV material semantics. If unsupported overlap stays native, include it in
the full denominator and report fallback; never count it as algorithm activation.
Current PDC flag/control tests do not satisfy PDC coexistence acceptance.
