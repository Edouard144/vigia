from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from decouple import config
from typing import TypedDict

llm = ChatAnthropic(
    model="claude-sonnet-4-5-20250929",
    api_key=config('ANTHROPIC_API_KEY')
)

class AgentState(TypedDict):
    event_source: str
    event_payload: dict
    summary: str
    needs_approval: bool
    action_plan: str

def triage_node(state: AgentState) -> AgentState:
    payload = state["event_payload"]
    source = state["event_source"]

    prompt = f"""You are a life-assistant triage agent.
Event source: {source}
Event data: {payload}

Summarize what happened in one sentence, and decide if this needs human approval
(true for anything involving money, sending messages, or scheduling; false for informational events).

Respond in this exact format:
SUMMARY: <one sentence>
NEEDS_APPROVAL: <true/false>
ACTION: <what you'd do about it>
"""
    response = llm.invoke(prompt)
    text = response.content

    summary = ""
    needs_approval = False
    action = ""

    for line in text.split("\n"):
        if line.startswith("SUMMARY:"):
            summary = line.replace("SUMMARY:", "").strip()
        elif line.startswith("NEEDS_APPROVAL:"):
            needs_approval = "true" in line.lower()
        elif line.startswith("ACTION:"):
            action = line.replace("ACTION:", "").strip()

    state["summary"] = summary
    state["needs_approval"] = needs_approval
    state["action_plan"] = action
    return state

graph = StateGraph(AgentState)
graph.add_node("triage", triage_node)
graph.set_entry_point("triage")
graph.add_edge("triage", END)

agent_graph = graph.compile()
