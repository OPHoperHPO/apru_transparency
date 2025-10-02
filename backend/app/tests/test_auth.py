import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
User = get_user_model()
@pytest.mark.django_db
class TestAuthentication:
    def test_token_obtain_pair(self):
        """Test JWT token generation"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role=User.Role.USER
        )
        client = APIClient()
        url = reverse('token_obtain_pair')
        data = {'username': 'testuser', 'password': 'testpass123'}
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
    def test_token_refresh(self):
        """Test JWT token refresh"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role=User.Role.USER
        )
        client = APIClient()
        url = reverse('token_obtain_pair')
        data = {'username': 'testuser', 'password': 'testpass123'}
        response = client.post(url, data, format='json')
        refresh_token = response.data['refresh']
        url = reverse('token_refresh')
        data = {'refresh': refresh_token}
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
    def test_invalid_credentials(self):
        """Test authentication with invalid credentials"""
        client = APIClient()
        url = reverse('token_obtain_pair')
        data = {'username': 'nonexistent', 'password': 'wrongpass'}
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
@pytest.mark.django_db
class TestUserRoles:
    def test_admin_role(self):
        """Test admin user role"""
        admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )
        assert admin_user.is_admin()
        assert admin_user.role == User.Role.ADMIN
    def test_regulator_role(self):
        """Test regulator user role"""
        regulator_user = User.objects.create_user(
            username='regulator',
            password='reg123',
            role=User.Role.REGULATOR
        )
        assert regulator_user.role == User.Role.REGULATOR
        assert not regulator_user.is_admin()
    def test_owner_role(self):
        """Test owner user role"""
        owner_user = User.objects.create_user(
            username='owner',
            password='owner123',
            role=User.Role.OWNER
        )
        assert owner_user.role == User.Role.OWNER
        assert not owner_user.is_admin()
    def test_user_role(self):
        """Test regular user role"""
        regular_user = User.objects.create_user(
            username='user',
            password='user123',
            role=User.Role.USER
        )
        assert regular_user.role == User.Role.USER
        assert not regular_user.is_admin()
