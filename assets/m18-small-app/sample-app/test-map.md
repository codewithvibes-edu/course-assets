# Test map: snip

| Criterion | What it promises | Evidence type | Where | Passing? |
| --- | --- | --- | --- | --- |
| AC-1.1 | saved snippet lists with tags + date | unit | test_snippets.py::test_add_and_list | yes |
| AC-1.2 | untagged snippet saves and lists | unit | test_snippets.py::test_add_without_tags_lists_fine | yes |
| AC-2.1 | --tag filters | unit | test_snippets.py::test_list_filters_by_tag | yes |
| AC-2.2 | search hits text + tags, case-insensitive | unit | test_snippets.py::test_search_matches_text_and_tags | yes |
| AC-3.1 | delete by id removes one, keeps rest | unit | test_snippets.py::test_delete_missing_id_reports_cleanly (survivor check) + manual | yes |
| AC-U.1 | corrupted store refused, never overwritten | unit | test_snippets.py::test_corrupted_store_reports_cleanly | yes |
| AC-U.2 | empty text refused | unit | test_snippets.py::test_empty_text_refused | yes |
| AC-U.3 | missing id reported cleanly | unit | test_snippets.py::test_delete_missing_id_reports_cleanly | yes |

## Manual evidence log

- AC-3.1: ran `add "a"`, `add "b"`, `delete 1`, `list`. Watched #2 survive
  with its id unchanged and #1 gone.

## Orphan check

No tests exist outside this table. (The whole suite is seven tests. Small
app, small suite, every row accounted for; AC-3.1's survivor check shares a
test with AC-U.3 plus the manual run below.)
