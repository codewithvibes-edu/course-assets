"""
Placeholder prompt function for the example eval suite. In a real
project, this would call the actual model with the actual production
prompt; here it returns a deterministic stub so the suite runs without
API keys for demo purposes.

Replace with your real prompt before treating eval results as meaningful.
"""

from __future__ import annotations

import json


def classify(input_text: str) -> str:
    """
    Stub classifier. Returns JSON matching examples/classifier.schema.json
    based on simple keyword heuristics. NOT a real classifier; just enough
    to demonstrate that the eval harness works end-to-end.

    Replace this function with a real LLM call:

        def classify(input_text: str) -> str:
            response = anthropic_client.messages.create(...)
            return response.content[0].text
    """
    text = input_text.lower()

    if any(word in text for word in ("charged", "refund", "billing", "invoice", "payment")):
        category = "billing"
        urgency = "high" if "twice" in text or "double" in text else "medium"
        action = "route_to_billing"
    elif any(word in text for word in ("down", "outage", "broken", "not working", "error")):
        category = "outage" if "down" in text and "minutes" in text else "bug"
        urgency = "critical" if "30 minutes" in text or "business hours" in text else "high"
        action = "escalate"
    elif any(word in text for word in ("add", "feature", "would be nice", "improvement", "could use")):
        category = "feature_request"
        urgency = "low"
        action = "auto_reply"
    elif any(word in text for word in ("love", "great", "thank", "appreciate")):
        category = "feedback"
        urgency = "low"
        action = "auto_reply"
    elif "checking in" in text or len(text.split()) < 8:
        category = "other"
        urgency = "low"
        action = "auto_reply"
    else:
        category = "other"
        urgency = "low"
        action = "human_review"

    return json.dumps(
        {
            "category": category,
            "urgency": urgency,
            "suggested_action": action,
            "confidence": 0.85,
            "reasoning": "Stub heuristic classifier; replace with real model call.",
        }
    )
