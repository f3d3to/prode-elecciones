from django.db import models

class Prediction(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    username = models.CharField(max_length=120)
    email = models.EmailField(unique=True)

    # Simplified national fields for MVP
    top3 = models.JSONField(default=list)  # ["LLA","UxP","JxC"]
    national_percentages = models.JSONField(default=dict)  # {force: percent}
    participation = models.FloatField(null=True, blank=True)
    margin_1_2 = models.FloatField(null=True, blank=True)
    blanco_nulo_impugnado = models.FloatField(null=True, blank=True)
    total_votes = models.BigIntegerField(null=True, blank=True)

    # Simplified provincial predictions MVP (map province -> {force: percent, winner})
    provinciales = models.JSONField(default=dict)

    # Bonus
    bonus = models.JSONField(default=dict)

    sync_pending = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} <{self.email}>"


class OfficialResults(models.Model):
    """Resultados oficiales publicados por staff.

    Modelo simple y único por publicación; el GET usará el último cargado.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Nacional
    national_percentages = models.JSONField(default=dict)  # {force: percent}
    participation = models.FloatField(null=True, blank=True)
    margin_1_2 = models.FloatField(null=True, blank=True)
    blanco_nulo_impugnado = models.FloatField(null=True, blank=True)
    total_votes = models.BigIntegerField(null=True, blank=True)

    # Provinciales: {provincia: {percentages: {force: percent}, winner: force}}
    provinciales = models.JSONField(default=dict)

    is_published = models.BooleanField(default=False)

    def __str__(self):
        stamp = self.published_at.isoformat() if self.published_at else "draft"
        return f"OfficialResults({stamp})"
