"""
LangGraph wiring of the multi-agent support system.

State shape: agents.state.SupportState (TypedDict)
Nodes: supervisor + 4 specialists (billing, technical, escalation, general)
Edges: supervisor -> conditional based on classification -> specialist -> END

LangGraph's API has shifted across versions. This implementation works
against the version pinned in requirements.txt. If the import shape
changes upstream, update here; the node functions below are
framework-agnostic and would work in CrewAI, AutoGen, or raw Python
with minor wrapper changes.
"""

from __future__ import annotations

from agents import (
    SupportState,
    billing_specialist,
    classify_and_route,
    escalation_specialist,
    general_specialist,
    route_after_supervisor,
    technical_specialist,
)


def build_graph():
    """
    Compile the LangGraph state machine. Imported lazily so test files
    that exercise the node functions in isolation do not need LangGraph
    installed.
    """
    from langgraph.graph import StateGraph, END

    graph = StateGraph(SupportState)

    graph.add_node("supervisor", classify_and_route)
    graph.add_node("billing_specialist", billing_specialist)
    graph.add_node("technical_specialist", technical_specialist)
    graph.add_node("escalation_specialist", escalation_specialist)
    graph.add_node("general_specialist", general_specialist)

    graph.set_entry_point("supervisor")
    graph.add_conditional_edges("supervisor", route_after_supervisor)

    for specialist in (
        "billing_specialist",
        "technical_specialist",
        "escalation_specialist",
        "general_specialist",
    ):
        graph.add_edge(specialist, END)

    return graph.compile()


def run(user_input: str, customer_email: str | None = None) -> SupportState:
    """Entry point: invoke the compiled graph against a single ticket."""
    app = build_graph()
    initial: SupportState = {
        "user_input": user_input,
        "customer_email": customer_email,
        "trace": [],
    }
    return app.invoke(initial)
