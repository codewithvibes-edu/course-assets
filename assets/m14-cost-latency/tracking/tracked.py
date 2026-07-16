"""
The `@tracked` decorator and `traced` context manager. Wraps an LLM
call (or any function) so a TraceSpan is created, populated, and
written automatically.

Usage:

    tracer = Tracer("traces.db")

    @tracked(tracer, agent="responder", model="claude-sonnet-4-6")
    def respond(prompt: str) -> str:
        # ... call the model ...
        return response_text

    with traced(tracer, agent="responder", model="claude-sonnet-4-6") as span:
        response = call_model(prompt)
        span.input_tokens = response.usage.input_tokens
        span.output_tokens = response.usage.output_tokens
        span.cost_cents = estimate_cost_cents(model, span.input_tokens, span.output_tokens)
"""

from __future__ import annotations

from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Iterator

from .pricing import estimate_cost_cents
from .tracer import Tracer, TraceSpan


@contextmanager
def traced(
    tracer: Tracer,
    *,
    agent: str | None = None,
    model: str | None = None,
    trace_id: str | None = None,
    parent_span_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Iterator[TraceSpan]:
    """Context-manager form. Yields the span for the caller to populate."""
    with tracer.span(
        agent=agent,
        model=model,
        trace_id=trace_id,
        parent_span_id=parent_span_id,
        metadata=metadata,
    ) as span:
        yield span


def tracked(
    tracer: Tracer,
    *,
    agent: str | None = None,
    model: str | None = None,
    extract_usage: Callable[[Any], tuple[int, int]] | None = None,
):
    """
    Decorator. Wraps a function so each call records a TraceSpan.

    extract_usage(return_value) -> (input_tokens, output_tokens) lets the
    decorator pull token counts off the wrapped function's response without
    the caller having to populate the span manually. Pass None to skip
    automatic usage extraction.
    """

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            with tracer.span(agent=agent, model=model) as span:
                result = fn(*args, **kwargs)
                if extract_usage is not None and result is not None:
                    try:
                        in_tokens, out_tokens = extract_usage(result)
                        span.input_tokens = in_tokens
                        span.output_tokens = out_tokens
                        if model:
                            span.cost_cents = estimate_cost_cents(
                                model, in_tokens, out_tokens
                            )
                    except Exception:
                        # Non-fatal: usage extraction failed; the trace
                        # row still gets written without token counts.
                        pass
                return result

        return wrapper

    return decorator
