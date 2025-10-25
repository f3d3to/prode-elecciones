import os
from django.http import JsonResponse, HttpResponseForbidden
from rest_framework.views import APIView
from rest_framework.request import Request
from .serializers import PredictionSerializer
from .models import Prediction
from prode_backend import settings as app_settings
from .validators import (
    get_fuerzas,
    get_provincias,
    validate_national_fuerzas,
    validate_provinciales,
    validate_top3,
    validate_bonus,
)


class MetadataView(APIView):
    def get(self, request: Request):
        return JsonResponse({
            'fuerzas': sorted(get_fuerzas()),
            'provincias': sorted(get_provincias()),
            'deadline': app_settings.DEADLINE,
        })


class PredictionMineView(APIView):
    def get(self, request: Request):
        email = request.GET.get('email')
        if not email:
            return JsonResponse({'detail': 'email requerido'}, status=400)
        email = email.strip().lower()
        soft = request.GET.get('soft')
        try:
            p = Prediction.objects.get(email=email)
        except Prediction.DoesNotExist:
            if soft:
                return JsonResponse({'exists': False, 'prediction': None})
            return JsonResponse({'detail': 'no encontrado'}, status=404)
        data = PredictionSerializer(p).data
        if soft:
            return JsonResponse({'exists': True, 'prediction': data})
        return JsonResponse(data)


class PredictionUpsertView(APIView):
    def post(self, request: Request):
        if app_settings.is_after_deadline():
            return HttpResponseForbidden('Elecciones finalizadas')

        data = request.data.copy()
        if 'email' in data and isinstance(data['email'], str):
            data['email'] = data['email'].strip().lower()

        fuerzas = get_fuerzas()
        provincias = get_provincias()

        err = validate_national_fuerzas(data.get('national_percentages') or {}, fuerzas)
        if err:
            return JsonResponse({'national_percentages': err}, status=400)

        err = validate_provinciales(data.get('provinciales') or {}, provincias, fuerzas)
        if err:
            return JsonResponse({'provinciales': err}, status=400)

        err = validate_top3(data.get('top3'), fuerzas)
        if err:
            return JsonResponse({'top3': err}, status=400)

        err = validate_bonus(data.get('bonus') or {}, provincias)
        if err:
            return JsonResponse({'bonus': err}, status=400)

        try:
            inst = Prediction.objects.get(email=data.get('email'))
            serializer = PredictionSerializer(inst, data=data, partial=True)
        except Prediction.DoesNotExist:
            serializer = PredictionSerializer(data=data)

        if serializer.is_valid():
            obj = serializer.save()
            return JsonResponse(PredictionSerializer(obj).data, status=201)
        return JsonResponse(serializer.errors, status=400)


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request):
        # Minimal health: app up, db reachable
        try:
            _ = Prediction.objects.count()
            db = 'ok'
        except Exception as e:
            db = f'error: {type(e).__name__}'
        return JsonResponse({
            'status': 'ok',
            'db': db,
            'deadline': app_settings.DEADLINE,
        })


class PlayersView(APIView):
    def get(self, request: Request):
        # MVP completion criterion: user completed Top-3 (3 fuerzas)
        # Completed = has any relevant content: top3, some national percentage > 0, or any provinciales filled
        names = []
        for p in Prediction.objects.order_by('-updated_at').only('username','top3','national_percentages','provinciales'):
            if not p.username:
                continue
            t3 = p.top3 or []
            nat = p.national_percentages or {}
            prov = p.provinciales or {}
            nat_sum = 0.0
            try:
                nat_sum = sum(float(v) for v in nat.values()) if nat else 0.0
            except Exception:
                nat_sum = 0.0
            if (len(t3) > 0) or (nat_sum > 0) or (bool(prov)):
                names.append(p.username)
        total = Prediction.objects.count()
        return JsonResponse({'count_completed': len(names), 'usernames': names, 'count_total': total})
