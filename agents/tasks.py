import logging
from celery import shared_task
from .models import Event, AgentTask, ApprovalRequest
from .graph import agent_graph

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_event(self, event_id):
    try:
        event = Event.objects.get(id=event_id)

        task = AgentTask.objects.create(
            event=event,
            agent_name="triage_agent",
            status="running",
            input_data=event.payload
        )

        try:
            result_state = agent_graph.invoke({
                "event_source": event.source,
                "event_payload": event.payload,
                "summary": "",
                "needs_approval": False,
                "action_plan": ""
            })
        except Exception as ai_error:
            logger.error(f"AI agent failed for event {event_id}: {ai_error}")
            task.status = "failed"
            task.error = str(ai_error)
            task.save()
            raise self.retry(exc=ai_error)

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

        logger.info(f"Event {event_id} processed successfully")
        return result_state

    except Event.DoesNotExist:
        logger.error(f"Event {event_id} not found")
        return {"error": "event not found"}
