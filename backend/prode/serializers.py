from rest_framework import serializers
from .models import Prediction, OfficialResults

class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = [
            'id','username','email','top3','national_percentages','participation','margin_1_2','blanco_nulo_impugnado','total_votes','provinciales','bonus','created_at','updated_at','sync_pending'
        ]
        read_only_fields = ['id','created_at','updated_at','sync_pending']

    def validate(self, data):
        self._validate_national_percentages(data)
        self._validate_top3(data)
        self._validate_percent_fields(data, ['participation','margin_1_2','blanco_nulo_impugnado'])
        self._validate_total_votes(data)
        return data

    def _validate_national_percentages(self, data):
        np = data.get('national_percentages') or {}
        if not np:
            return
        total = 0.0
        for k, v in np.items():
            fv = self._to_float(v, field="national_percentages", key=k)
            self._assert_range(fv, 0, 100, field="national_percentages", key=k)
            total += fv
        if not (95 <= total <= 105):
            raise serializers.ValidationError({"national_percentages": "La suma debería estar cerca de 100% (95-105)"})

    def _validate_top3(self, data):
        t3 = data.get('top3') or []
        if len(t3) > 3:
            raise serializers.ValidationError({"top3": "Top-3 debe tener hasta 3 fuerzas"})

    def _validate_percent_fields(self, data, fields):
        for field in fields:
            val = data.get(field)
            if val is None:
                continue
            fv = self._to_float(val, field=field)
            self._assert_range(fv, 0, 100, field=field)

    def _validate_total_votes(self, data):
        tv = data.get('total_votes')
        if tv is None:
            return
        try:
            iv = int(tv)
        except (ValueError, TypeError):
            raise serializers.ValidationError({"total_votes": "Debe ser entero"})
        if iv < 0:
            raise serializers.ValidationError({"total_votes": "Debe ser >= 0"})

    @staticmethod
    def _to_float(value, *, field: str, key: str | None = None) -> float:
        try:
            return float(value)
        except (ValueError, TypeError):
            suffix = f" para {key}" if key is not None else ""
            raise serializers.ValidationError({field: f"Valor inválido{suffix}"})

    @staticmethod
    def _assert_range(value: float, lo: float, hi: float, *, field: str, key: str | None = None):
        if value < lo or value > hi:
            suffix = f" {key}" if key is not None else ""
            raise serializers.ValidationError({field: f"{suffix} fuera de rango {lo}-{hi}"})


class OfficialResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficialResults
        fields = [
            'id', 'created_at', 'updated_at', 'published_at', 'is_published',
            'national_percentages', 'participation', 'margin_1_2', 'blanco_nulo_impugnado', 'total_votes',
            'provinciales',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        self._validate_percent_fields(data, ['participation', 'margin_1_2', 'blanco_nulo_impugnado'])
        self._validate_national_percentages(data)
        self._validate_provinciales(data)
        return data

    def _validate_percent_fields(self, data, fields):
        for field in fields:
            val = data.get(field)
            if val is None:
                continue
            fv = self._to_float(val, field=field)
            self._assert_range(fv, 0, 100, field=field)

    def _validate_national_percentages(self, data):
        np = data.get('national_percentages') or {}
        if not np:
            return
        total = 0.0
        for k, v in np.items():
            fv = self._to_float(v, field='national_percentages', key=k)
            self._assert_range(fv, 0, 100, field='national_percentages', key=k)
            total += fv
        if not (95 <= total <= 105):
            raise serializers.ValidationError({"national_percentages": "La suma debería estar cerca de 100% (95-105)"})

    def _validate_provinciales(self, data):
        prov = data.get('provinciales') or {}
        if prov and not isinstance(prov, dict):
            raise serializers.ValidationError({"provinciales": "Formato inválido"})
