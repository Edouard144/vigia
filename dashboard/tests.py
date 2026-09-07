from django.test import TestCase
from django.contrib.auth.models import User
from agents.models import Event, AgentTask, ApprovalRequest


class EventAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_event_creation(self):
        event = Event.objects.create(
            user=self.user,
            source='gmail',
            event_type='new_email',
            payload={'subject': 'test'}
        )
        self.assertEqual(event.source, 'gmail')
        self.assertFalse(event.processed)


class AgentTaskAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.event = Event.objects.create(
            user=self.user,
            source='gmail',
            event_type='new_email',
            payload={'subject': 'test'}
        )

    def test_task_creation(self):
        task = AgentTask.objects.create(
            event=self.event,
            agent_name='triage_agent',
            status='pending',
            input_data=self.event.payload
        )
        self.assertEqual(task.status, 'pending')


class ApprovalRequestAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.event = Event.objects.create(
            user=self.user,
            source='calendar',
            event_type='meeting',
            payload={'needs_approval': True, 'title': 'Board sync'}
        )
        self.task = AgentTask.objects.create(
            event=self.event,
            agent_name='triage_agent',
            status='running',
            input_data=self.event.payload
        )

    def test_approval_request_creation(self):
        approval = ApprovalRequest.objects.create(
            task=self.task,
            message='Approve this action'
        )
        self.assertIsNone(approval.approved)