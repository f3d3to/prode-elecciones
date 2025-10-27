from rest_framework import serializers
from .models import Prediction, OfficialResults
from .validators import (
    get_fuerzas,
    get_provincias,
    validate_national_fuerzas,
    validate_provinciales,
)

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
            raise serializers.ValidationError({"national_percentages": f"La suma es {round(total, 2)}; debería estar cerca de 100% (95-105)"})

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
        self._validate_domain_rules(data)
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
        # Para resultados oficiales somos más estrictos que en predicciones
        if not (98 <= total <= 102):
            diff = round(100.0 - total, 2)
            hint = "faltan" if diff > 0 else "sobran"
            extra = ""
            try:
                bni = float(data.get('blanco_nulo_impugnado')) if data.get('blanco_nulo_impugnado') is not None else None
                if bni is not None:
                    tot_bni = total + bni
                    if 98 <= tot_bni <= 102:
                        extra = f". Tip: sumando blanco_nulo_impugnado da {round(tot_bni,2)}; recordá que national_percentages debe contar solo votos afirmativos"
            except Exception:
                pass
            raise serializers.ValidationError({
                "national_percentages": f"La suma es {round(total, 2)}; {hint} {abs(diff)} p.p. para 100 (tolerancia 98-102){extra}"
            })

    def _validate_provinciales(self, data):
        prov = data.get('provinciales') or {}
        if prov and not isinstance(prov, dict):
            raise serializers.ValidationError({"provinciales": "Formato inválido"})

    # Helpers (duplicados mínimos para evitar mezclar clases en este MVP)
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

    def _validate_domain_rules(self, data):
        # Validamos nombres de fuerzas y restricciones por provincia
        fuerzas = get_fuerzas()
        provincias = get_provincias()
        err = validate_national_fuerzas(data.get('national_percentages') or {}, fuerzas)
        if err:
            raise serializers.ValidationError({"national_percentages": err})
        err = validate_provinciales(data.get('provinciales') or {}, provincias, fuerzas)
        if err:
            raise serializers.ValidationError({"provinciales": err})
