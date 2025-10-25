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
        try:
            p = Prediction.objects.get(email=email)
        except Prediction.DoesNotExist:
            return JsonResponse({'detail': 'no encontrado'}, status=404)
        return JsonResponse(PredictionSerializer(p).data)


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
