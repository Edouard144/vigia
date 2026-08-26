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

    if event.payload.get("needs_approval"):
        task.status = "waiting_approval"
        task.save()
        ApprovalRequest.objects.create(
            task=task,
            message=f"Approve processing of event from {event.source}?"
        )
        return {"status": "waiting_approval", "task_id": str(task.id)}

    result = {"summary": f"Processed event from {event.source}"}

    task.status = "completed"
    task.output_data = result
    task.save()

    event.processed = True
    event.save()

    return result
