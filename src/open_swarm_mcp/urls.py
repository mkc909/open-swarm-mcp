"""open_swarm_mcp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path
from .rest_mode import views

urlpatterns = [
    # Admin route
    path('admin/', admin.site.urls),

    # API-style routes
    path('v1/chat/completions', views.chat_completions, name='chat_completions'),
    path('v1/models', views.list_models, name='list_models'),

    # Blueprint routes
    path('<str:blueprint_name>/', views.blueprint_webpage, name='blueprint_webpage'),
]
