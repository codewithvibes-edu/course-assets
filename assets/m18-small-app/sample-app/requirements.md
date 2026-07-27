# Requirements: snip

Written before the build. Three stories, observable criteria, ugly cases
included. The test map points back at these IDs.

## Story 1: capture

As the terminal user, I want to save a snippet with optional tags so the
hard-won one-liner survives the terminal closing.

- AC-1.1: Given a text and tags, when I run `add`, then `list` shows the
  snippet with its tags and save date.
- AC-1.2: Given no tags, when I run `add`, then the snippet saves and
  lists cleanly. Tags are optional, never required.

## Story 2: retrieve

As the terminal user, I want to filter and search so finding beats
re-googling.

- AC-2.1: Given snippets with tags, when I run `list --tag X`, then only
  snippets tagged X print.
- AC-2.2: Given saved snippets, when I run `search Q`, then matches
  against text or tags print, case-insensitive.

## Story 3: prune

As the terminal user, I want to delete by id so stale snippets leave.

- AC-3.1: Given a snippet with id N, when I run `delete N`, then it no
  longer lists and the others survive.

## Ugly cases

- AC-U.1: Given a store file someone hand-edited into invalid JSON, when
  any command runs, then snip reports the file and refuses. It never
  silently replaces my data.
- AC-U.2: Given empty or whitespace text, when I run `add`, then snip
  refuses with a message.
- AC-U.3: Given an id that does not exist, when I run `delete`, then snip
  says so and changes nothing.
