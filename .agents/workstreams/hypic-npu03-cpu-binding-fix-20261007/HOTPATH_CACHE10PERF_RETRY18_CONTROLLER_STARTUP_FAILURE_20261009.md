# Retry18 controller-only startup failure — 2026-10-09

This was not an NPU experiment and did not create an attempt root. Controller
operation `exec-00000000000002f7` exited 1 after 78 ms, before root creation,
service launch, health, or scoring. The traceback was
`UnboundLocalError: local variable 'quality' referenced before assignment`
while checking retry17 receipt hashes: the check ran before the local import.

Immediately afterward, direct-target inspection confirmed the retry18 root
did not exist, physical NPU0–3 had no running processes, and port 8223 was
free. The controller now uses standard-library SHA256 for this pre-import
receipt gate. Its corrected source is preregistered at SHA256
`c11a6223dea01ab85c6b91e1cc59ab39092aab0572baa0d724832df9eee9b139`; the
focused controller unit suite passed 25/25 and `--help` exposes retry18.

Retry18 remains the same planned unique root because no contract, service, or
raw attempt artifact was created by the failed controller initialization.
Before any actual launch, re-run its no-`--run` admission path, then take a new
physical NPU0–3/8223/root snapshot. Do not count this control-plane error as a
HYPIC performance result.
