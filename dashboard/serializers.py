from rest_framework import serializers
from agents.models import Event, AgentTask, ApprovalRequest

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['user', 'processed']

    def validate_source(self, value):
        if not value.strip():
            raise serializers.ValidationError("source cannot be empty")
        return value

    def validate_payload(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("payload must be a JSON object")
        return value

class AgentTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentTask
        fields = '__all__'
        read_only_fields = ['status', 'output_data', 'error']

class ApprovalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRequest
        fields = '__all__'
        read_only_fields = ['approved', 'responded_at']
