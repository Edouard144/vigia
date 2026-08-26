from celery import shared_task
from .models import Event, AgentTask, ApprovalRequest
from .graph import agent_graph

@shared_task
def process_event(event_id):
    event = Event.objects.get(id=event_id)

    task = AgentTask.objects.create(
        event=event,
        agent_name="triage_agent",
        status="running",
        input_data=event.payload
    )

    result_state = agent_graph.invoke({
        "event_source": event.source,
        "event_payload": event.payload,
        "summary": "",
        "needs_approval": False,
        "action_plan": ""
    })

    if result_state["needs_approval"]:
        task.status = "waiting_approval"
        task.output_data = result_state
        task.save()

        ApprovalRequest.objects.create(
            task=task,
            message=f"{result_state['summary']} — Proposed action: {result_state['action_plan']}"
        )
    else:
        task.status = "completed"
        task.output_data = result_state
        task.save()

    event.processed = True
    event.save()

    return result_state
