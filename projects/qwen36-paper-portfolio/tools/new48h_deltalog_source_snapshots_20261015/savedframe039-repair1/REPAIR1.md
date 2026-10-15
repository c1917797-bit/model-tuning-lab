#039 repair1 — stage ABI only

Original039 was never deployed. Its stage JSON lacked authority, which actual host.wait_ge requires even in CPU/native mode. New entry adds exact authority=ar and parsed lifecycle from its actual CLI; existing source/pass_gate remain unchanged. Host, diagnose Decimal80/100, arithmetic/input/old gate and budgets are byte-identical039.

New test runs actual entry.main to produce STAGE_RESULT (diagnostic body replaced by software-only stub, not raw evidence), then evaluates the actual original host source-complete and authority predicates from its AST against that persisted JSON. Wrong source/authority and false pass_gate reject. CPU/native branch requires no NPU handshake and reads no other stage-specific fields; parent/result Ref paths remain existing host-owned behavior. All3 tests PASS, including signed cells and independent Decimal arithmetic controls. No NPU/container execution or raw numerics claimed.
