from rest_framework.routers import DefaultRouter
from .views import EventViewSet, AgentTaskViewSet, ApprovalRequestViewSet

router = DefaultRouter()
router.register('events', EventViewSet, basename='event')
router.register('tasks', AgentTaskViewSet, basename='agenttask')
router.register('approvals', ApprovalRequestViewSet, basename='approvalrequest')

urlpatterns = router.urls
