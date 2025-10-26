from typing import Optional, Tuple
from django.contrib.auth import get_user_model
from django.core import signing
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

# Salt compartida para firmar/verificar tokens del admin
ADMIN_TOKEN_SALT = 'prode-admin-token'


class AdminBearerAuthentication(BaseAuthentication):
    """Autenticación por token Bearer firmada con django.core.signing.

    - Espera un encabezado Authorization: Bearer <token>
    - El token contiene un payload JSON con:
        {"u": <username>, "s": true, "iat": <ts>, "exp": <ts>}
    - Verifica firma, expiración y que el usuario siga siendo staff.
    """

    keyword = 'Bearer'

    def authenticate(self, request) -> Optional[Tuple[object, None]]:
        header = request.META.get('HTTP_AUTHORIZATION') or request.headers.get('Authorization')
        if not header or not header.startswith(self.keyword + ' '):
            return None
        token = header.split(' ', 1)[1].strip()
        try:
            payload = signing.loads(token, salt=ADMIN_TOKEN_SALT)
        except Exception:
            raise exceptions.AuthenticationFailed('Invalid token')

        exp = payload.get('exp')
        username = payload.get('u')
        if not exp or not username:
            raise exceptions.AuthenticationFailed('Invalid token payload')
        now_ts = int(timezone.now().timestamp())
        try:
            if int(exp) < now_ts:
                raise exceptions.AuthenticationFailed('Token expired')
        except Exception:
            raise exceptions.AuthenticationFailed('Invalid token exp')

        user_model = get_user_model()
        try:
            user = user_model.objects.get(username=username)
        except user_model.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')
        if not getattr(user, 'is_staff', False):
            raise exceptions.AuthenticationFailed('Not staff')
        return (user, None)
