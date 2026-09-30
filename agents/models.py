from django.db import models
from common.models import BaseModel
from django.contrib.auth.models import User

class Event(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.CharField(max_length=100)  # e.g. "gmail", "calendar"
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)

class AgentTask(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('waiting_approval', 'Waiting Approval'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tasks')
    agent_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True, null=True)

class ApprovalRequest(BaseModel):
    CHANNEL_CHOICES = [
        ('gmail', 'Gmail'),
        ('calendar', 'Calendar'),
        ('slack', 'Slack'),
        ('banking', 'Banking'),
        ('contacts', 'Contacts'),
    ]
    RISK_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    task = models.ForeignKey(AgentTask, on_delete=models.CASCADE, related_name='approvals')
    title = models.CharField(max_length=255, blank=True, default='')
    intent = models.TextField(blank=True, default='')
    recipient = models.CharField(max_length=255, blank=True, default='')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, blank=True, default='')
    risk = models.CharField(max_length=10, choices=RISK_CHOICES, default='medium')
    confidence = models.FloatField(default=0.0)
    expires_in_minutes = models.PositiveIntegerField(null=True, blank=True)
    reasoning = models.JSONField(default=list, blank=True)
    draft = models.TextField(blank=True, default='')
    side_effects = models.JSONField(default=list, blank=True)
    message = models.TextField(blank=True, default='')
    approved = models.BooleanField(null=True)  # null = pending
    responded_at = models.DateTimeField(null=True, blank=True)
