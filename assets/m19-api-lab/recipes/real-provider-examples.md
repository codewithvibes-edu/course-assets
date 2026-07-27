# DATED RECIPES: the same anatomy against two real providers

Last verified: 2026-07-24. OPTIONAL. The required path for this module is
the lab service; these exist to prove the anatomy transfers, using two
current hosted providers as examples. Neither is a recommendation; they
are simply two services this recipe was tested against, and the anatomy
below transfers to any provider with an HTTP API. Both cost real (small)
money and need your own key, handled with the .env discipline from Module
0: the key lives in the environment, never in the command text, never in
your history, never in a screenshot.

If anything below disagrees with the provider's current docs, the docs
win. That sentence is on every dated recipe in this course because it
keeps being true.

## Example A: Anthropic

Setup facts (account, prepaid billing, key creation) live in the Module 0
starter repo's `recipes/anthropic.py` and have not changed shape: console
at platform.claude.com, prepaid credits, key shown once. Model name below
was current at verification; if the response says not_found, swap in a
current ID from the provider's model list.

```sh
# key already in the environment, e.g. loaded from .env:
#   export ANTHROPIC_KEY=sk-ant-...
curl -s -i -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-5",
    "max_tokens": 200,
    "messages": [{"role": "user", "content": "In one sentence, what is an API?"}]
  }'
```

Sort it with the lesson-2 buckets: `POST`, `Host`, `Content-Type` are
protocol. The endpoint `/v1/messages`, the auth header being NAMED
`x-api-key`, the extra `anthropic-version` header, and the required
`max_tokens` field are service-specific. The model ID and your message
are your choice. Nothing here is a new concept; every line sorts.

## Example B: OpenAI

Setup facts live in the starter repo's `recipes/openai.py`: console at
platform.openai.com, billing plus usage limit, key shown once. Copy a
current model ID from the provider's model list into the environment.

```sh
#   export OPENAI_KEY=sk-...
#   export OPENAI_MODEL=<current model ID from the provider's list>
curl -s -i -X POST https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'"$OPENAI_MODEL"'",
    "messages": [{"role": "user", "content": "In one sentence, what is an API?"}]
  }'
```

Same buckets: the endpoint `/v1/chat/completions` and the field names are
service-specific; the auth header here is `Authorization: Bearer`, the
exact pattern the lab service uses. Two providers, two spellings of the
same request. Holding both in view at once is the best argument you will
ever see for Module 21's adapter.

## Compare the failure surfaces too

With a deliberately wrong key, both providers return a 401 with a
structured error body and a request ID header, exactly the shape you
drilled on the exhibits. Reading a real provider's 401 and finding it
boring is this module working as intended.
