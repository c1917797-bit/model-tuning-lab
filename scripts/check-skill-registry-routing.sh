#!/bin/sh
# Check per-Skill routing metadata without requiring a YAML package.
set -eu

registry=${1:-.agents/skills.registry.yaml}
awk '
function finish_entry() {
  if (id == "") return
  count++
  if (seen_id[id]++) {
    print "FAIL: duplicate Skill id " id > "/dev/stderr"
    failed = 1
  }
  if (!has_path || !has_purpose || purpose ~ /^Generated from /) {
    print "FAIL: " id " has absent path/purpose or generic purpose" > "/dev/stderr"
    failed = 1
  }
  if (trigger_count == 0) {
    print "FAIL: " id " has no triggers" > "/dev/stderr"
    failed = 1
  }
  if (scope_count == 0) {
    print "FAIL: " id " has no scope" > "/dev/stderr"
    failed = 1
  }
}
function reset_entry() {
  has_path = 0
  has_purpose = 0
  purpose = ""
  trigger_count = 0
  scope_count = 0
  section = ""
}
/^  - id: / {
  finish_entry()
  id = substr($0, 9)
  reset_entry()
  next
}
id != "" && /^    path: / { has_path = 1; section = ""; next }
id != "" && /^    purpose: / {
  has_purpose = 1
  purpose = substr($0, 14)
  section = ""
  next
}
id != "" && /^    triggers:/ { section = "triggers"; next }
id != "" && /^    scope:/ { section = "scope"; next }
id != "" && /^    [A-Za-z_]+:/ { section = ""; next }
id != "" && /^      - / {
  value = substr($0, 9)
  if (section == "triggers") {
    trigger_count++
    key = tolower(value)
    if (seen_trigger[key]++) {
      print "FAIL: duplicate exact trigger " value > "/dev/stderr"
      failed = 1
    }
  } else if (section == "scope") {
    scope_count++
  }
}
END {
  finish_entry()
  if (count == 0) {
    print "FAIL: no Skill entries found" > "/dev/stderr"
    failed = 1
  }
  if (failed) exit 1
  print "PASS: Skill routing metadata present (" count " skills)"
}
' "$registry"
