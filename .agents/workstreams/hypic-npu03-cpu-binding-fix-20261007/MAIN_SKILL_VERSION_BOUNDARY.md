# Main-Skill version boundary for the HYPIC validation campaign

As of 2026-10-08, `origin/main` is
`ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2`. Its 29-Skill tree and
registry are unchanged from `f1f37a39bd86f7db5fd3ee3dea358ae6868275c6`.
The HYPIC worktree is on `work/hypic-npu03-cpu-binding-fix-20261007`.
Campaign evidence from that branch is not automatically evidence that the
exact main text or main registry routing produced the same behavior.

The branch differs in **seven** `SKILL.md` bodies, two associated
references, and the registry. `verify_skill_matrix.py` derives this from
Git blobs each run; it currently finds these bodies:

| Skill | Main Git blob | Work-branch Git blob | Bounded campaign code |
| --- | --- | --- | --- |
| `ascend-benchmark-evidence` | `03ade79d` | `e9c2a263` | V |
| `ascend-model-quality-evaluation` | `303658f0` | `019b3196` | P |
| `ascend-performance-optimization` | `50acfe94` | `cc8d3e67` | P |
| `chicaihong01-host-maintenance` | `4f226c75` | `e25fdec5` | V |
| `mst-loop-engineering-framework` | `32ae8445` | `10341d5f` | P |
| `paper-ingestion` | `69edbce7` | `beeb0507` | P |
| `paper-to-ascend-reproduction` | `d0298d9f` | `90fd7d45` | P |

The main registry blob is `2611864bbcf719d57920aae03ff9eb85521526b4`;
the branch registry blob is `9bbde82aa85c12c6365aeec3f36ca47ad8ad6bec`.
The quality-contract reference also differs
(`a3d5ca9a` main versus `30be89e7` branch), and the branch adds a
three-horizon reference for `mst-loop-engineering-framework`. The other
22 Skill bodies match main, but branch routing metadata still differs.

Two of the current **V11 bounded workflow** rows therefore used Skill
identities whose branch bodies now differ from main:
`chicaihong01-host-maintenance` and `ascend-benchmark-evidence`.
The branch-added continuous shared-NPU guard and stage-specific benchmark
activation/percentile guidance cannot be attributed to main verbatim.
Keep their HYPIC evidence as bounded work-branch validation; do not promote
those two main-version claims without exact-version analysis or focused
revalidation after reviewed promotion. Do not mechanically downgrade the
historical result either: first trace which text and check were in force
at each experiment checkpoint.

`mst-repo-onboarding` has unchanged Skill and registry blobs across its
tested main commit and current main. Its fresh-clone workflow was exercised
and reported in `ONBOARDING_FRESH_CLONE_ACCEPTANCE_20261008.md`, correcting
the earlier stale “fresh-clone unverified” note. The original clone is now
absent, so `skill-cases/mst-repo-onboarding.json` labels long-term portable
evidence `partial-evidence` rather than asserting an independently
replayed full acceptance. It verifies neither live host/NPU entry nor the
other 28 Skills.

Before calling any **main** Skill long-term verified, bind a real task,
the exact main Skill blob and registry context, an acceptance oracle,
raw-artifact hashes, environment/date, a repeatable check, and a failure
boundary. Structural validation and branch-local V/P/N alone cannot fill
those fields. Main promotion of revised Skill text requires reviewed
integration followed by version-matched focused validation.
