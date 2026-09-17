from django.urls import path
from . import views

urlpatterns = [
    path('auth/register/', views.register),
    path('auth/login/', views.login),
    path('overview/', views.overview),
    path('markets/', views.markets),
    path('commodities/', views.commodities),
    path('prices/', views.prices),
    path('prices/submit/', views.submit_price),
    path('forecasts/', views.forecasts),
    path('recommendations/', views.recommendations),
    path('alerts/', views.alerts),
    path('alerts/<int:alert_id>/read/', views.mark_alert_read),
    path('alerts/read-all/', views.mark_all_alerts_read),
    path('reports/', views.report),
    path('ussd/', views.ussd),
]
