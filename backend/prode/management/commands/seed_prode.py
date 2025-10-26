from django.core.management.base import BaseCommand
from django.utils import timezone
from prode.models import Prediction, OfficialResults
from prode.validators import get_fuerzas, get_provincias
import random


class Command(BaseCommand):
    help = "Borra datos y genera pronósticos y resultados oficiales simulados (para pruebas)."

    def add_arguments(self, parser):
        parser.add_argument('--players', type=int, default=50, help='Cantidad de jugadores a simular')
        parser.add_argument('--publish', action='store_true', help='Publicar resultados oficiales')

    def handle(self, *args, **options):
        players = int(options['players'])
        publish = bool(options['publish'])

        self.stdout.write(self.style.WARNING('Eliminando datos anteriores...'))
        Prediction.objects.all().delete()
        OfficialResults.objects.all().delete()

        fuerzas = sorted(get_fuerzas() or {"LLA","UxP","JxC","FIT","FP"})
        provincias = sorted(get_provincias() or {"Buenos Aires","CABA","Córdoba","Santa Fe"})

        # Resultados oficiales simulados
        nat_real = _random_percentages(fuerzas)
        participation = round(random.uniform(60, 80), 1)
        # margen 1-2 según top 2 del nacional
        sorted_nat = sorted(nat_real.items(), key=lambda kv: kv[1], reverse=True)
        margin_1_2 = round(abs(sorted_nat[0][1] - sorted_nat[1][1]), 1) if len(sorted_nat) >= 2 else 0.0
        bni = round(random.uniform(1, 4), 1)
        total_votes = random.randint(15_000_000, 26_000_000)

        provinciales = {}
        for prov in provincias:
            prov_pcts = _random_percentages(fuerzas)
            winner = max(prov_pcts.items(), key=lambda kv: kv[1])[0]
            provinciales[prov] = { 'percentages': prov_pcts, 'winner': winner }

        OfficialResults.objects.create(
            national_percentages=nat_real,
            participation=participation,
            margin_1_2=margin_1_2,
            blanco_nulo_impugnado=bni,
            total_votes=total_votes,
            provinciales=provinciales,
            is_published=publish,
            published_at=timezone.now() if publish else None,
        )

        # Jugadores simulados
        self.stdout.write(self.style.WARNING(f'Generando {players} jugadores...'))
        for i in range(players):
            username = f'Jugador {i+1:03d}'
            email = f'jugador{i+1:03d}@example.com'
            # ruido sobre el real (para que haya dispersión)
            nat_pred = { k: _clip(v + random.uniform(-5, 5)) for k, v in nat_real.items() }
            top3 = [k for k,_ in sorted(nat_pred.items(), key=lambda kv: kv[1], reverse=True)[:3]]
            participation_p = _clip(participation + random.uniform(-5, 5))
            margin_p = _clip(margin_1_2 + random.uniform(-3, 3))
            bni_p = _clip(bni + random.uniform(-1, 1))
            total_votes_p = int(total_votes * random.uniform(0.95, 1.05))

            provinciales_p = {}
            for prov, payload in provinciales.items():
                basep = payload['percentages']
                jitter = { k: _clip(v + random.uniform(-6, 6)) for k, v in basep.items() }
                win = max(jitter.items(), key=lambda kv: kv[1])[0]
                provinciales_p[prov] = { 'percentages': jitter, 'winner': win }

            Prediction.objects.create(
                username=username,
                email=email,
                top3=top3,
                national_percentages=nat_pred,
                participation=participation_p,
                margin_1_2=margin_p,
                blanco_nulo_impugnado=bni_p,
                total_votes=total_votes_p,
                provinciales=provinciales_p,
                bonus={},
            )

        self.stdout.write(self.style.SUCCESS('Seed completado.'))
        if publish:
            self.stdout.write(self.style.SUCCESS('Resultados oficiales publicados.'))


def _random_percentages(keys):
    weights = [random.uniform(5, 40) for _ in keys]
    s = sum(weights)
    return { k: round(100.0 * w / s, 1) for k, w in zip(keys, weights) }


def _clip(v):
    return round(max(0.0, min(100.0, float(v))), 1)
