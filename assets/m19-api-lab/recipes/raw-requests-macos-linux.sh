# DATED RECIPE: raw requests with curl on macOS / Linux.
# Last verified: 2026-07-24 (macOS 15, curl 8.x; every line also tested
# against the lab service in this folder). curl ships preinstalled on
# macOS and nearly every Linux. If a flag misbehaves, `man curl` wins.
#
# Run the lab service first, in another terminal:
#   python3 mock_service.py
#
# These are commands to run one at a time and READ, not a script to execute.

# ---- lesson 2 and 4: one complete request, spelled out -------------------
# -s quiet, -i include response headers (read them, that is the point)
curl -s -i -X POST http://127.0.0.1:8124/v1/echo \
  -H "Authorization: Bearer mock-key-local-only" \
  -H "Content-Type: application/json" \
  -d '{"model": "mock-1", "input": "What is an API?"}'

# lesson 4, with the body you repaired in lesson 3:
curl -s -i -X POST http://127.0.0.1:8124/v1/echo \
  -H "Authorization: Bearer mock-key-local-only" \
  -H "Content-Type: application/json" \
  --data @fixtures/malformed/repaired.json

# lesson 4, credential discipline: the key comes from the environment,
# never typed inline once you are past the mock. Put it in .env or export
# it; the command then never contains the value.
#   export LAB_KEY=mock-key-local-only
curl -s -i -X POST http://127.0.0.1:8124/v1/echo \
  -H "Authorization: Bearer $LAB_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": "key came from the environment"}'

# ---- lesson 5: walk the exhibits -----------------------------------------
for kind in bad-input auth forbidden missing rate-limit server; do
  echo "== $kind =="
  curl -s -i "http://127.0.0.1:8124/v1/error/$kind"
  echo
done

# ---- lesson 6: streaming ---------------------------------------------------
# -N disables buffering so events print as they ARRIVE. Watch the pacing.
# Press Ctrl+C mid-stream once, on purpose: that is the cancel exercise.
curl -sN -X POST http://127.0.0.1:8124/v1/stream \
  -H "Authorization: Bearer mock-key-local-only"

# ---- lesson 6: force a timeout --------------------------------------------
# The endpoint takes 8 seconds. Your budget is 2. Note the exit code:
# 28 is curl's spelling of "I gave up waiting", and $? is where exit
# codes live (Module 0 taught you that).
curl -s --max-time 2 -X POST http://127.0.0.1:8124/v1/slow \
  -H "Authorization: Bearer mock-key-local-only"
echo "exit code: $?"

# ---- lesson 6: save the raw evidence ---------------------------------------
# -D saves response headers (request ID lives there), -o saves the body,
# -w prints timing. Three files of evidence from one request.
curl -s -X POST http://127.0.0.1:8124/v1/echo \
  -H "Authorization: Bearer mock-key-local-only" \
  -H "Content-Type: application/json" \
  -d '{"model": "mock-1", "input": "save this one"}' \
  -D response-headers.txt -o response-body.json \
  -w "total time: %{time_total}s\n"
