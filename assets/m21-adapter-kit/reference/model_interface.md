# model_interface.md: the canonical contract

The application speaks these types and no others. Provider shapes stop at
the adapter boundary, in both directions. This file is the contract's
prose; `src/canonical.py` is the same contract, compilable.

## The types

| Type | Fields | The rule that shaped it |
| --- | --- | --- |
| CanonicalRequest | messages, media (refs only), max_output_tokens, timeout_s | Only fields THIS application uses. A canonical type that mirrors one provider's API is that provider's API with a fake mustache. |
| CanonicalResponse | content, finish_reason, usage, latency_s, request_id, raw_debug | finish_reason is one of complete / length / canceled. raw_debug is redacted evidence, never secrets. |
| StreamEvent | kind (delta / usage / done / canceled / error), text, usage, request_id | The UI imports THESE names. No provider event name ever reaches the display layer. |
| Usage | input_tokens, output_tokens | Units normalized by the adapter, whatever the provider calls them. |
| Capabilities | text, streaming, structured_output, tools, image_input, last_tested | Declared and dated. An absent feature is a stated fact, not a nullable surprise. |
| AdapterError | category, retry_after, request_id, raw_debug | Nine categories: auth, rate_limit, bad_input, not_found, server, timeout, network, malformed, unsupported. The category carries the decision. |

## The adapter protocol

Every adapter implements:

| Method | Contract |
| --- | --- |
| `capabilities()` | Truthful, dated declaration. The suite checks declared streaming actually streams and declared absences actually refuse. |
| `test()` | One cheap call proving address + credential together. |
| `generate(request)` | CanonicalRequest in, CanonicalResponse out, AdapterError on every failure shape. |
| `stream(request)` | Only where capabilities.streaming is true. Typed events, done event carries usage and request ID, GeneratorExit (cancellation) closes cleanly. A stream that ends without done raises malformed, never returns a short success. |

## The two boundary rules

1. Provider request/response types never cross the boundary. If the
   application can name the provider's event or error type, the fence has
   a hole.
2. Normalization preserves evidence. Mapping a provider error to a
   category must not erase the raw context a human needs later; it goes
   in raw_debug, redacted of every secret, truncated, kept.

## Eligibility

An adapter that passes `tests/test_adapter_contract.py` is eligible for
selection through a connection profile. An adapter that does not pass is
not an adapter yet; it is a draft. There is no partially-eligible state,
which is exactly what makes routing (m3) and the local lane (m23/m24)
safe to build on this seam.
