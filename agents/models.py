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
    task = models.ForeignKey(AgentTask, on_delete=models.CASCADE, related_name='approvals')
    message = models.TextField()
    approved = models.BooleanField(null=True)  # null = pending
    responded_at = models.DateTimeField(null=True, blank=True)
