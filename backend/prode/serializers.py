from rest_framework import serializers
from .models import Prediction

class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = [
            'id','username','email','top3','national_percentages','participation','margin_1_2','blanco_nulo_impugnado','total_votes','provinciales','bonus','created_at','updated_at','sync_pending'
        ]
        read_only_fields = ['id','created_at','updated_at','sync_pending']

    def validate(self, data):
        # Simple ranges and sum≈100 check for national_percentages
        np = data.get('national_percentages') or {}
        total = 0.0
        for k,v in np.items():
            try:
                fv = float(v)
            except (ValueError, TypeError):
                raise serializers.ValidationError({"national_percentages": f"Valor inválido para {k}"})
            if fv < 0 or fv > 100:
                raise serializers.ValidationError({"national_percentages": f"{k} fuera de rango 0-100"})
            total += fv
        if np and not (95 <= total <= 105):
            raise serializers.ValidationError({"national_percentages": "La suma debería estar cerca de 100% (95-105)"})
        # Top3 must be list length<=3
        t3 = data.get('top3') or []
        if len(t3) > 3:
            raise serializers.ValidationError({"top3": "Top-3 debe tener hasta 3 fuerzas"})
        # Simple ranges
        for field in ['participation','margin_1_2','blanco_nulo_impugnado']:
            val = data.get(field)
            if val is not None:
                try:
                    fv = float(val)
                except (ValueError, TypeError):
                    raise serializers.ValidationError({field: "Debe ser número"})
                if fv < 0 or fv > 100:
                    raise serializers.ValidationError({field: "Rango 0-100"})
        tv = data.get('total_votes')
        if tv is not None:
            try:
                iv = int(tv)
            except (ValueError, TypeError):
                raise serializers.ValidationError({"total_votes": "Debe ser entero"})
            if iv < 0:
                raise serializers.ValidationError({"total_votes": "Debe ser >= 0"})
        return data
