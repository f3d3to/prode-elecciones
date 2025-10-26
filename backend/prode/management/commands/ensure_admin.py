from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Crea/actualiza un usuario admin (is_staff/is_superuser) con la contraseña indicada."

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--password', required=True)

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        user_model = get_user_model()
        user, _created = user_model.objects.get_or_create(username=username, defaults={'is_staff': True, 'is_superuser': True})
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Usuario admin '{username}' listo."))
