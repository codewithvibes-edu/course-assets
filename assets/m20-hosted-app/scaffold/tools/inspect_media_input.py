"""Lesson 6 tool: inspect one image-plus-text input BEFORE any provider
sees it, and start the capability record with measured facts.

    python3 tools/inspect_media_input.py path/to/chart.png "What was the peak?"

Reads the file, measures what a request would actually carry (raw bytes
vs base64 bytes; encoding inflates size by about a third, which is why
providers publish limits), sniffs the real format from the file's magic
bytes instead of trusting the extension, and prints the JSON body shape
the request would take. Network: none. Sending it is the optional dated
path; measuring it is the required one.
"""

import base64
import json
import mimetypes
import sys
from pathlib import Path

MAGIC = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"%PDF": "application/pdf",
}


def sniff(data):
    for magic, mime in MAGIC.items():
        if data.startswith(magic):
            return mime
    return None


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    path, question = Path(argv[1]), argv[2]
    data = path.read_bytes()
    encoded = base64.b64encode(data).decode()

    claimed = mimetypes.guess_type(path.name)[0]
    actual = sniff(data)
    print(f"file:            {path.name}")
    print(f"raw size:        {len(data):,} bytes")
    print(f"base64 size:     {len(encoded):,} bytes "
          f"({len(encoded) / max(len(data), 1):.2f}x the raw size)")
    print(f"extension says:  {claimed or 'unknown'}")
    print(f"magic bytes say: {actual or 'unrecognized; check before sending'}")
    if claimed and actual and claimed != actual:
        print("MISMATCH: the extension lies. Trust the bytes; record both.")

    body = {
        "model": "<from .env>",
        "input": [
            {"type": "image", "media_type": actual or claimed or "unknown",
             "data": f"<base64, {len(encoded):,} bytes, omitted here>"},
            {"type": "text", "text": question},
        ],
    }
    print("\nrequest body shape (what a media request actually carries):")
    print(json.dumps(body, indent=2))
    print("\nNext: fill in templates/capability-record.template.md with these "
          "numbers, the provider's documented limits, and a last-tested date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
