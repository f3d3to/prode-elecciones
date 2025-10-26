from django.test import TestCase


class MetadataFuerzasPorProvinciaTests(TestCase):
    def test_metadata_has_per_province_mapping(self):
        res = self.client.get('/api/metadata')
        assert res.status_code == 200
        js = res.json()
        fpp = js.get('fuerzas_por_provincia') or {}
        assert isinstance(fpp, dict)
        # Debe contener CABA y lista de fuerzas
        caba = fpp.get('CABA')
        assert isinstance(caba, list)
        # No debe listar 'Unión Federal' para CABA
        assert 'Unión Federal' not in caba