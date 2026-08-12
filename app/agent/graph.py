from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import (
    extract_ingredients,
    normalize_ingredients,
    kb_lookup,
    reason_unmatched,
    synthesize_report,
)


def needs_reasoning(state: AgentState) -> str:
    """The one real branching decision in the whole agent."""
    return "reason" if state["unmatched"] else "skip"


graph = StateGraph(AgentState)

graph.add_node("extract", extract_ingredients)
graph.add_node("normalize", normalize_ingredients)
graph.add_node("kb_lookup", kb_lookup)
graph.add_node("reason", reason_unmatched)
graph.add_node("synthesize", synthesize_report)

graph.set_entry_point("extract")
graph.add_edge("extract", "normalize")
graph.add_edge("normalize", "kb_lookup")

graph.add_conditional_edges(
    "kb_lookup",
    needs_reasoning,
    {"reason": "reason", "skip": "synthesize"},
)
graph.add_edge("reason", "synthesize")
graph.add_edge("synthesize", END)

agent = graph.compile()