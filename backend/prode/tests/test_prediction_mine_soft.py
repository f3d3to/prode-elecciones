from django.test import TestCase
from django.urls import reverse
from prode.models import Prediction

class PredictionMineSoftTests(TestCase):
    def setUp(self):
        self.url = '/api/predictions/mine'

    def test_soft_new_email_returns_exists_false(self):
        res = self.client.get(self.url, {'email': 'nuevo@example.com', 'soft': 1})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['exists'], False)

    def test_soft_existing_email_returns_prediction(self):
        Prediction.objects.create(username='Alice', email='alice@example.com')
        res = self.client.get(self.url, {'email': 'alice@example.com', 'soft': 1})
        self.assertEqual(res.status_code, 200)
        js = res.json()
        self.assertTrue(js['exists'])
        self.assertEqual(js['prediction']['email'], 'alice@example.com')

    def test_hard_mode_404_for_missing(self):
        res = self.client.get(self.url, {'email': 'missing@example.com'})
        self.assertEqual(res.status_code, 404)
