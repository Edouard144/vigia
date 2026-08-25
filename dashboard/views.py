from rest_framework import viewsets, permissions
from agents.models import Event, AgentTask, ApprovalRequest
from agents.tasks import process_event
from .serializers import EventSerializer, AgentTaskSerializer, ApprovalRequestSerializer

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        event = serializer.save(user=self.request.user)
        process_event.delay(str(event.id))

class AgentTaskViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgentTask.objects.all()
    serializer_class = AgentTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

class ApprovalRequestViewSet(viewsets.ModelViewSet):
    queryset = ApprovalRequest.objects.all()
    serializer_class = ApprovalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
