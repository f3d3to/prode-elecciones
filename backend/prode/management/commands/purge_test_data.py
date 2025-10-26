from django.core.management.base import BaseCommand
from django.db import transaction
from prode.models import Prediction, OfficialResults


class Command(BaseCommand):
    help = "Elimina UNICAMENTE datos de prueba sembrados (heurística segura)."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='No borrar, solo mostrar qué se borraría')
        parser.add_argument('--include-official', action='store_true', help='Incluir resultados oficiales sembrados de prueba (drafts)')
        parser.add_argument('--purge-all-official', action='store_true', help='[Peligroso] Eliminar TODOS los OfficialResults (incluye publicados)')
        parser.add_argument('--force', action='store_true', help='No pedir confirmación interactiva')

    def handle(self, *args, **options):
        dry = bool(options['dry_run'])
        include_official = bool(options['include_official'])
        purge_all_official = bool(options['purge_all_official'])
        force = bool(options['force'])

        # Regla 1: Predicciones cuyo email termina en @example.com (generadas por seed)
        q_email = Prediction.objects.filter(email__iendswith='@example.com')
        # Regla 2: Predicciones cuyo username matchea el patrón "Jugador ", usado en seed
        q_name = Prediction.objects.filter(username__istartswith='Jugador ')
        ids_email = set(q_email.values_list('id', flat=True))
        ids_name = set(q_name.values_list('id', flat=True))
        ids = sorted(ids_email.union(ids_name))

        self.stdout.write(self.style.WARNING(f"Predicciones de prueba detectadas: {len(ids)}"))
        if ids:
            for pk in ids[:10]:
                self.stdout.write(f" - Prediction id={pk}")
            if len(ids) > 10:
                self.stdout.write(f"   ... (+{len(ids) - 10} más)")

        # Resultados oficiales: opcionalmente borrar borradores sembrados (no publicados)
        off_qs = OfficialResults.objects.none()
        if purge_all_official:
            off_qs = OfficialResults.objects.all()
            self.stdout.write(self.style.ERROR(f"Se eliminarán TODOS los OfficialResults: {off_qs.count()}"))
        elif include_official:
            off_qs = OfficialResults.objects.filter(is_published=False)
            self.stdout.write(self.style.WARNING(f"Resultados oficiales (draft) a eliminar: {off_qs.count()}"))

        if dry:
            self.stdout.write(self.style.SUCCESS('Dry-run: no se eliminaron datos.'))
            return

        if not force:
            confirm = input('Confirmar eliminación de datos de PRUEBA? (yes/no): ').strip().lower()
            if confirm not in ('y', 'yes'):
                self.stdout.write(self.style.ERROR('Cancelado.'))
                return

        if purge_all_official and not force:
            confirm2 = input('CONFIRMAR ELIMINACIÓN DE TODOS LOS RESULTADOS OFICIALES? (type ALL): ').strip().upper()
            if confirm2 != 'ALL':
                self.stdout.write(self.style.ERROR('Cancelado.'))
                return

        with transaction.atomic():
            if ids:
                Prediction.objects.filter(id__in=ids).delete()
            if include_official or purge_all_official:
                off_qs.delete()

        self.stdout.write(self.style.SUCCESS('Purge completado (solo datos de prueba).'))
