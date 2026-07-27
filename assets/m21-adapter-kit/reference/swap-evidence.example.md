# Swap evidence (example, captured 2026-07-24)

What "configuration-only" looks like when it is true. Both runs execute
the same app_swap_demo.py, byte for byte. The only difference between
them is environment configuration.

## Run 1: `CWV_CONNECTION=fallback`

```
connection: fallback (a logical name; no provider in sight)
profile: adapter=mock, privacy_class=local-only
content:       [deterministic 6375d236] Received 1 message(s); the last one carries 10 word(s).
finish_reason: complete
usage:         in=10 out=11
latency_s:     0.000
request_id:    local-0001
```

## Run 2: `LAB_API_KEY=mock-key-local-only CWV_CONNECTION=primary`

```
connection: primary (a logical name; no provider in sight)
profile: adapter=lab, privacy_class=public
content:       Echo complete. Every field above came from your request.
finish_reason: complete
usage:         in=16 out=9
latency_s:     0.006
request_id:    req_e5a55adb15c4
```

## Run 3: `CWV_CONNECTION=primary` with no secret set (fails closed)

```
failed: auth: Profile 'primary' expects the secret in $LAB_API_KEY, which
is not set. The profile stores the pointer; you hold the value.
```

Three things to check in your own evidence: the application code diff
between runs is empty; every response field is canonical (no provider
shapes leaked into the output); and the failure path names the pointer,
never the value. Save yours in this format, dates and all.
