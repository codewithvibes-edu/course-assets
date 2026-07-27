# Requirements: [app name]

Written BEFORE the build. The build does not get to negotiate with this file.
Three stories, each with acceptance criteria you can observe from outside
the program. At least one criterion covers an ugly case.

## Story 1: [the core job]

As [the one user], I want to [do the job] so that [the visible result].

**Acceptance criteria:**

- [ ] AC-1.1: Given [concrete input], when [action], then [observable result].
- [ ] AC-1.2: Given [concrete input], when [action], then [observable result].

## Story 2: [the second-most-important thing]

As [the one user], I want to [...] so that [...].

**Acceptance criteria:**

- [ ] AC-2.1: Given [...], when [...], then [...].

## Story 3: [the thing that makes it trustworthy]

As [the one user], I want to [...] so that [...].

**Acceptance criteria:**

- [ ] AC-3.1: Given [...], when [...], then [...].

## The ugly case (required, at least one)

- [ ] AC-U.1: Given [the empty file / the missing column / the duplicate /
      the garbage input], when [...], then [the program does something
      deliberate: a clear message, a skip that gets reported, a refusal].
      "Crashes with a traceback" is not deliberate.

## Rules for this file

1. Every criterion is observable: input in, visible behavior out. "The code
   is clean" is not a criterion. "Running X prints Y" is.
2. In lesson 5, every test you accept must point at a criterion ID from this
   file. A test that points at nothing gets deleted or gets a criterion.
3. If a new feature idea shows up mid-build, it goes in a version-two list,
   never in this file. This file was finished before the build started.
