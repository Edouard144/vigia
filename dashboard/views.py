from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from agents.models import Event, AgentTask, ApprovalRequest
from agents.tasks import process_event
from .serializers import EventSerializer, AgentTaskSerializer, ApprovalRequestSerializer

class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        event = serializer.save(user=self.request.user)
        process_event.delay(str(event.id))

class AgentTaskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AgentTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AgentTask.objects.filter(event__user=self.request.user)

class ApprovalRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ApprovalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ApprovalRequest.objects.filter(task__event__user=self.request.user)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        approval = self.get_object()
        approved = request.data.get('approved')

        if approved is None:
            return Response({"error": "approved field is required"}, status=400)

        approval.approved = approved
        approval.responded_at = timezone.now()
        approval.save()

        task = approval.task
        task.status = 'completed' if approved else 'failed'
        task.output_data = {**task.output_data, "approved": approved}
        task.save()

        return Response({"status": "approved" if approved else "rejected"})
