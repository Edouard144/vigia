from rest_framework.routers import DefaultRouter
from .views import EventViewSet, AgentTaskViewSet, ApprovalRequestViewSet

router = DefaultRouter()
router.register('events', EventViewSet)
router.register('tasks', AgentTaskViewSet)
router.register('approvals', ApprovalRequestViewSet)

urlpatterns = router.urls
