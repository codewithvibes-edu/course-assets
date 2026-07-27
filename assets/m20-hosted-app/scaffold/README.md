# Hosted app scaffold

The supplied starting point for Module 20, so setup does not eat the
module. Standard library only. Defaults point at the Module 19 lab
service, so everything runs free and local until YOU decide otherwise.

## Layout, and why each thing is separate

```
scaffold/
├── README.md            # documentation: how to run, test, and stop
├── .env.example         # environment: values that change per machine/provider
├── .gitignore           # the boundary: .env and logs/ never enter git
├── src/
│   ├── app.py           # the application: display, cancel, budgets, logging
│   ├── client.py        # THE ONLY FILE THAT TALKS TO THE PROVIDER
│   ├── state.py         # bounded history; the API remembers nothing
│   └── usage_log.py     # facts about requests; never their content
├── fixtures/            # sample data: deterministic input + one malformed event
├── tests/               # contract tests; every failure is a free test double
├── tools/
│   └── inspect_media_input.py   # lesson 6: measure before you send
└── logs/                # gitignored; usage.jsonl lands here
```

Lesson 2 asks you to explain this separation in your own words. The short
version: source is code anyone can read, configuration is values that
change per machine, secrets are configuration that must never be seen,
fixtures are inputs that never change, tests are promises being checked,
and logs are facts being kept. When each has its own home, "where does
this go?" always has an answer, and .gitignore only has to guard two doors.

## Run it

```sh
cp .env.example .env           # then read it; the defaults are the mock
python3 src/app.py summarize fixtures/sample-input.txt
python3 src/app.py chat        # watch the state bound do its job
```

Start the Module 19 lab service first (its folder, `python3
mock_service.py`). The summarize command streams as events arrive; Ctrl+C
mid-stream is a supported move, not a crash, and gets logged as canceled.

## Test it

```sh
python3 -m unittest discover -s tests -v
```

Eight tests, zero network: invalid credential, rate limit with
Retry-After, timeout, malformed event, a stream that dies before its done
event, the happy path, the state bound, and the log-privacy check. They
are free because client.py exposes an opener seam the doubles plug into.
That seam is a design choice you now get to keep making on purpose.

## Stop it

Both commands are run-and-exit (chat exits on `quit` or Ctrl+C). The lab
service stops with Ctrl+C in its own terminal.
