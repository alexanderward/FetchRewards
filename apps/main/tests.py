from datetime import datetime

from django.core.management import call_command
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status

from apps.main.models import Points


class PointSampleDataTest(TestCase):

    def setUp(self):
        self.client = Client()

    @classmethod
    def setUpTestData(cls):
        call_command('insert_mock_data', verbosity=3)

    def test_initial_balance(self):
        response = self.client.get(reverse('points'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [{'payer': 'DANNON', 'points': 1100},
                                           {'payer': 'MILLER COORS', 'points': 10000},
                                           {'payer': 'UNILEVER', 'points': 200}])

    def test_sample_spend(self):
        response = self.client.post(reverse('points-spend'), {"points": 5000}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [{'payer': 'DANNON', 'points': -100},
                                           {'payer': 'UNILEVER', 'points': -200},
                                           {'payer': 'MILLER COORS', 'points': -4700}])


class PointDataTest(TestCase):

    def setUp(self):
        self.client = Client()

    @classmethod
    def setUpTestData(cls):
        Points.objects.all().delete()

    def test_insert_data(self):
        response = self.client.post(reverse('points'),
                                    {'payer': 'DANNON', 'points': 1100, 'timestamp': datetime.now()},
                                    content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(reverse('points'),
                                    {'payer': 'DANNON', 'points': 100, 'timestamp': datetime.now()},
                                    content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(reverse('points'),
                                    {'payer': 'UNILEVER', 'points': 50, 'timestamp': datetime.now()},
                                    content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(reverse('points'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [{'payer': 'DANNON', 'points': 1200},
                                           {'payer': 'UNILEVER', 'points': 50}])

    def test_cannot_overspend(self):
        response = self.client.post(reverse('points'),
                                    {'payer': 'DANNON', 'points': 500, 'timestamp': datetime.now()},
                                    content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(reverse('points'),
                                    {'payer': 'UNILEVER', 'points': 50, 'timestamp': datetime.now()},
                                    content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(reverse('points'),
                                    {'payer': 'UNILEVER', 'points': 150, 'timestamp': datetime.now()},
                                    content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(reverse('points'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [{'payer': 'DANNON', 'points': 500},
                                           {'payer': 'UNILEVER', 'points': 200}])

        response = self.client.post(reverse('points-spend'), {"points": 5000}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()[0], 'You are attempting to spend more points than are available')

        response = self.client.post(reverse('points-spend'), {"points": 650}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [{'payer': 'DANNON', 'points': -500},
                                           {'payer': 'UNILEVER', 'points': -150}])

        response = self.client.get(reverse('points'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [{'payer': 'DANNON', 'points': 0},
                                           {'payer': 'UNILEVER', 'points': 50}])
