from django.urls import path
from .views import (
    MetadataView, PredictionMineView, PredictionUpsertView, HealthView, PlayersView,
    OfficialResultsView, RankingView,
    AdminCsrfView, AdminLoginView, AdminLogoutView, AdminOverviewView, AdminReprocessView, AdminExportRankingCsvView, AdminRetrySheetsView,
)

urlpatterns = [
    path('metadata', MetadataView.as_view()),
    path('health', HealthView.as_view()),
    path('players', PlayersView.as_view()),
    path('results', OfficialResultsView.as_view()),
    path('predictions/mine', PredictionMineView.as_view()),
    path('predictions', PredictionUpsertView.as_view()),
    path('ranking', RankingView.as_view()),
    # Admin (no enlazado en UI pública)
    path('admin/csrf', AdminCsrfView.as_view()),
    path('admin/login', AdminLoginView.as_view()),
    path('admin/logout', AdminLogoutView.as_view()),
    path('admin/overview', AdminOverviewView.as_view()),
    path('admin/reprocess', AdminReprocessView.as_view()),
    path('admin/export/ranking.csv', AdminExportRankingCsvView.as_view()),
    path('admin/retry-sheets', AdminRetrySheetsView.as_view()),
]
