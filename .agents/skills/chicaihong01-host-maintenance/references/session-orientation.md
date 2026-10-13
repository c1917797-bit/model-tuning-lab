## Start-of-turn remote orientation

From the canonical target repository, capture at minimum:

```sh
git fetch origin
git status --short --branch
git log -8 --decorate --oneline
git worktree list --porcelain
hostname
uname -a
docker ps
npu-smi info
ss -lntp
grep -E '^(MemTotal|MemAvailable|Hugetlb):' /proc/meminfo
```

Read `.agents/HANDOFF.md`. For every relevant active `work/*` tree, read its
`task.json` and branch-local `HANDOFF.md` before touching claimed files,
containers, ports, processes, or NPUs.

Use `.agents/git-policy.yaml` as the repository override for workstream
lifecycle limits. The current active worktree budget is eight. Inventory first;
never reclaim a dirty, in-use, unpushed, unmerged, or unsuperseded worktree.
