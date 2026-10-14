# Warmup protocol boundary

Latest draft0265: opt-in allow_public_tail selector and prefix-only GDN/KV
capture implemented. Defaultfalse; threeCPU controls pass. Real fourworker/
device correctness unverified. Prepared warmup builder now emits B+tail256,
but must not run until the enabled prefix path and new source manifest pass.
The historical unimplemented discussion below describes the prior checkpoint.

Reviewed benchmark defaults0263: two PIC producers and two native warmups,
warm tail256. They are unscored and separate from40 measured/c16 requests.
Independent native warmups use A8192+distinct tail256, preserving this geometry.

Current independent canonical material interface accepts ONLY exactB16384.
Thus prepared independent_formal_warmups uses B-only producers, not the
reference B+tail256 producers. This is an explicit adaptation, not exact
warmup parity or completed paper reproduction. It must be reported and frozen
identically across groups if used. Do not hide this discrepancy.

For exact workflow parity, extend material capture to the selected B prefix
within B+tail, including intermediate GDN/conv state and full KV ownership;
simply treating whole B+tail state as B is incorrect. That extension is not
implemented or accepted. Main measured A+bridge+B+tail layout remains fixed.
