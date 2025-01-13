"""
Local version of urls.py that uses views_local
"""
from django.urls import path
from django.views.generic import RedirectView
from . import views_local

urlpatterns = [
    path("", RedirectView.as_view(url="/university/", permanent=False)),
    path("v1/chat/completions", views_local.chat_completions, name="chat_completions"),
    path("v1/models", views_local.list_models, name="list_models"),
    path("<str:blueprint_name>/", views_local.blueprint_webpage, name="blueprint_page"),
]
