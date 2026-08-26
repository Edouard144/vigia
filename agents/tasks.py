from celery import shared_task
from .models import Event, AgentTask, ApprovalRequest

@shared_task
def process_event(event_id):
    event = Event.objects.get(id=event_id)

    task = AgentTask.objects.create(
        event=event,
        agent_name="triage_agent",
        status="running",
        input_data=event.payload
    )

    needs_approval = event.payload.get("needs_approval", False)

    if needs_approval:
        task.status = "waiting_approval"
        task.save()

        ApprovalRequest.objects.create(
            task=task,
            message=f"Approve action for event: {event.source} - {event.payload.get('title', 'Untitled')}"
        )

        event.processed = True
        event.save()
        return {"status": "waiting_approval"}

    result = {"summary": f"Processed event from {event.source}"}
    task.status = "completed"
    task.output_data = result
    task.save()

    event.processed = True
    event.save()

    return result
