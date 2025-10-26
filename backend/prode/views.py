import os
from django.http import JsonResponse, HttpResponseForbidden
from rest_framework.views import APIView
from rest_framework.request import Request
from .serializers import PredictionSerializer, OfficialResultsSerializer
from .models import Prediction, OfficialResults
from prode_backend import settings as app_settings
from .validators import (
    get_fuerzas,
    get_provincias,
    get_fuerzas_por_provincia,
    validate_national_fuerzas,
    validate_provinciales,
    validate_top3,
    validate_bonus,
)
from django.utils import timezone
from typing import Dict, Any, List
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.middleware.csrf import get_token
from django.http import HttpResponse
from django.db.models import Q
import csv
from django.core.management import call_command

MSG_WAIT_RESULTS = 'A la espera de resultados oficiales'
MSG_STAFF_ONLY = 'Solo staff'


class MetadataView(APIView):
    def get(self, request: Request):
        # Convertimos el mapa de sets a listas serializables
        fpp_raw = get_fuerzas_por_provincia()
        fpp = {prov: sorted(vals) for prov, vals in fpp_raw.items()}
        return JsonResponse({
            'fuerzas': sorted(get_fuerzas()),
            'provincias': sorted(get_provincias()),
            'fuerzas_por_provincia': fpp,
            'deadline': app_settings.DEADLINE,
        })


class PredictionMineView(APIView):
    def get(self, request: Request):
        email = request.GET.get('email')
        if not email:
            return JsonResponse({'detail': 'email requerido'}, status=400)
        email = email.strip().lower()
        soft = request.GET.get('soft')
        # Evitar 500 por duplicados: tomamos el último por updated_at
        try:
            p = (
                Prediction.objects.filter(email=email)
                .order_by('-updated_at')
                .first()
            )
        except Exception as e:
            # Log simple para Render
            print(f"PredictionMineView error querying email={email}: {type(e).__name__}: {e}")
            p = None
        if not p:
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

        # Normalizar nulos a estructuras vacías para evitar errores de tipo
        if data.get('provinciales') is None:
            data['provinciales'] = {}
        if data.get('bonus') is None:
            data['bonus'] = {}

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

        # Evitar 500 si hay duplicados históricos del mismo email: tomar el último actualizado
        inst = (
            Prediction.objects.filter(email=data.get('email'))
            .order_by('-updated_at')
            .first()
        )
        if inst is not None:
            serializer = PredictionSerializer(inst, data=data, partial=True)
        else:
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
        try:
            # MVP completion criterion: user completed Top-3 (3 fuerzas)
            # Completed = has any relevant content: top3, some national percentage > 0, or any provinciales filled
            names = []
            qs = Prediction.objects.order_by('-updated_at').only('username','top3','national_percentages','provinciales')
            for p in qs.iterator():
                try:
                    if not p.username:
                        continue
                    t3 = p.top3 or []
                    nat = p.national_percentages or {}
                    prov = p.provinciales or {}
                    nat_sum = 0.0
                    try:
                        nat_sum = sum(float(v) for v in getattr(nat, 'values', lambda: [])()) if nat else 0.0
                    except Exception:
                        nat_sum = 0.0
                    if (len(t3) > 0) or (nat_sum > 0) or (bool(prov)):
                        names.append(p.username)
                except Exception as row_err:
                    # Evitar que un registro corrupto rompa el listado completo
                    print(f"PlayersView row error id={getattr(p, 'id', None)}: {type(row_err).__name__}: {row_err}")
                    continue
            total = Prediction.objects.count()
            return JsonResponse({'count_completed': len(names), 'usernames': names, 'count_total': total})
        except Exception as e:
            # Fallback seguro ante cualquier error no esperado
            print(f"PlayersView failed: {type(e).__name__}: {e}")
            try:
                total = Prediction.objects.count()
            except Exception:
                total = 0
            return JsonResponse({'count_completed': 0, 'usernames': [], 'count_total': total})


class OfficialResultsView(APIView):
    """
    GET: público, devuelve el último resultado oficial publicado.
    POST: solo staff, crea una nueva publicación de resultados.
    """

    def get(self, request: Request):
        """Devuelve 200 siempre; si no hay resultados publicados, responde
        un payload vacío para evitar errores en consola del browser.
        """
        try:
            obj = (
                OfficialResults.objects.filter(is_published=True)
                .order_by('-published_at', '-created_at')
                .first()
            )
            if not obj:
                return JsonResponse({
                    'national_percentages': {},
                    'participation': None,
                    'margin_1_2': None,
                    'blanco_nulo_impugnado': None,
                    'total_votes': None,
                    'provinciales': {},
                    'detail': MSG_WAIT_RESULTS,
                })
            return JsonResponse(OfficialResultsSerializer(obj).data)
        except Exception as e:
            # En producción preferimos respuesta controlada sin stacktrace
            print(f"OfficialResultsView get failed: {type(e).__name__}: {e}")
            return JsonResponse({
                'national_percentages': {},
                'participation': None,
                'margin_1_2': None,
                'blanco_nulo_impugnado': None,
                'total_votes': None,
                'provinciales': {},
                'detail': MSG_WAIT_RESULTS,
            })

    def post(self, request: Request):
        # Requiere sesión de staff
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False) or not getattr(user, 'is_staff', False):
            return HttpResponseForbidden(MSG_STAFF_ONLY)

        data = request.data.copy()
        serializer = OfficialResultsSerializer(data=data)
        if serializer.is_valid():
            obj = serializer.save()
            # Si se marca publicado y no hay timestamp, lo fijamos ahora
            if obj.is_published and obj.published_at is None:
                obj.published_at = timezone.now()
                obj.save(update_fields=['published_at'])

            # Nota: aquí podría gatillarse el proceso de scoring y la sincronización con Sheets.
            return JsonResponse(OfficialResultsSerializer(obj).data, status=201)
        return JsonResponse(serializer.errors, status=400)


class RankingView(APIView):
    """Ranking público calculado on-the-fly a partir del último resultado publicado.

    Params:
      - q: filtro por nombre o email (icontains)
    """

    def get(self, request: Request):
        """Devuelve 200 siempre. Si no hay resultados publicados, responde una
        estructura vacía para evitar errores visibles en consola del browser.
        """
        try:
            res = (
                OfficialResults.objects.filter(is_published=True)
                .order_by('-published_at', '-created_at')
                .first()
            )

            # Si no hay resultados, respondemos 200 con lista vacía
            if not res:
                return JsonResponse({
                    'count': 0,
                    'generated_at': timezone.now().isoformat(),
                    'results': [],
                    'detail': MSG_WAIT_RESULTS,
                })

            q = (request.GET.get('q') or '').strip()
            qs = Prediction.objects.all().only('username','email','top3','national_percentages','participation','margin_1_2','updated_at')
            if q:
                qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))

            items: List[Dict[str, Any]] = []
            for p in qs.iterator():
                try:
                    scored = _score_prediction(p, res)
                    items.append({
                        'username': p.username,
                        'email': p.email,
                        'score': scored['score'],
                        'bonus': scored['bonus'],
                        'medals': scored['medals'],
                        'breakdown': scored['breakdown'],
                        'submitted_at': p.updated_at.isoformat(),
                    })
                except Exception as row_err:
                    print(f"RankingView row error id={getattr(p, 'id', None)}: {type(row_err).__name__}: {row_err}")
                    continue

            # Ordenamos por score desc y por fecha de envío asc (tie-breaker)
            items.sort(key=lambda x: (-x['score'], x['submitted_at']))
            for idx, it in enumerate(items, start=1):
                it['position'] = idx

            return JsonResponse({
                'count': len(items),
                'generated_at': timezone.now().isoformat(),
                'results': items,
            })
        except Exception as e:
            # Fallback seguro: 200 con lista vacía
            print(f"RankingView failed: {type(e).__name__}: {e}")
            return JsonResponse({
                'count': 0,
                'generated_at': timezone.now().isoformat(),
                'results': [],
                'detail': MSG_WAIT_RESULTS,
            })


def _score_prediction(p: Prediction, res: OfficialResults) -> Dict[str, Any]:
    nat_real = res.national_percentages or {}
    mae_nat = _mae_national(p, nat_real)
    part_err = _abs_error(p.participation, res.participation)
    margin_err = _abs_error(p.margin_1_2, res.margin_1_2)
    top3_points = _top3_points(p.top3 or [], nat_real)
    top3_err = 30.0 - top3_points

    err = (mae_nat * 0.5) + (part_err * 0.25) + (margin_err * 0.25) + (top3_err * (2.0/3.0))
    score = round(max(0.0, 100.0 - err), 2)

    return {
        'score': score,
        'bonus': 0,
        'medals': [],
        'breakdown': {
            'mae_national': round(mae_nat, 2),
            'participation_error': round(part_err, 2),
            'margin_error': round(margin_err, 2),
            'top3_points': round(top3_points, 2),
        }
    }


def _mae_national(p: Prediction, nat_real: Dict[str, Any]) -> float:
    forces = list(nat_real.keys())
    if not forces:
        return 0.0
    abs_sum = 0.0
    preds = p.national_percentages or {}
    for f in forces:
        pred_v = _to_float_or_zero(preds.get(f, 0))
        real_v = _to_float_or_zero(nat_real.get(f, 0))
        abs_sum += abs(pred_v - real_v)
    return abs_sum / len(forces)


def _to_float_or_zero(x: Any) -> float:
    try:
        return float(x or 0)
    except Exception:
        return 0.0


def _abs_error(pred: Any, real: Any) -> float:
    try:
        r = float(real)
    except Exception:
        return 0.0
    try:
        p = float(pred)
    except Exception:
        p = 100.0
    return abs(p - r)


def _top3_points(predicted_top3: List[str], nat_real: Dict[str, Any]) -> float:
    official_sorted = sorted(nat_real.items(), key=lambda kv: _to_float_or_zero(kv[1]), reverse=True)
    official_top3 = [k for k, _ in official_sorted[:3]]
    points = 0.0
    for i in range(min(3, len(predicted_top3))):
        f = predicted_top3[i]
        if i < len(official_top3) and f == official_top3[i]:
            points += 10.0
        elif f in official_top3:
            points += 5.0
    return points


class AdminCsrfView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request):
        token = get_token(request)
        resp = JsonResponse({'csrfToken': token})
        # Seteamos cookie CSRF para uso por el frontend (SameSite=Lax apropiado para dev)
        resp.set_cookie('csrftoken', token, samesite='Lax')
        return resp


class AdminLoginView(APIView):
    def get(self, request: Request):
        user = getattr(request, 'user', None)
        if getattr(user, 'is_authenticated', False) and getattr(user, 'is_staff', False):
            return JsonResponse({'authenticated': True, 'username': user.username, 'is_staff': True})
        return JsonResponse({'authenticated': False}, status=403)

    def post(self, request: Request):
        username = (request.data.get('username') or '').strip()
        password = (request.data.get('password') or '')
        user = authenticate(request, username=username, password=password)
        if user is None or not user.is_staff:
            return JsonResponse({'detail': 'Credenciales inválidas o sin permisos'}, status=403)
        auth_login(request, user)
        return JsonResponse({'authenticated': True, 'username': user.username, 'is_staff': True})


class AdminLogoutView(APIView):
    def post(self, request: Request):
        auth_logout(request)
        return JsonResponse({'ok': True})


class AdminOverviewView(APIView):
    def get(self, request: Request):
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False) or not getattr(user, 'is_staff', False):
            return HttpResponseForbidden(MSG_STAFF_ONLY)

        res = (
            OfficialResults.objects.filter(is_published=True)
            .order_by('-published_at', '-created_at')
            .first()
        )
        predictions = Prediction.objects.count()
        completed = Prediction.objects.exclude(username='').count()
        overview = {
            'deadline': app_settings.DEADLINE,
            'after_deadline': app_settings.is_after_deadline(),
            'predictions_total': predictions,
            'predictions_completed': completed,
            'results_published': bool(res),
            'results_published_at': res.published_at.isoformat() if res and res.published_at else None,
        }
        return JsonResponse(overview)


class AdminReprocessView(APIView):
    def post(self, request: Request):
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False) or not getattr(user, 'is_staff', False):
            return HttpResponseForbidden(MSG_STAFF_ONLY)
        # En este MVP el ranking se calcula on-the-fly; devolvemos un resumen
        count = Prediction.objects.count()
        return JsonResponse({'reprocessed': True, 'predictions_count': count, 'at': timezone.now().isoformat()})


class AdminExportRankingCsvView(APIView):
    def get(self, request: Request):
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False) or not getattr(user, 'is_staff', False):
            return HttpResponseForbidden('Solo staff')

        res = (
            OfficialResults.objects.filter(is_published=True)
            .order_by('-published_at', '-created_at')
            .first()
        )
        if not res:
            return JsonResponse({'detail': MSG_WAIT_RESULTS}, status=404)

        rows = []
        for p in Prediction.objects.all().only('username','email','top3','national_percentages','participation','margin_1_2','updated_at'):
            s = _score_prediction(p, res)
            rows.append({
                'username': p.username,
                'email': p.email,
                'score': s['score'],
                'bonus': s['bonus'],
                'submitted_at': p.updated_at.isoformat(),
            })
        rows.sort(key=lambda x: (-x['score'], x['submitted_at']))
        # Construir CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ranking.csv"'
        writer = csv.writer(response)
        writer.writerow(['posicion','usuario','email','puntaje','bonus','enviado'])
        for i, r in enumerate(rows, start=1):
            writer.writerow([i, r['username'], r['email'], r['score'], r['bonus'], r['submitted_at']])
        return response


class AdminRetrySheetsView(APIView):
    def post(self, request: Request):
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False) or not getattr(user, 'is_staff', False):
            return HttpResponseForbidden(MSG_STAFF_ONLY)
        # No implementado en este MVP
        return JsonResponse({'detail': 'Sheets no configurado'}, status=501)


class AdminPurgeTestDataView(APIView):
    def post(self, request: Request):
        """Borra datos de PRUEBA de manera segura (sin costo extra en Render,
        ejecutando en el mismo proceso web). Requiere sesión staff.

        Body JSON opcional:
          - dry_run: bool (default false)
          - include_official: bool (default false)
          - purge_all_official: bool (default false) [PELIGRO]
        """
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False) or not getattr(user, 'is_staff', False):
            return HttpResponseForbidden(MSG_STAFF_ONLY)

        dry = bool(request.data.get('dry_run'))
        include_official = bool(request.data.get('include_official'))
        purge_all_official = bool(request.data.get('purge_all_official'))

        # Ejecutamos el management command directamente.
        # Usamos --force para saltar confirmaciones interactivas.
        buf = []
        try:
            call_command(
                'purge_test_data',
                dry_run=dry,
                include_official=include_official,
                purge_all_official=purge_all_official,
                force=True,
                stdout=type('ListWriter', (), {'write': lambda self, s: buf.append(str(s))})(),
            )
            out = ''.join(buf)
            return JsonResponse({'ok': True, 'dry_run': dry, 'include_official': include_official, 'purge_all_official': purge_all_official, 'output': out})
        except Exception as e:
            return JsonResponse({'ok': False, 'detail': f'Error en purge: {type(e).__name__}: {e}'}, status=500)


class AdminPredictionsView(APIView):
    """Listado y borrado selectivo de predicciones para staff.

    GET params:
      - q: filtro por username/email (icontains)
      - limit: int (default 50, máx 200)

    DELETE body JSON:
      - ids: lista de IDs a eliminar
    """

    def get(self, request: Request):
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False) or not getattr(user, 'is_staff', False):
            return HttpResponseForbidden(MSG_STAFF_ONLY)
        q = (request.GET.get('q') or '').strip()
        try:
            limit = min(max(int(request.GET.get('limit') or '50'), 1), 200)
        except Exception:
            limit = 50
        qs = Prediction.objects.all().order_by('-updated_at')
        if q:
            qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))
        rows = []
        for p in qs[:limit]:
            rows.append({
                'id': p.id,
                'username': p.username,
                'email': p.email,
                'updated_at': p.updated_at.isoformat(),
            })
        total = Prediction.objects.count()
        return JsonResponse({'results': rows, 'count': len(rows), 'total': total})

    def delete(self, request: Request):
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False) or not getattr(user, 'is_staff', False):
            return HttpResponseForbidden(MSG_STAFF_ONLY)
        ids = request.data.get('ids') if isinstance(request.data, dict) else None
        if not isinstance(ids, list) or not ids:
            return JsonResponse({'detail': 'ids requerido (lista)'}, status=400)
        try:
            n, _ = Prediction.objects.filter(id__in=ids).delete()
            return JsonResponse({'deleted': n})
        except Exception as e:
            return JsonResponse({'detail': f'No se pudo eliminar: {type(e).__name__}: {e}'}, status=400)


class AdminOfficialResultsView(APIView):
    """Listado y borrado de resultados oficiales. Solo se puede borrar drafts."""

    def get(self, request: Request):
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False) or not getattr(user, 'is_staff', False):
            return HttpResponseForbidden(MSG_STAFF_ONLY)
        qs = OfficialResults.objects.all().order_by('-published_at', '-created_at')
        rows = []
        for r in qs[:200]:
            rows.append({
                'id': r.id,
                'is_published': r.is_published,
                'published_at': r.published_at.isoformat() if r.published_at else None,
                'created_at': r.created_at.isoformat(),
            })
        return JsonResponse({'results': rows, 'count': len(rows)})

    def delete(self, request: Request):
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False) or not getattr(user, 'is_staff', False):
            return HttpResponseForbidden(MSG_STAFF_ONLY)
        rid = request.data.get('id') if isinstance(request.data, dict) else None
        if not rid:
            return JsonResponse({'detail': 'id requerido'}, status=400)
        try:
            obj = OfficialResults.objects.get(id=rid)
            if obj.is_published:
                return JsonResponse({'detail': 'No se puede borrar un resultado publicado'}, status=400)
            obj.delete()
            return JsonResponse({'deleted': 1})
        except OfficialResults.DoesNotExist:
            return JsonResponse({'detail': 'No encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'detail': f'No se pudo eliminar: {type(e).__name__}: {e}'}, status=400)
