import os
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from django.test import TestCase


@contextmanager
def set_deadline_env(dt_iso: str):
    old = os.environ.get('DEADLINE')
    os.environ['DEADLINE'] = dt_iso
    try:
        yield
    finally:
        if old is None:
            os.environ.pop('DEADLINE', None)
        else:
            os.environ['DEADLINE'] = old


class DeadlineBehaviorTests(TestCase):
    def setUp(self):
        self.predictions_url = '/api/predictions'
        self.mine_url = '/api/predictions/mine'
        self.metadata_url = '/api/metadata'

    def _base_payload(self):
        return {
            'username': 'Tester',
            'email': 'deadline@example.com',
            'top3': [],
            'national_percentages': {},
            'bonus': {},
            'provinciales': {},
        }

    def test_post_blocked_after_deadline(self):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        with set_deadline_env(past):
            res = self.client.post(self.predictions_url, data=self._base_payload(), content_type='application/json')
            assert res.status_code == 403
            assert 'Elecciones finalizadas' in res.content.decode('utf-8')

    def test_gets_still_work_after_deadline(self):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        with set_deadline_env(past):
            # metadata sigue disponible
            r1 = self.client.get(self.metadata_url)
            assert r1.status_code == 200
            # predictions/mine lectura soft también
            r2 = self.client.get(self.mine_url, {'email': 'x@y.z', 'soft': 1})
            assert r2.status_code == 200