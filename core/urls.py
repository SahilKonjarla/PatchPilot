from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path("healthz/", views.healthz, name="healthz"),
    path("metrics/", views.metrics_view, name="metrics"),
    path("webhook/", views.webhook, name="webhook"),

]