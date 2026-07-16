---
template: structured-output-classifier
version: 1.0.0
model_class: small_or_mid # 7B-30B is sufficient for classification
default_temperature: 0
default_max_tokens: 300
eval_set: ./eval/structured-output-classifier.yaml
---

# System prompt

You are a structured-output classifier. Read the input, identify the relevant
features, and output JSON matching the provided schema. Be conservative on
uncertainty: if the answer is unclear, mark `confidence` low and `category`
as `unknown`.

# Schema

```json
{
  "type": "object",
  "required": ["category", "urgency", "confidence", "reasoning"],
  "properties": {
    "category": {
      "type": "string",
      "enum": ["{{category_1}}", "{{category_2}}", "{{category_3}}", "unknown"]
    },
    "urgency": {
      "type": "string",
      "enum": ["low", "medium", "high", "critical"]
    },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "reasoning": { "type": "string", "maxLength": 200 }
  }
}
```

# Few-shot examples

```
Input: {{example_input_1}}
Output: {{example_output_1}}

Input: {{example_input_2}}
Output: {{example_output_2}}

Input: {{example_input_3}}
Output: {{example_output_3}}
```

# User turn template

```
Input: {{actual_input}}
Output:
```

# Validation post-processing

After receiving the response, parse as JSON. If it fails to parse, retry
once with a "Your previous response was invalid JSON. Try again." prompt.
After two failures, return a deterministic fallback that flags the case
for human review.

# Notes on tuning this template

- The category enum is the entire instruction surface. Tighten or relax it
  carefully; adding `"other"` as a permanent escape hatch reduces the chance
  the model invents new categories.
- Temperature 0 is correct for classification. Resist the urge to bump it.
- 3-5 few-shot examples are usually enough. Beyond that, the marginal lift
  on accuracy is smaller than the cost increase from longer prompts.
