# Module 25: Daily-driver kit

Everything m25 operates on: the deterministic fixture repo, the
Daily_Driver_Ops_Kit template tree, and two dated harness recipe packs
presented on equal footing with no favorite.

## What's in here

```
m25-daily-driver/
├── README.md
├── fixture-repo/          # "orchard": the repo you operate ON (see its README)
│   ├── data/              # tiny CSVs with four planted findings
│   └── scripts/           # repo_check, slow_task, run_with_lock, notify
├── kit-templates/         # the Daily_Driver_Ops_Kit tree, one file per artifact
└── recipes/
    ├── claude-code-pack.md   # dated pack, v2.1.219, tested 2026-07-24
    └── codex-cli-pack.md     # dated pack, v0.144.1, tested 2026-07-24
```

## How to use it

Copy `fixture-repo/` out, git init it, verify it with its README's smoke
checks. Copy `kit-templates/` as the start of YOUR ops kit. Then pick
ONE recipe pack and run the eight drills; the packs translate the same
neutral contracts into each harness's current syntax, and either one
covers the whole module. The packs are dated because harness surfaces
move fast; when a pack disagrees with the harness docs, the docs win,
and the neutral contract files are the part that survives the churn.

Bundle your finished tree as Daily_Driver_Ops_Kit.zip. Learner-held,
like every artifact in this course: no submission, no upload, no
harness credentials stored anywhere but your own machine.
