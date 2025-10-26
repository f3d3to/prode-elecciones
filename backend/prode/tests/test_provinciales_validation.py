from django.test import TestCase


class ProvincialesValidationTests(TestCase):
    def setUp(self):
        self.url = '/api/predictions'

    def _base_payload(self):
        return {
            'username': 'Tester',
            'email': 'tester@example.com',
            'top3': [],
            'national_percentages': {},
            'bonus': {},
            'provinciales': {},
        }

    def test_caba_rejects_union_federal(self):
        payload = self._base_payload()
        payload['provinciales'] = {
            'CABA': {
                'porcentajes': { 'Unión Federal': 10 },
                'winner': 'Unión Federal',
            }
        }
        res = self.client.post(self.url, data=payload, content_type='application/json')
        assert res.status_code == 400, res.content
        js = res.json()
        # Debe señalar fuerza inválida en CABA
        assert 'provinciales' in js
        assert 'Unión Federal' in js['provinciales']
        assert 'CABA' in js['provinciales']

    def test_caba_accepts_allowed_force(self):
        payload = self._base_payload()
        payload['provinciales'] = {
            'CABA': {
                'porcentajes': { 'LLA': 35, 'Fuerza Patria': 40 },
                'winner': 'Fuerza Patria',
            }
        }
        res = self.client.post(self.url, data=payload, content_type='application/json')
        assert res.status_code == 201, res.content