# Media input capability record (lesson 6)

One image-plus-text input, measured, with the limits that applied on the
day you tested. This record is deliberately humble: it describes ONE
connection on ONE date, because capability tables rot and other
connections differ. The last-tested date is not decoration; it is the
main field.

## The input, measured (from tools/inspect_media_input.py)

| Fact | Value |
| --- | --- |
| File | |
| Raw size (bytes) | |
| Base64 size (bytes) and inflation factor | |
| Extension claims | |
| Magic bytes say | |
| Mismatch? | |

## The connection's documented limits (from the provider's CURRENT docs)

| Fact | Value | Source page checked |
| --- | --- | --- |
| Accepted formats | | |
| Max size per image | | |
| Upload method (inline base64 / reference / either) | | |
| Cost model for image input | | |

## If you sent it (optional dated path)

| Fact | Value |
| --- | --- |
| Latency vs a text-only request | |
| The question you asked | |
| Whether the answer cited something actually visible | |
| Failure shape when you sent an oversized/wrong-format file on purpose | |

## Boundaries held

- Input understanding only: the model READ an image you owned. Nothing
  here generates images, audio, or video; that is not what this course
  builds.
- This record describes [connection name] on [date]. It transfers as a
  method, not as numbers: re-measure per connection, per date.

**Last tested:** [date]
