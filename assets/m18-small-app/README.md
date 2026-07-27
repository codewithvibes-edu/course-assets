# Module 18: Small app build kit

Everything the module hands you, in one folder. Nothing here uploads anywhere;
every artifact you produce stays on your machine.

## What's in here

```
m18-small-app/
├── README.md                          # this file
├── problem-cards.md                   # three proven starter app choices
├── templates/
│   ├── requirements.template.md       # lesson 2: three stories + ugly case
│   ├── architecture.template.md       # lesson 3: two designs, one winner
│   ├── plan.template.md               # lesson 4: stages, assumptions, retreat rule
│   ├── test-map.template.md           # lesson 5: criterion -> evidence
│   ├── dependency-review.template.md  # lesson 6: five questions per dependency
│   ├── readme.template.md             # lesson 7: the stranger-proof README
│   └── release-card.template.md       # lesson 7: known-good state, on paper
├── sample-app/                        # a finished worked example ("snip")
│   ├── README.md
│   ├── problem.md                     # the sample's own module artifacts,
│   ├── requirements.md                #   so you can see the arc end to end
│   ├── test-map.md
│   ├── snippets.py                    # the app: stdlib only, one file
│   └── tests/test_snippets.py
└── exercises/
    ├── prepared-defect-briefing.md    # lesson 5 drill: read this first
    ├── prepared-defect.patch
    ├── risky-diff-briefing.md         # lesson 6 drill: read this first
    ├── risky-diff.patch               # REVIEW ONLY. Never apply this one.
    └── answers/
        ├── prepared-defect.answer.md
        └── risky-diff.answer.md
```

## How the pieces map to the lessons

Lesson 1 sends you to `problem-cards.md` (or your own idea, same rules).
Lessons 2 through 7 each have a template in `templates/`; copy it into YOUR
app repo and fill it in. The sample app is there to read, so you can see what
a finished, small, honest version of every artifact looks like. It is a
snippet keeper on purpose, a different job from all three problem cards, so
there is nothing to copy-paste into your own build.

The two exercises run against the sample app, never against your build.
Each briefing file tells you exactly what to run and when to open the answer
key. Do the drill before the answer. Missing something in a drill is the
cheapest tuition you will ever pay.

## Sample app quick start

```sh
cd sample-app
python3 snippets.py add "uv run python file.py" --tags python,uv
python3 snippets.py list
python3 -m unittest discover -s tests -v
```

Python 3.10+ and the standard library. No installs, no network, no keys.
