from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.hashers import make_password
from .models import User, Employer, Executor
from rest_framework_simplejwt.tokens import RefreshToken

class AuthViewsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            login='testuser',
            password=make_password('testpass123'),
            role='employer',
            username='Test User'
        )
        self.employer = Employer.objects.create(
            user=self.user,
            name='Test Employer',
            organization='Test Org',
            description='Test Description'
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)

    def test_login_success(self):
        url = reverse('login') + '?login=testuser&password=testpass123'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['login'], 'testuser')

    def test_login_failure(self):
        url = reverse('login') + '?login=wrong&password=wrong'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_refresh_token_success(self):
        url = reverse('refresh-token')
        response = self.client.get(
            url, 
            HTTP_X_REFRESH_TOKEN=self.refresh_token
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_token_failure(self):
        url = reverse('refresh-token')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_debug_token_success(self):
        url = reverse('debug-token')
        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.user.id)

    def test_logout_success(self):
        url = reverse('logout')
        response = self.client.post(
            url,
            {'refresh_token': self.refresh_token},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class UserRegistrationTests(APITestCase):
    def test_register_employer_success(self):
        url = reverse('register')
        data = {
            'login': 'newemployer',
            'password': 'employerpass123',
            'role': 'employer',
            'username': 'New Employer',
            'organization': 'New Org',
            'description': 'New Desc'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(login='newemployer').exists())
        self.assertTrue(Employer.objects.filter(user__login='newemployer').exists())

    def test_register_executor_success(self):
        url = reverse('register')
        data = {
            'login': 'newexecutor',
            'password': 'executorpass123',
            'role': 'executor',
            'username': 'New Executor',
            'description': 'New Desc'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Executor.objects.filter(user__login='newexecutor').exists())

    def test_register_duplicate_login(self):
        User.objects.create(login='existing', password='pass123')
        
        url = reverse('register')
        data = {
            'login': 'existing',
            'password': 'newpass123',
            'role': 'employer'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.data)

class ProtectedViewsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            login='testuser',
            password=make_password('testpass123'),
            role='employer',
            username='Test User'
        )
        self.employer = Employer.objects.create(
            user=self.user,
            name='Test Employer'
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_get_user_by_id_success(self):
        url = reverse('get-user-by-id') + f'?id={self.user.id}'
        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['id'], self.user.id)

    def test_get_employer_success(self):
        url = reverse('get-employer') + f'?id={self.user.id}'
        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], 'Test Employer')

    def test_get_executor_success(self):
        executor_user = User.objects.create(
            login='executor',
            password=make_password('execpass'),
            role='executor',
            username='Executor'
        )
        executor = Executor.objects.create(
            user=executor_user,
            name='Test Executor'
        )
        
        url = reverse('get-executor') + f'?id={executor_user.id}'
        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], 'Test Executor')

    def test_protected_views_without_token(self):
        urls = [
            reverse('get-user-by-id') + '?id=1',
            reverse('get-employer') + '?id=1',
            reverse('get-executor') + '?id=1'
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)