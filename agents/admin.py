from django.contrib import admin
from .models import Event, AgentTask, ApprovalRequest

admin.site.register(Event)
admin.site.register(AgentTask)
admin.site.register(ApprovalRequest)
