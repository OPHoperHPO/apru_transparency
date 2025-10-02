import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from app.projects.models import Project, Complaint
User = get_user_model()
@pytest.mark.django_db
class TestProjectsAPI:
    def setup_method(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            role=User.Role.ADMIN,
            is_superuser=True
        )
        self.regulator_user = User.objects.create_user(
            username='reg',
            password='reg123',
            role=User.Role.REGULATOR
        )
        self.owner_user = User.objects.create_user(
            username='owner',
            password='owner123',
            role=User.Role.OWNER
        )
        self.regular_user = User.objects.create_user(
            username='user',
            password='user123',
            role=User.Role.USER
        )
    def authenticate_client(self, user):
        """Helper method to authenticate client"""
        client = APIClient()
        url = reverse('token_obtain_pair')
        data = {'username': user.username, 'password': f'{user.username}123'}
        response = client.post(url, data, format='json')
        token = response.data['access']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client
    def test_create_project_as_owner(self):
        """Test project creation by owner"""
        client = self.authenticate_client(self.owner_user)
        url = reverse('projects-list')
        data = {
            'name': 'Test Project',
            'site_url': 'https://example.com'
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Project.objects.filter(name='Test Project').exists()
    def test_create_project_as_regular_user(self):
        """Test project creation by regular user"""
        client = self.authenticate_client(self.regular_user)
        url = reverse('projects-list')
        data = {
            'name': 'Test Project',
            'site_url': 'https://example.com'
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
    def test_list_projects_as_admin(self):
        """Test project listing as admin (should see all)"""
        Project.objects.create(
            name='Project 1',
            site_url='https://example1.com',
            owner=self.owner_user
        )
        Project.objects.create(
            name='Project 2',
            site_url='https://example2.com',
            owner=self.regular_user
        )
        client = self.authenticate_client(self.admin_user)
        url = reverse('projects-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2
    def test_list_projects_as_owner(self):
        """Test project listing as owner (should see only own)"""
        Project.objects.create(
            name='Owner Project',
            site_url='https://owner.com',
            owner=self.owner_user
        )
        Project.objects.create(
            name='User Project',
            site_url='https://user.com',
            owner=self.regular_user
        )
        client = self.authenticate_client(self.owner_user)
        url = reverse('projects-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        for project in response.data:
            assert project['name'] == 'Owner Project'
    def test_unauthenticated_access_public_projects(self):
        """Test accessing projects without authentication"""
        Project.objects.create(
            name='Public Project',
            site_url='https://public.com',
            owner=self.owner_user
        )
        client = APIClient()
        url = reverse('projects-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
@pytest.mark.django_db
class TestComplaintsAPI:
    def setup_method(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            role=User.Role.ADMIN,
            is_superuser=True
        )
        self.regulator_user = User.objects.create_user(
            username='reg',
            password='reg123',
            role=User.Role.REGULATOR
        )
        self.owner_user = User.objects.create_user(
            username='owner',
            password='owner123',
            role=User.Role.OWNER
        )
        self.regular_user = User.objects.create_user(
            username='user',
            password='user123',
            role=User.Role.USER
        )
        self.project = Project.objects.create(
            name='Test Project',
            site_url='https://example.com',
            owner=self.owner_user
        )
    def authenticate_client(self, user):
        """Helper method to authenticate client"""
        client = APIClient()
        url = reverse('token_obtain_pair')
        if user.username == 'admin':
            password = 'admin123'
        elif user.username == 'reg':
            password = 'reg123'
        elif user.username == 'owner':
            password = 'owner123'
        else:
            password = f'{user.username}123'
        data = {'username': user.username, 'password': password}
        response = client.post(url, data, format='json')
        if 'access' not in response.data:
            print(f"Auth failed for {user.username}: {response.data}")
            return None
        token = response.data['access']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client
    def test_create_complaint_as_regular_user(self):
        """Test complaint creation by regular user (should be allowed)"""
        client = self.authenticate_client(self.regular_user)
        url = reverse('complaints-list')
        data = {
            'project': str(self.project.id),
            'complaint_type': Complaint.Type.FALSE_POSITIVE,
            'subject': 'Test Complaint',
            'text': 'This is a test complaint'
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Complaint.objects.filter(subject='Test Complaint').exists()
    def test_create_complaint_as_owner(self):
        """Test complaint creation by owner (should be restricted)"""
        client = self.authenticate_client(self.owner_user)
        url = reverse('complaints-list')
        data = {
            'project': str(self.project.id),
            'complaint_type': Complaint.Type.FALSE_POSITIVE,
            'subject': 'Owner Complaint',
            'text': 'This should not be allowed'
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    def test_create_complaint_as_regulator(self):
        """Test complaint creation by regulator (should be restricted)"""
        client = self.authenticate_client(self.regulator_user)
        url = reverse('complaints-list')
        data = {
            'project': str(self.project.id),
            'complaint_type': Complaint.Type.FALSE_POSITIVE,
            'subject': 'Regulator Complaint',
            'text': 'This should not be allowed'
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    def test_list_complaints_as_regulator(self):
        """Test complaint listing as regulator (should see all)"""
        Complaint.objects.create(
            project=self.project,
            author=self.regular_user,
            complaint_type=Complaint.Type.FALSE_POSITIVE,
            subject='User Complaint',
            text='Test complaint'
        )
        client = self.authenticate_client(self.regulator_user)
        url = reverse('complaints-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    def test_list_complaints_as_regular_user(self):
        """Test complaint listing as regular user (should see only own)"""
        user_complaint = Complaint.objects.create(
            project=self.project,
            author=self.regular_user,
            complaint_type=Complaint.Type.FALSE_POSITIVE,
            subject='User Complaint',
            text='User complaint'
        )
        another_user = User.objects.create_user(
            username='another',
            password='another123',
            role=User.Role.USER
        )
        Complaint.objects.create(
            project=self.project,
            author=another_user,
            complaint_type=Complaint.Type.OTHER,
            subject='Another Complaint',
            text='Another complaint'
        )
        client = self.authenticate_client(self.regular_user)
        url = reverse('complaints-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        for complaint in response.data:
            assert complaint['subject'] == 'User Complaint'
    def test_respond_to_complaint_as_regulator(self):
        """Test responding to complaint as regulator"""
        complaint = Complaint.objects.create(
            project=self.project,
            author=self.regular_user,
            complaint_type=Complaint.Type.FALSE_POSITIVE,
            subject='Test Complaint',
            text='Test complaint'
        )
        client = self.authenticate_client(self.regulator_user)
        url = reverse('complaints-respond', kwargs={'pk': str(complaint.id)})
        data = {
            'response_text': 'Thank you for your complaint. We are investigating.',
            'status': Complaint.Status.INVESTIGATING
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        complaint.refresh_from_db()
        assert complaint.response_text == 'Thank you for your complaint. We are investigating.'
        assert complaint.status == Complaint.Status.INVESTIGATING
        assert complaint.responded_by == self.regulator_user
    def test_respond_to_complaint_as_regular_user(self):
        """Test responding to complaint as regular user (should be forbidden)"""
        complaint = Complaint.objects.create(
            project=self.project,
            author=self.regular_user,
            complaint_type=Complaint.Type.FALSE_POSITIVE,
            subject='Test Complaint',
            text='Test complaint'
        )
        client = self.authenticate_client(self.regular_user)
        url = reverse('complaints-respond', kwargs={'pk': str(complaint.id)})
        data = {
            'response_text': 'Self response',
            'status': Complaint.Status.INVESTIGATING
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
