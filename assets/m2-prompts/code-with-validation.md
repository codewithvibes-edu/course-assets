---
template: code-with-validation
version: 1.0.0
model_class: code_specialized_or_frontier
default_temperature: 0
default_max_tokens: 2000
eval_set: ./eval/code-with-validation.yaml
---

# System prompt

You are a code generator. Output a single Python code block with no
surrounding explanation. Constraints:

- Use only the standard library unless the user explicitly says otherwise.
- Include type hints on all function signatures.
- Include 3-5 unit tests using pytest.
- Code must parse, must import cleanly, and must pass its own tests when run.

If you cannot satisfy all constraints, output a single comment beginning
with `# CANNOT_COMPLY:` followed by the reason, instead of partial code.

# User turn template

```
Function signature: {{signature}}
Docstring: {{docstring}}
Additional constraints (optional): {{constraints}}
```

# Validation post-processing

Three gates that run on the output before returning to the caller:

1. **Syntax gate.** Parse with `ast.parse()`. Reject on SyntaxError.
2. **Stdlib-only gate.** Walk the AST for Import / ImportFrom nodes.
   Reject if any imported module is not in `sys.stdlib_module_names`.
3. **Runtime gate.** Write to a temp file, run with `python -m pytest`
   in a subprocess with a 30s timeout. Reject if the process exits non-zero.

On rejection, retry once with a follow-up prompt that includes the
specific failure reason. After two failures, return a deterministic
fallback (e.g., raise a ValueError to the caller, or queue for human
review depending on the calling context).

# Notes on tuning this template

- Temperature 0 because code generation rewards consistency over creativity.
  Higher temperature produces more variety but more hallucinated APIs.
- Code-specialized models (Qwen Coder, Codestral, DeepSeek Coder) often
  outperform frontier general models on this task at lower cost.
- The "stdlib-only" constraint is example-specific. Drop it if your
  use case wants third-party imports; replace it with an allowlist of
  approved third-party libraries.
- Run model-generated code in an isolated environment. Module 14 covers
  the safety patterns. A subprocess with a timeout is a minimum, not a
  maximum.
