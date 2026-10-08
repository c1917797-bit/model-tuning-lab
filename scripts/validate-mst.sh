#!/bin/sh
set -eu

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

warn() {
  echo "WARN: $*" >&2
}

test -f AGENTS.md || fail "missing AGENTS.md"
test -f .agents/skills.registry.yaml || fail "missing .agents/skills.registry.yaml"
test -f .agents/HANDOFF.md || fail "missing .agents/HANDOFF.md"
test -d .agents/skills || fail "missing .agents/skills directory"


# Current handoff shape: this is the fast resume surface for future agents.
for section in   "## 0. Status"   "## 1. North Star"   "## 2. Current Focus"   "## 3. Recent Progress"   "## 4. Current Action"   "## 5. Next Actions"   "## 6. Validation Commands"   "## 7. Do Not Do"   "## 8. Recovery / Resume Commands"
do
  grep -q "$section" .agents/HANDOFF.md || fail ".agents/HANDOFF.md missing section: $section"
done

count=$(find .agents/skills -mindepth 2 -maxdepth 2 -name SKILL.md -type f | wc -l | tr -d ' ')
[ "$count" -gt 0 ] || fail "no .agents/skills/*/SKILL.md files found"

missing_frontmatter=0
for file in $(find .agents/skills -mindepth 2 -maxdepth 2 -name SKILL.md -type f | sort); do
  head -n 1 "$file" | grep -q '^---$' || {
    echo "FAIL: $file missing YAML frontmatter delimiter" >&2
    missing_frontmatter=1
  }
  grep -q '^name:' "$file" || {
    echo "FAIL: $file missing name frontmatter" >&2
    missing_frontmatter=1
  }
  grep -q '^description:' "$file" || {
    echo "FAIL: $file missing description frontmatter" >&2
    missing_frontmatter=1
  }
done
[ "$missing_frontmatter" -eq 0 ] || exit 1



# Loop engineering framework must include controlled next-loop and non-drift semantics.
if [ -f .agents/skills/mst-loop-engineering-framework/SKILL.md ]; then
  grep -q 'Non-Drift Loop Contract' .agents/skills/mst-loop-engineering-framework/SKILL.md || fail "mst-loop-engineering-framework/SKILL.md missing Non-Drift Loop Contract"
  grep -q 'Generic Loop-Control Skill Pattern' .agents/skills/mst-loop-engineering-framework/SKILL.md || fail "mst-loop-engineering-framework/SKILL.md missing Generic Loop-Control Skill Pattern"
  grep -q 'Architecture Orientation Gate' .agents/skills/mst-loop-engineering-framework/SKILL.md || fail "mst-loop-engineering-framework/SKILL.md missing Architecture Orientation Gate"
  grep -q 'Template / instance boundary' .agents/skills/mst-loop-engineering-framework/SKILL.md || fail "mst-loop-engineering-framework/SKILL.md missing Template / instance boundary"
  grep -q 'Target repositories own their concrete production paths' .agents/skills/mst-loop-engineering-framework/SKILL.md || fail "mst-loop-engineering-framework/SKILL.md missing target-repository ownership boundary"
  grep -q 'active production path and legacy/compatibility path separately' .agents/skills/mst-loop-engineering-framework/SKILL.md || fail "mst-loop-engineering-framework/SKILL.md missing production-vs-legacy path rule"
  grep -q 'maker/checker split' .agents/skills/mst-loop-engineering-framework/SKILL.md || fail "mst-loop-engineering-framework/SKILL.md missing maker/checker split"
fi

if [ -f .agents/skills/mst-agent-self-orientation/SKILL.md ]; then
  grep -q 'Architecture/topology check' .agents/skills/mst-agent-self-orientation/SKILL.md || fail "mst-agent-self-orientation/SKILL.md missing Architecture/topology check"
  grep -q 'recent commits and current topology files' .agents/skills/mst-agent-self-orientation/SKILL.md || fail "mst-agent-self-orientation/SKILL.md missing recent-commits/topology rule"
fi
for dir in .opencode .codex .cursor runtime-skills; do
  if [ -d "$dir" ]; then
    warn "$dir exists; verify it is an adapter or product artifact, not canonical maintainer knowledge"
  fi
done


if [ -d .agents/evals/transformation-cases ]; then
  for case_file in $(find .agents/evals/transformation-cases -name '*.yaml' -type f | sort); do
    grep -q '^schema: mst-transformation-case/v1' "$case_file" || fail "$case_file missing transformation case schema"
    grep -q '^id:' "$case_file" || fail "$case_file missing id"
    grep -q '^validation_commands:' "$case_file" || fail "$case_file missing validation_commands"
    grep -q '^lessons_ingested:' "$case_file" || fail "$case_file missing lessons_ingested"
  done
fi

if [ -d .agents/evals/practice-iterations ]; then
  for case_file in $(find .agents/evals/practice-iterations -name '*.yaml' -type f | sort); do
    grep -q '^schema: mst-practice-iteration/v1' "$case_file" || fail "$case_file missing practice iteration schema"
    grep -q '^id:' "$case_file" || fail "$case_file missing id"
    grep -q '^validated_commit:' "$case_file" || fail "$case_file missing validated_commit"
    grep -q '^lessons_ingested:' "$case_file" || fail "$case_file missing lessons_ingested"
    grep -q '^validation_commands:' "$case_file" || fail "$case_file missing validation_commands"
  done
fi

if [ -d templates/skills ]; then
  for template_file in $(find templates/skills -name '*.SKILL.md' -type f | sort); do
    head -n 1 "$template_file" | grep -q '^---$' || fail "$template_file missing YAML frontmatter delimiter"
    grep -q '^name:' "$template_file" || fail "$template_file missing name frontmatter"
    grep -q '^description:' "$template_file" || fail "$template_file missing description frontmatter"
    grep -q '^## When to generate' "$template_file" || fail "$template_file missing generation guidance"
  done
fi

if [ -x ./scripts/validate-pack.sh ]; then
  ./scripts/validate-pack.sh >/dev/null
fi

if [ -x ./scripts/validate-workstream-governance.sh ]; then
  ./scripts/validate-workstream-governance.sh >/dev/null
fi

# Registry <-> filesystem consistency (additive lint).
if [ -x ./scripts/check-registry-consistency.sh ]; then
  ./scripts/check-registry-consistency.sh >/dev/null
fi

# Every registry entry needs discriminating routing data. This check uses
# POSIX awk so fresh clones do not need a YAML package just to validate.
sh ./scripts/check-skill-registry-routing.sh >/dev/null

# Continuity trailer contract on HEAD (skillsgit v2 standard; non-blocking
# warning because historical commits predate the trailer baseline).
if [ -x ./scripts/validate-commit-continuity.sh ]; then
  if ! ./scripts/validate-commit-continuity.sh >/dev/null; then
    warn "last commit predates the continuity trailer baseline; future commits must carry Maintainer-* trailers"
  fi
fi

# Flagship cloud-agent profile golden (characterization) test.
if [ -x ./scripts/test-cloud-agent-golden.sh ]; then
  ./scripts/test-cloud-agent-golden.sh >/dev/null
fi

echo "PASS: Maintainer Skill Tree structure is valid ($count skills)"
