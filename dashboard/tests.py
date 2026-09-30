from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
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


class ApprovalAPIEndpointTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.event = Event.objects.create(
            user=self.user,
            source='gmail',
            event_type='new_email',
            payload={'subject': 'invoice'},
        )
        self.task = AgentTask.objects.create(
            event=self.event,
            agent_name='triage_agent',
            status='waiting_approval',
            input_data=self.event.payload,
        )
        self.approval = ApprovalRequest.objects.create(
            task=self.task,
            title='Pay invoice',
            intent='Settle the January invoice',
            recipient='billing@vendor.com',
            channel='banking',
            risk='high',
            confidence=0.87,
            expires_in_minutes=1440,
            reasoning=['Involves money transfer'],
            draft='Wire $420 to billing@vendor.com',
            side_effects=['Funds leave the account immediately'],
        )

    def test_list_exposes_frontend_fields_as_read_only(self):
        response = self.client.get('/api/approvals/')
        self.assertEqual(response.status_code, 200)
        data = response.data['results'][0]
        for field in (
            'title', 'intent', 'recipient', 'channel', 'risk', 'confidence',
            'expires_in_minutes', 'reasoning', 'draft', 'side_effects',
        ):
            self.assertIn(field, data)
        self.assertIsNone(data['approved'])

    def test_approved_is_not_writable_through_standard_update(self):
        response = self.client.patch(
            f'/api/approvals/{self.approval.id}/',
            {'approved': True},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.approval.refresh_from_db()
        self.assertIsNone(self.approval.approved)

    def test_respond_accepts_approved_and_message(self):
        response = self.client.post(
            f'/api/approvals/{self.approval.id}/respond/',
            {'approved': True, 'message': 'Looks good'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.approval.refresh_from_db()
        self.task.refresh_from_db()
        self.assertTrue(self.approval.approved)
        self.assertIsNotNone(self.approval.responded_at)
        self.assertEqual(self.task.status, 'completed')

    def test_respond_rejects_missing_approved(self):
        response = self.client.post(
            f'/api/approvals/{self.approval.id}/respond/',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_respond_only_once(self):
        self.client.post(
            f'/api/approvals/{self.approval.id}/respond/',
            {'approved': True},
            format='json',
        )
        response = self.client.post(
            f'/api/approvals/{self.approval.id}/respond/',
            {'approved': False},
            format='json',
        )
        self.assertEqual(response.status_code, 409)
        self.approval.refresh_from_db()
        self.assertTrue(self.approval.approved)

    def test_pending_filter(self):
        self.client.post(
            f'/api/approvals/{self.approval.id}/respond/',
            {'approved': True},
            format='json',
        )
        pending = self.client.get('/api/approvals/?pending=true')
        self.assertEqual(pending.data['count'], 0)
        decided = self.client.get('/api/approvals/?pending=false')
        self.assertEqual(decided.data['count'], 1)

    def test_event_activity_record(self):
        self.client.post(
            f'/api/approvals/{self.approval.id}/respond/',
            {'approved': True},
            format='json',
        )
        response = self.client.get('/api/events/')
        response = self.client.get('/api/events/')
        activity = response.data['results'][0]['activity']
        self.assertEqual(activity['channel'], 'banking')
        self.assertEqual(activity['outcome'], 'approved')
        self.assertEqual(activity['title'], 'Pay invoice')
        self.assertEqual(activity['detail'], 'Wire $420 to billing@vendor.com')
        self.assertIn('time', activity)