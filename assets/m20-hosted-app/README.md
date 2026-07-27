# Module 20: Hosted app kit

The supplied scaffold plus the four templates the lessons fill in.
Everything runs against the Module 19 lab service by default: free,
local, no key that costs money. A real provider is an optional swap in
.env plus a dated recipe, and only ever that.

## What's in here

```
m20-hosted-app/
├── README.md                              # this file
├── scaffold/                              # the starting project (lesson 2 on)
└── templates/
    ├── application-contract.template.md   # lesson 1: the promise, before the provider
    ├── decision-note.template.md          # lesson 3: HTTP vs SDK, observed not argued
    ├── state-record.template.md           # lesson 5: sent / retained / discarded / redacted
    └── capability-record.template.md      # lesson 6: one media input, measured and dated
```

## The path through it

Lesson 1 writes the contract with no code open. Lesson 2 copies the
scaffold and makes it yours. Lesson 3 compares direct HTTP against an SDK
and keeps one. Lesson 4 is streaming, cancel, and timeout, all visible.
Lesson 5 bounds the state and proves the bound. Lesson 6 measures one
image-plus-text input. Lesson 7 mocks the failures, runs the contract
tests, and finishes a local release with the Module 18 release
discipline: README replayed, release card, rollback proven.

Bundle the artifacts as Hosted_Model_Application.zip when you finish. It
stays on your machine, like every artifact in this course.
