# Prospective lifecycle validation — minimal service boundary

Scope remains27B physicalNPU0-3 oneTP4, unchanged officialimage, independently
implementedC1/C2 only. No distributedC3, no oldalgorithm imports or foreign changes.
This is future M6, NOT an accepted rollback result.

Official source review: collective_rpc exists under serve/dev/rpc, gated by
VLLM_SERVER_DEV_MODE; registration also adds otherdevelopmentrouters.
Do NOT enable it, do NOT expose a newadminendpoint, do NOT deserialize code into
workers. Existing service/ownedcontainerboundary is sufficient for package
disable/uninstall/restart. Review receipt binds exactofficialsourcebytes.

Lifecycle sequence after required performance/quality gates:
1. Disabled control: samepackage mountedread-only, explicitswitch off, unchanged
officialimage, real frozen semanticrequests. Prove exactlaunchswitch/source,
successfulresponses, fourphysicalownedworkers and absenceoftreatmentactivation.
2. Enabled boundedcontrol: explicitswitch on withsameimage/package, knownpublic
producer/privateprefill requests andfourrank48C1/16C2source-bound receipts.
This is lifecycle/mechanism coverage, not newformal speed or fullquality.
3. Stop/release that exactownedcontainer throughfrozenlabel/image/CID/device guard.
Keep originalrawdirectory, logs, responseIDs, namespaces, sourcehashes andisolation.
4. Uninstall/restart: newownedcontainerfromsameofficialimage without/probe mount,
withoutbootstrap/PYTHONPATH injection andwithouttreatmentswitch; repeatdisabled
semanticprotocol. Prove newinstance/PIDs, requestssucceed, noactivationmarker,
officialsourcehashesunchanged. Uninstall here means removing thepackage from
servicestartup thenrestarting, NOT claiming hotin-processuninstall was tested.
5. Independentlyaudit allstates andexactownCIDabsence/strictportbind/finalphysical
release. Foreignprocesses are never stopped or altered.

Implementation constraints:
- Derive a separate lifecyclecontroller fromreviewedgenericownership/guard code.
Do not change current frozenperformance147 or qualityR2/full163 source identities.
- Disabled public-materialreadiness must be skipped becausealgorithm is off;
never countnativefallback asenabledhotproof.
- Only lifecycle-specificswitch/readiness/package-mount spans may differ.
ASTdiff controls must keep guard/deadline/precisecleanup intact.
- Freeze payloads, stagecontracts, newroots, sufficient boundedtimeout andauditor
BEFORE hardware. Deviceactualidle/ports/directroute admission everylaunch.
- Only oneownedcontroller; running/unclear means pollsamehandle, notrestart.
- Fixedlatesthumanstop2026-10-17T06:48:09Z, noextension; preserve/release ownstage.

Formal full127x3pairedquality remains after completeG1-G4three-round performance
gates, per runtime-monkeypatch-delivery. Preparedcontracts now state this explicit
prerequisite. A failed/interruptedperformance stage cannot silentlyskip thatgate.
Allplans/sourceprobes are offline evidence only; noM6or29Skillfunctionalacceptance.
