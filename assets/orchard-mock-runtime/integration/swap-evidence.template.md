# Swap evidence: local mock runtime

Fill in every bracket, then save this file with your module evidence.
Your saved copy is the acceptance record for m24-3: same application,
different runtime, zero application-code changes.

Capture date: [YYYY-MM-DD]
Captured by: [your name]

## The claim being proven

The application selected a LOGICAL connection. It never learned which
runtime answered. Swapping runtimes was a configuration change, and this
file holds the bytes that prove it.

## Run 1: the connection you already had

Command: `CWV_CONNECTION=[your existing logical id] python3 app_swap_demo.py`

```
[paste the full output]
```

## Run 2: the local mock connection

Command: `CWV_CONNECTION=local_mock python3 app_swap_demo.py`

(or `python3 integration/swap_proof.py`, which performs the registry
merge for you against the shipped m21 kit and saves its own capture)

```
[paste the full output]
```

## Checksums

| Record | Value |
| --- | --- |
| Connection profile | [paste the local_mock profile JSON, or its path] |
| Adapter ID | local |
| Contract suite file | test_adapter_contract.py sha256=[checksum] |
| Application file | app_swap_demo.py sha256=[checksum, same for both runs] |

Compute a checksum with: `python3 -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" app_swap_demo.py`

## Application-code diff between the runs

```
[paste the diff; the acceptance condition is that it is EMPTY]
```

## Canonical response check

Confirm each field of Run 2's response is canonical, with no provider
shape leaked through the boundary:

- [ ] content starts with `[COURSE MOCK, NOT MODEL OUTPUT]`
- [ ] finish_reason is one of complete, length, canceled
- [ ] usage has input_tokens and output_tokens (whitespace words, not a tokenizer result)
- [ ] request_id is present
- [ ] no field in the output names a provider, a vendor, or an HTTP shape

## Route class

This route is recorded as: `exercise-only mock route`

It proves the operations. It says nothing about any model, quant,
runtime, or machine, and it may not be recommended for real work.
