from django.db import models
from common.models import BaseModel
from django.contrib.auth.models import User

class Integration(BaseModel):
    PROVIDER_CHOICES = [
        ('gmail', 'Gmail'),
        ('calendar', 'Google Calendar'),
        ('slack', 'Slack'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='integrations')
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    token_expiry = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'provider')
