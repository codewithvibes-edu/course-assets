# Adapter authoring guide

How to add connection number three, next month, in under an hour,
without asking anyone's permission but the contract suite's.

## The steps, in order

1. **Probe first.** Run the capability probes against the new connection
   and fill in a coupling-inventory capability table with dates. You are
   about to DECLARE these; measure before you declare.
2. **Copy the closest adapter.** `adapter_lab.py` for anything HTTP,
   `adapter_mock.py` for anything local or deterministic. The protocol is
   four methods: capabilities, test, generate, stream (stream only if you
   measured streaming).
3. **Write the translation, both directions.** Canonical request in,
   provider shape out; provider response in, canonical shape out. Field
   by field. The temptation to "just pass through" one convenient
   provider object is the fence hole; do not cut it.
4. **Normalize every failure you met in the probe** into the nine
   categories, keeping raw context in raw_debug, redacted. If the
   provider has a failure shape the categories cannot hold, that is a
   design conversation, not a tenth category you add quietly.
5. **Declare capabilities truthfully, with the probe date.** An absent
   feature raises `unsupported` at call time; it does not return None and
   hope.
6. **Register it**: one entry in `ADAPTERS`, one connection profile with
   a secret POINTER (a name, never a value), a privacy class, and the
   capabilities note.
7. **Run the contract suite.** Every applicable test, green, before any
   route may select the new connection. A red suite means the adapter is
   still a draft, whatever the demo looked like.
8. **Produce swap evidence**: the same application run, old connection
   and new, configuration change only, saved side by side with dates.

## The three rules that outlive this file

1. Provider types never cross the boundary.
2. Normalization keeps evidence (redacted), never erases it.
3. Capabilities are measured, declared, dated, and enforced; eligibility
   is the suite passing, nothing softer.
