from celery import shared_task
from .models import Event, AgentTask

@shared_task
def process_event(event_id):
    event = Event.objects.get(id=event_id)

    task = AgentTask.objects.create(
        event=event,
        agent_name="triage_agent",
        status="running",
        input_data=event.payload
    )

    result = {"summary": f"Processed event from {event.source}"}

    task.status = "completed"
    task.output_data = result
    task.save()

    event.processed = True
    event.save()

    return result
