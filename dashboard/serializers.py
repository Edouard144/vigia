from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from agents.models import Event, AgentTask, ApprovalRequest

SOURCE_TO_CHANNEL = {
    'gmail': 'gmail',
    'calendar': 'calendar',
    'slack': 'slack',
    'banking': 'banking',
    'contacts': 'contacts',
}


class ActivitySerializer(serializers.Serializer):
    id = serializers.CharField()
    time = serializers.DateTimeField()
    created_at = serializers.DateTimeField()
    channel = serializers.CharField(allow_blank=True)
    outcome = serializers.ChoiceField(
        choices=['autonomous', 'approved', 'declined', 'observed']
    )
    title = serializers.CharField(allow_blank=True)
    detail = serializers.CharField(allow_blank=True)


class EventSerializer(serializers.ModelSerializer):
    activity = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['user', 'processed', 'created_at', 'updated_at', 'activity']

    def validate_source(self, value):
        if not value.strip():
            raise serializers.ValidationError("source cannot be empty")
        return value

    def validate_payload(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("payload must be a JSON object")
        return value

    def _derive_activity(self, event):
        tasks = list(event.tasks.prefetch_related('approvals').all())

        channel = ''
        outcome = 'observed'
        title = event.event_type or event.source
        detail = ''
        first_output = {}

        for task in tasks:
            approvals = list(task.approvals.all())
            output = task.output_data or {}
            first_output = first_output or output

            for approval in approvals:
                channel = approval.channel or channel
                title = approval.title or title
                detail = approval.draft or approval.message or detail

                if approval.approved is True:
                    outcome = 'approved'
                elif approval.approved is False and outcome != 'approved':
                    outcome = 'declined'

            if not approvals and task.status == 'completed' and outcome == 'observed':
                outcome = 'autonomous'

            if task.status == 'failed' and outcome == 'observed' and not detail:
                detail = task.error or ''

            if not channel:
                channel = output.get('channel', '')

        if not channel:
            channel = SOURCE_TO_CHANNEL.get((event.source or '').strip().lower(), event.source or '')

        if not detail:
            detail = first_output.get('action_plan', '') or first_output.get('summary', '')

        if not title:
            title = first_output.get('title', '')

        return {
            'id': str(event.id),
            'time': event.created_at,
            'created_at': event.created_at,
            'channel': channel,
            'outcome': outcome,
            'title': title,
            'detail': detail,
        }

    @extend_schema_field(ActivitySerializer)
    def get_activity(self, obj):
        return self._derive_activity(obj)


class AgentTaskSerializer(serializers.ModelSerializer):
    event = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = AgentTask
        fields = '__all__'
        read_only_fields = ['status', 'output_data', 'error', 'event', 'created_at', 'updated_at']


class ApprovalRequestSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(read_only=True)
    reasoning = serializers.ListField(
        child=serializers.CharField(allow_blank=True), required=False
    )
    side_effects = serializers.ListField(
        child=serializers.CharField(allow_blank=True), required=False
    )

    class Meta:
        model = ApprovalRequest
        fields = '__all__'
        read_only_fields = [
            'task',
            'approved',
            'responded_at',
            'created_at',
            'updated_at',
        ]

    def validate_confidence(self, value):
        if not 0.0 <= value <= 1.0:
            raise serializers.ValidationError("confidence must be between 0 and 1")
        return value


class ApprovalRespondSerializer(serializers.Serializer):
    approved = serializers.BooleanField()
    message = serializers.CharField(required=False, allow_blank=True, default='')
