# Module 21: Provider adapter kit

The reference implementation of the course's architectural hinge: one
canonical boundary, two adapters behind it, one contract suite that
decides eligibility, and a swap you prove with configuration alone.

## What's in here

```
m21-adapter-kit/
├── README.md
├── reference/                        # complete, working, tested
│   ├── model_interface.md            # the contract in prose
│   ├── app_swap_demo.py              # the swap proof (run it both ways)
│   ├── swap-evidence.example.md      # what passing evidence looks like
│   ├── src/
│   │   ├── canonical.py              # the only types the app may see
│   │   ├── adapter_lab.py            # HTTP adapter (the m19 lab protocol)
│   │   ├── adapter_mock.py           # deterministic adapter, no network
│   │   ├── registry.py               # logical IDs, profiles, capability gate
│   │   └── profiles.json             # metadata + secret POINTERS, committable
│   └── tests/
│       └── test_adapter_contract.py  # THE suite; 13 tests, fully offline
└── templates/
    ├── coupling-inventory.template.md
    ├── connection-threat-model.template.md
    └── adapter-authoring-guide.md
```

## Run it

```sh
cd reference

# the contract suite: offline, milliseconds, both adapters
python3 -m unittest discover -s tests -v

# the swap proof (start the Module 19 lab service for the second run)
CWV_CONNECTION=fallback python3 app_swap_demo.py
LAB_API_KEY=mock-key-local-only CWV_CONNECTION=primary python3 app_swap_demo.py
```

## How the module uses it

Lessons 1 and 2 you do against YOUR Module 20 application: inventory the
coupling, then define canonical types for what your app actually uses
(this reference is a worked answer, not a handout to skip the thinking).
Lessons 3 through 6 refactor your app behind the boundary, add the
deterministic second connection, normalize everything, and split
metadata from secrets. Lesson 7 is the suite and the swap evidence.
Bundle your version as Provider_Adapter_Kit.zip. The reference stays
useful afterward as the authoring guide's companion when connection
number three shows up.
