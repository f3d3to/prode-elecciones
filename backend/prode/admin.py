from django.contrib import admin
from .models import Prediction

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("username","email","created_at","updated_at","sync_pending")
    search_fields = ("username","email")
