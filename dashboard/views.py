from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from agents.models import Event, AgentTask, ApprovalRequest
from agents.tasks import process_event
from .serializers import (
    EventSerializer,
    AgentTaskSerializer,
    ApprovalRequestSerializer,
    ApprovalRespondSerializer,
)


def _as_bool(value):
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['source', 'event_type']
    ordering_fields = ['created_at', 'updated_at']

    def get_queryset(self):
        return Event.objects.filter(user=self.request.user).prefetch_related(
            'tasks__approvals'
        ).order_by('-created_at')

    def perform_create(self, serializer):
        event = serializer.save(user=self.request.user)
        process_event.delay(str(event.id))


class AgentTaskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AgentTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AgentTask.objects.filter(event__user=self.request.user).order_by('-created_at')


class ApprovalRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ApprovalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'intent', 'recipient', 'message', 'draft']
    ordering_fields = ['created_at', 'responded_at', 'risk']

    def get_queryset(self):
        queryset = ApprovalRequest.objects.filter(
            task__event__user=self.request.user
        ).select_related('task').order_by('-created_at')

        pending = self.request.query_params.get('pending')
        if pending is not None:
            if _as_bool(pending):
                return queryset.filter(approved__isnull=True)
            return queryset.filter(approved__isnull=False)

        status = self.request.query_params.get('status')
        if status == 'pending':
            return queryset.filter(approved__isnull=True)
        if status == 'approved':
            return queryset.filter(approved=True)
        if status == 'declined':
            return queryset.filter(approved=False)

        return queryset

    @extend_schema(
        request=ApprovalRespondSerializer,
        responses={200: ApprovalRequestSerializer, 400: None, 409: None},
        summary='Approve or decline an approval request',
    )
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        approval = self.get_object()

        serializer = ApprovalRespondSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved = serializer.validated_data['approved']
        note = serializer.validated_data.get('message') or ''

        if approval.approved is not None:
            return Response(
                {"error": "already responded", "approved": approval.approved},
                status=409,
            )

        approval.approved = approved
        approval.responded_at = timezone.now()
        if note:
            approval.message = f"{approval.message}\n\nDecision note: {note}".strip()
        approval.save()

        task = approval.task
        task.status = 'completed' if approved else 'failed'
        task.output_data = {
            **(task.output_data or {}),
            "approved": approved,
            "decided_at": approval.responded_at.isoformat(),
        }
        if not approved and note:
            task.error = note
        task.save()

        return Response(
            ApprovalRequestSerializer(approval).data,
            status=200,
        )
