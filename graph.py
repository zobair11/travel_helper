from langgraph.graph import StateGraph, END
from state import TravelState
from config import REQUIRED_FIELDS
from nodes import (
    start_or_prompt,
    input_agent_node,
    wait_for_user_node,
    map_user_answer_node,
    validator_node,
)


graph = StateGraph(TravelState)

graph.add_node("start", start_or_prompt)
graph.add_node("input_agent", input_agent_node)
graph.add_node("wait_user", wait_for_user_node)
graph.add_node("map_answer", map_user_answer_node)
graph.add_node("validator", validator_node)

graph.set_entry_point("start")
graph.add_edge("start", "input_agent")
graph.add_edge("input_agent", "validator")


def validator_router(state: TravelState):
    all_present = all(state.get(k) for k in REQUIRED_FIELDS)
    needs_more = state.get("ask") is not None
    has_errors = bool(state.get("errors"))

    if (not has_errors) and (not needs_more) and all_present:
        return END
    if needs_more:
        return "wait_user"
    return "input_agent"


graph.add_conditional_edges(
    "validator",
    validator_router,
    {
        "wait_user": "wait_user",
        "input_agent": "input_agent",
        END: END
    }
)

graph.add_edge("wait_user", "map_answer")
graph.add_edge("map_answer", "validator")


app = graph.compile()
