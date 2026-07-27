"""snip: keep terminal one-liners you keep forgetting.

Standard library only. Data lives in a plain JSON file next to this script
(or wherever --store points). See problem.md and requirements.md in this
folder for the artifacts that defined this app before it was built.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

DEFAULT_STORE = Path(__file__).parent / "snippets.json"


def load_store(store_path):
    """Read the snippet list. A missing store is an empty store. A corrupted
    store is reported and refused, never silently replaced (AC-U.1)."""
    path = Path(store_path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise SystemExit(
            f"snip: {path} is not valid JSON ({err}). "
            "Fix or remove the file; refusing to overwrite your data."
        )
    if not isinstance(data, list):
        raise SystemExit(f"snip: {path} does not contain a snippet list.")
    return data


def save_store(store_path, entries):
    Path(store_path).write_text(
        json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def next_id(entries):
    return 1 + max((entry["id"] for entry in entries), default=0)


def add_snippet(store_path, text, tags):
    """Add one snippet. Empty text is refused (AC-U.2)."""
    if not text.strip():
        raise SystemExit("snip: refusing to save an empty snippet.")
    entries = load_store(store_path)
    entry = {
        "id": next_id(entries),
        "text": text.strip(),
        "tags": tags,
        "created": date.today().isoformat(),
    }
    entries.append(entry)
    save_store(store_path, entries)
    return entry


def format_entry(entry):
    tag_part = f"  [{', '.join(entry['tags'])}]" if entry["tags"] else ""
    return f"{entry['id']:>3}  {entry['text']}{tag_part}  ({entry['created']})"


def list_snippets(store_path, tag=None):
    """Return formatted lines, newest last. Optional tag filter (AC-2.1)."""
    entries = load_store(store_path)
    if tag is not None:
        entries = [entry for entry in entries if tag in entry["tags"]]
    return [format_entry(entry) for entry in entries]


def search_snippets(store_path, query):
    """Case-insensitive match against text and tags (AC-2.2)."""
    needle = query.lower()
    results = []
    for entry in load_store(store_path):
        haystack = entry["text"].lower()
        tag_hit = any(needle in tag.lower() for tag in entry["tags"])
        if needle in haystack or tag_hit:
            results.append(format_entry(entry))
    return results


def delete_snippet(store_path, snippet_id):
    """Delete by id. A missing id is reported cleanly, never ignored (AC-U.3)."""
    entries = load_store(store_path)
    kept = [entry for entry in entries if entry["id"] != snippet_id]
    if len(kept) == len(entries):
        raise SystemExit(f"snip: no snippet with id {snippet_id}.")
    save_store(store_path, kept)


def parse_tags(raw):
    if not raw:
        return []
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(prog="snip", description=__doc__)
    parser.add_argument("--store", default=str(DEFAULT_STORE), help="path to the JSON store")
    commands = parser.add_subparsers(dest="command", required=True)

    add_cmd = commands.add_parser("add", help="save one snippet")
    add_cmd.add_argument("text")
    add_cmd.add_argument("--tags", default="", help="comma-separated, e.g. python,uv")

    list_cmd = commands.add_parser("list", help="show snippets")
    list_cmd.add_argument("--tag", default=None, help="only snippets with this tag")

    search_cmd = commands.add_parser("search", help="find snippets by text or tag")
    search_cmd.add_argument("query")

    delete_cmd = commands.add_parser("delete", help="remove one snippet by id")
    delete_cmd.add_argument("id", type=int)

    args = parser.parse_args(argv)

    if args.command == "add":
        entry = add_snippet(args.store, args.text, parse_tags(args.tags))
        print(f"saved #{entry['id']}")
    elif args.command == "list":
        lines = list_snippets(args.store, tag=args.tag)
        print("\n".join(lines) if lines else "no snippets yet.")
    elif args.command == "search":
        lines = search_snippets(args.store, args.query)
        print("\n".join(lines) if lines else "no matches.")
    elif args.command == "delete":
        delete_snippet(args.store, args.id)
        print(f"deleted #{args.id}")


if __name__ == "__main__":
    main()
