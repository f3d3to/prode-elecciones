from django.urls import path
from .views import MetadataView, PredictionMineView, PredictionUpsertView, HealthView

urlpatterns = [
    path('metadata', MetadataView.as_view()),
    path('health', HealthView.as_view()),
    path('predictions/mine', PredictionMineView.as_view()),
    path('predictions', PredictionUpsertView.as_view()),
]
