import json
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from app.processing.models import Task, Worker
User = get_user_model()
@pytest.mark.django_db
class TestTasksAPI:
    def setup_method(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role=User.Role.USER
        )
    def test_submit_task(self):
        """Test task submission"""
        client = APIClient()
        url = reverse('task-submit')
        data = {"url": "https://example.com"}
        response = client.post(url, data=json.dumps(data), content_type='application/json')
        assert response.status_code == status.HTTP_201_CREATED
        task_id = response.json()['id']
        assert Task.objects.filter(id=task_id).exists()
        task = Task.objects.get(id=task_id)
        assert task.url == "https://example.com"
        assert task.status == Task.Status.NEW
    def test_task_status(self):
        """Test getting task status"""
        client = APIClient()
        url = reverse('task-submit')
        data = {"url": "https://example.com"}
        response = client.post(url, data=json.dumps(data), content_type='application/json')
        task_id = response.json()['id']
        url = reverse('task-status', kwargs={'task_id': task_id})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == Task.Status.NEW
        assert response.json()['url'] == "https://example.com"
    def test_task_with_priority(self):
        """Test task submission with priority"""
        client = APIClient()
        url = reverse('task-submit')
        data = {
            "url": "https://example.com",
            "priority": Task.Priority.HIGH
        }
        response = client.post(url, data=json.dumps(data), content_type='application/json')
        assert response.status_code == status.HTTP_201_CREATED
        task_id = response.json()['id']
        task = Task.objects.get(id=task_id)
        assert task.priority == Task.Priority.HIGH
    def test_invalid_url_submission(self):
        """Test submitting invalid URL"""
        client = APIClient()
        url = reverse('task-submit')
        data = {"url": "not-a-valid-url"}
        response = client.post(url, data=json.dumps(data), content_type='application/json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    def test_missing_url_submission(self):
        """Test submitting without URL"""
        client = APIClient()
        url = reverse('task-submit')
        data = {}
        response = client.post(url, data=json.dumps(data), content_type='application/json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    def test_task_result_before_completion(self):
        """Test getting result for incomplete task"""
        client = APIClient()
        url = reverse('task-submit')
        data = {"url": "https://example.com"}
        response = client.post(url, data=json.dumps(data), content_type='application/json')
        task_id = response.json()['id']
        url = reverse('task-result', kwargs={'task_id': task_id})
        response = client.get(url)
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]
    def test_nonexistent_task_status(self):
        """Test getting status of non-existent task"""
        client = APIClient()
        fake_uuid = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
        url = reverse('task-status', kwargs={'task_id': fake_uuid})
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
@pytest.mark.django_db
class TestWorkerAPI:
    def setup_method(self):
        """Set up test data"""
        self.worker = Worker.objects.create(
            name='test-worker',
            token='test-token-123'
        )
    def test_worker_next_task(self):
        """Test worker getting next task"""
        task = Task.objects.create(
            url='https://example.com',
            status=Task.Status.NEW
        )
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.worker.token}')
        url = reverse('worker-task-next')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.assigned_to == self.worker
        assert task.status == Task.Status.QUEUED
    def test_worker_no_tasks_available(self):
        """Test worker when no tasks available"""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.worker.token}')
        url = reverse('worker-task-next')
        response = client.get(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
    def test_worker_update_task_status(self):
        """Test worker updating task status"""
        task = Task.objects.create(
            url='https://example.com',
            status=Task.Status.QUEUED,
            assigned_to=self.worker
        )
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.worker.token}')
        url = reverse('worker-task-status', kwargs={'task_id': str(task.id)})
        data = {
            'status': Task.Status.IN_PROGRESS,
            'progress': 50.0
        }
        response = client.post(url, data=json.dumps(data), content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.status == Task.Status.IN_PROGRESS
        assert task.progress == 50.0
    def test_worker_submit_result(self):
        """Test worker submitting task result"""
        task = Task.objects.create(
            url='https://example.com',
            status=Task.Status.IN_PROGRESS,
            assigned_to=self.worker
        )
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.worker.token}')
        url = reverse('worker-task-result', kwargs={'task_id': str(task.id)})
        result_data = {
            'dark_patterns': [],
            'trust_score': 85.0,
            'analysis_complete': True
        }
        data = {
            'status': Task.Status.DONE,
            'result_json': result_data
        }
        response = client.post(url, data=json.dumps(data), content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.status == Task.Status.DONE
        assert task.result_json == result_data
    def test_unauthorized_worker_access(self):
        """Test accessing worker endpoints without proper token"""
        client = APIClient()
        url = reverse('worker-task-next')
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
