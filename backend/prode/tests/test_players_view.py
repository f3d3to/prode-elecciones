from django.test import TestCase

from prode.models import Prediction
from prode.validators import get_fuerzas, get_provincias, get_fuerzas_por_provincia


class PlayersViewTests(TestCase):
    def setUp(self):
        self.url = '/api/players'

    def test_only_completed_users_are_listed(self):
        fuerzas = list(get_fuerzas()) or ['F1','F2','F3']
        provincias = list(get_provincias()) or ['Provincia X']
        # Not completed: only username/email
        Prediction.objects.create(username='OnlyUser', email='only@example.com')

        # Completed by top3 (usa hasta 3 fuerzas disponibles)
        top3 = fuerzas[:3] if len(fuerzas) >= 3 else fuerzas[:1]
        Prediction.objects.create(username='Top3User', email='top3@example.com', top3=top3)

        # Completed by national sum > 0 (usa primeras dos fuerzas disponibles)
        nat_forces = fuerzas[:2] if len(fuerzas) >= 2 else fuerzas[:1]
        nat_payload = {nat_forces[0]: 10}
        if len(nat_forces) > 1:
            nat_payload[nat_forces[1]] = 5
        Prediction.objects.create(username='NatUser', email='nat@example.com', national_percentages=nat_payload)

        # Completed by provinciales non-empty (usa primera provincia y primera fuerza)
        prov = provincias[0]
        per_prov = get_fuerzas_por_provincia()
        allowed = list(per_prov.get(prov) or fuerzas)
        force = allowed[0]
        Prediction.objects.create(
            username='ProvUser',
            email='prov@example.com',
            provinciales={prov: {'porcentajes': {force: 40}}}
        )

        expected_total = Prediction.objects.count()
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        js = res.json()
        names = js['usernames']
        self.assertEqual(js['count_completed'], len(names))
        self.assertEqual(js['count_total'], expected_total)
        self.assertIn('Top3User', names)
        self.assertIn('NatUser', names)
        self.assertIn('ProvUser', names)
        self.assertNotIn('OnlyUser', names)
