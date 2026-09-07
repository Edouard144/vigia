from django.contrib import admin
from .models import Integration, OAuthConnection

admin.site.register(Integration)
admin.site.register(OAuthConnection)