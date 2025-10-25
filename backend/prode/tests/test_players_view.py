from django.test import TestCase

from prode.models import Prediction


class PlayersViewTests(TestCase):
    def setUp(self):
        self.url = '/api/players'

    def test_only_completed_users_are_listed(self):
        # Not completed: only username/email
        Prediction.objects.create(username='OnlyUser', email='only@example.com')

        # Completed by top3
        Prediction.objects.create(username='Top3User', email='top3@example.com', top3=['LLA','UxP','JxC'])

        # Completed by national sum > 0
        Prediction.objects.create(username='NatUser', email='nat@example.com', national_percentages={'LLA': 10, 'UxP': 5})

        # Completed by provinciales non-empty
        Prediction.objects.create(username='ProvUser', email='prov@example.com', provinciales={'CABA': {'porcentajes': {'LLA': 40}}})

        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        js = res.json()
        names = js['usernames']
        self.assertEqual(js['count'], len(names))
        self.assertIn('Top3User', names)
        self.assertIn('NatUser', names)
        self.assertIn('ProvUser', names)
        self.assertNotIn('OnlyUser', names)
