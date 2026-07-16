---
template: structured-extractor
version: 1.0.0
model_class: small_or_mid
default_temperature: 0
default_max_tokens: 800
eval_set: ./eval/structured-extractor.yaml
---

# System prompt

You extract structured fields from unstructured text. Read the input,
identify the requested fields, output JSON matching the schema. If a
field cannot be determined from the input, use the literal value `null`.
Do not hallucinate values.

# Schema

The schema is supplied per call. Generic shape:

```json
{
  "type": "object",
  "required": ["{{required_fields_list}}"],
  "properties": {
    "{{field_name}}": {
      "type": "string|number|boolean|null",
      "description": "{{when this field should be filled}}"
    }
  }
}
```

# Few-shot examples (replace with your domain examples)

Receipt extraction:

```
Input: "Receipt from Coffee Shop, 2026-04-15. Total $4.50 paid by card ending 4242."
Output: {
  "merchant": "Coffee Shop",
  "date": "2026-04-15",
  "total": 4.50,
  "currency": "USD",
  "payment_method": "card",
  "card_last_four": "4242"
}
```

Email metadata extraction:

```
Input: "From: Alice <alice@example.com>\nTo: Bob <bob@example.com>\nSubject: Q3 review\nDate: 2026-05-01\n\nHi Bob, ..."
Output: {
  "from_name": "Alice",
  "from_email": "alice@example.com",
  "to_name": "Bob",
  "to_email": "bob@example.com",
  "subject": "Q3 review",
  "date": "2026-05-01"
}
```

Invoice extraction:

```
Input: "Invoice #INV-2026-1234 issued 2026-04-01 by ACME Corp. Due 2026-04-30. Subtotal $1,500.00. Tax $120.00. Total $1,620.00."
Output: {
  "invoice_number": "INV-2026-1234",
  "issuer": "ACME Corp",
  "issued_date": "2026-04-01",
  "due_date": "2026-04-30",
  "subtotal": 1500.00,
  "tax": 120.00,
  "total": 1620.00,
  "currency": "USD"
}
```

# User turn template

```
Schema: {{schema_json}}
Input: {{actual_text}}
Output:
```

# Validation post-processing

1. Parse the output as JSON. On parse failure, retry once with the
   parse error in the prompt. After two failures, mark for human review.
2. Validate against the schema using a JSON Schema validator (jsonschema
   in Python, ajv in Node). Reject on validation error.
3. Type-check field values. The model sometimes returns "5.0" as a string
   when the schema expects a number. Coerce or reject per your policy.
4. Confidence flag: if any field is `null`, surface that in the calling
   context so downstream code can decide whether to escalate.

# Notes on tuning this template

- Temperature 0 because extraction is a deterministic task by definition.
- Few-shot examples carry most of the instruction work. Three examples in
  the same domain as the actual input reliably outperforms abstract
  schema descriptions alone.
- Use a small model. Frontier reasoning is overkill for extraction; a
  7-30B parameter model handles structured output well at much lower cost.
- Real production extractors should log the input + output to traces
  (Module 12) so you can sample for human review and find systematic
  errors over time.
