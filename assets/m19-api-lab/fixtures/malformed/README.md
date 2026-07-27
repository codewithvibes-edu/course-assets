# Five broken bodies (lesson 3)

Each file LOOKS like JSON and fails a parser, each for a different disease.
Repair all five by hand in your editor, then prove each repair:

    python3 -c "import json; json.load(open('01-missing-comma.json')); print('valid')"

Do not guess at validity by eyeballing. The parser is the judge; that is
the entire lesson. When all five pass, build the final nested body
described in target-body.md, validate it the same way, and save it as
repaired.json. Compare with repaired.example.json only after yours parses.
