from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from .models import PaymentAcc, PaymentOperations
from .serializers import VirtualCardSerializer

class PaymentViewsTests(APITestCase):
    def setUp(self):
        self.employer_data = {
            'modify_dttm': timezone.now(),
            'owner_id': 1,
            'role': 'employer'
        }
        self.task_data = {
            'modify_dttm': timezone.now(),
            'owner_id': 1,
            'role': 'task'
        }
        self.executor_data = {
            'modify_dttm': timezone.now(),
            'owner_id': 2,
            'role': 'executor'
        }
        
        self.employer_acc = PaymentAcc.create_virtual_card(**self.employer_data)
        self.task_acc = PaymentAcc.create_virtual_card(**self.task_data)
        self.executor_acc = PaymentAcc.create_virtual_card(**self.executor_data)

    def test_create_virtual_card(self):
        url = reverse('create-card')
        data = {
            'modify_dttm': timezone.now(),
            'owner': 3,
            'role': 'employer'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PaymentAcc.objects.count(), 4)

    def test_get_balance(self):
        url = reverse('get-balance') + '?id=1&role=employer'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['balance']), 0.00)

    def test_to_employer(self):
        url = reverse('to-employer') + '?id=1&count=100.50&date=2023-01-01'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        employer = PaymentAcc.objects.get(owner_id=1, role='employer')
        self.assertEqual(float(employer.balance), 100.50)
        
        self.assertEqual(PaymentOperations.objects.count(), 1)

    def test_to_task(self):
        url = reverse('to-task') + '?EmployerID=1&TaskID=1&count=50.25&date=2023-01-01'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        employer = PaymentAcc.objects.get(owner_id=1, role='employer')
        task = PaymentAcc.objects.get(owner_id=1, role='task')
        self.assertEqual(float(employer.balance), -50.25)
        self.assertEqual(float(task.balance), 50.25)

    def test_to_executor(self):
        PaymentAcc.update_task_balance(task_id=1, amount=100)
        
        url = reverse('to-executor') + '?ExecutorID=2&TaskID=1&count=75.30&date=2023-01-01'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        task = PaymentAcc.objects.get(owner_id=1, role='task')
        executor = PaymentAcc.objects.get(owner_id=2, role='executor')
        self.assertEqual(float(task.balance), 24.70)
        self.assertEqual(float(executor.balance), 75.30)

    def test_from_executor(self):
        PaymentAcc.update_executor_balance(executor_id=2, amount=100)
        
        url = reverse('from-executor') + '?ExecutorID=2&count=40.50&date=2023-01-01'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        executor = PaymentAcc.objects.get(owner_id=2, role='executor')
        self.assertEqual(float(executor.balance), 59.50)

    def test_get_operations(self):
        PaymentOperations.create_operation(
            payment_id=1,
            reciever_id=1,
            count=100,
            date='2023-01-01',
            initiator=None,
            task_id=None
        )
        
        url = reverse('get-operations') + '?id=1'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['reciever_id'], 1)