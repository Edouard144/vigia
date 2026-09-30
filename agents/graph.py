import json
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from decouple import config
from typing import TypedDict

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=config('GROQ_API_KEY')
)

class AgentState(TypedDict):
    event_source: str
    event_payload: dict
    summary: str
    needs_approval: bool
    action_plan: str
    title: str
    intent: str
    recipient: str
    channel: str
    risk: str
    confidence: float
    expires_in_minutes: int
    reasoning: list
    draft: str
    side_effects: list

VALID_CHANNELS = {"gmail", "calendar", "slack", "banking", "contacts"}
VALID_RISKS = {"low", "medium", "high"}

SOURCE_TO_CHANNEL = {
    "gmail": "gmail",
    "calendar": "calendar",
    "slack": "slack",
    "banking": "banking",
    "contacts": "contacts",
}

def _coerce_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def _coerce_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _coerce_str_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value)]

def triage_node(state: AgentState) -> AgentState:
    payload = state["event_payload"]
    source = state["event_source"]

    prompt = f"""You are a life-assistant triage agent.
Event source: {source}
Event data: {payload}

Summarize what happened, decide if this needs human approval
(true for anything involving money, sending messages, or scheduling; false for informational events),
and describe the proposed action in detail.

Respond with ONLY a JSON object, no prose, using exactly these keys:
{{
  "summary": "<one sentence>",
  "needs_approval": true|false,
  "action_plan": "<what you'd do about it>",
  "title": "<short action title, max 80 chars>",
  "intent": "<what the user ultimately wants>",
  "recipient": "<person or address involved, empty string if none>",
  "channel": "gmail|calendar|slack|banking|contacts",
  "risk": "low|medium|high",
  "confidence": 0.0-1.0,
  "expires_in_minutes": <int or null>,
  "reasoning": ["<short bullet of why approval is needed>"],
  "draft": "<the exact message or action content you would send/execute>",
  "side_effects": ["<concrete consequence of approving>"]
}}
"""
    response = llm.invoke(prompt)
    text = response.content

    parsed = {}
    if "{" in text and "}" in text:
        candidate = text[text.index("{"):text.rindex("}") + 1]
        try:
            loaded = json.loads(candidate)
            if isinstance(loaded, dict):
                parsed = loaded
        except json.JSONDecodeError:
            parsed = {}

    if not parsed:
        for line in text.split("\n"):
            if line.startswith("SUMMARY:"):
                parsed["summary"] = line.replace("SUMMARY:", "").strip()
            elif line.startswith("NEEDS_APPROVAL:"):
                parsed["needs_approval"] = "true" in line.lower()
            elif line.startswith("ACTION:"):
                parsed["action_plan"] = line.replace("ACTION:", "").strip()

    summary = str(parsed.get("summary") or "").strip()
    action = str(parsed.get("action_plan") or "").strip()
    needs_approval = bool(parsed.get("needs_approval", False))

    channel = str(parsed.get("channel") or "").strip().lower()
    if channel not in VALID_CHANNELS:
        channel = SOURCE_TO_CHANNEL.get(str(source).strip().lower(), "")

    risk = str(parsed.get("risk") or "").strip().lower()
    if risk not in VALID_RISKS:
        risk = "medium"

    confidence = min(max(_coerce_float(parsed.get("confidence"), 0.0), 0.0), 1.0)

    state["summary"] = summary
    state["needs_approval"] = needs_approval
    state["action_plan"] = action
    state["title"] = str(parsed.get("title") or summary or "Proposed action")[:255]
    state["intent"] = str(parsed.get("intent") or "").strip()
    state["recipient"] = str(parsed.get("recipient") or "").strip()[:255]
    state["channel"] = channel
    state["risk"] = risk
    state["confidence"] = confidence
    state["expires_in_minutes"] = _coerce_int(parsed.get("expires_in_minutes"))
    state["reasoning"] = _coerce_str_list(parsed.get("reasoning"))
    state["draft"] = str(parsed.get("draft") or "").strip()
    state["side_effects"] = _coerce_str_list(parsed.get("side_effects"))
    return state

graph = StateGraph(AgentState)
graph.add_node("triage", triage_node)
graph.set_entry_point("triage")
graph.add_edge("triage", END)

agent_graph = graph.compile()
