"""open_swarm_mcp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from django.conf import settings
import os
from .rest_mode import views

def favicon(request):
    # Path to the favicon file
    favicon_path = os.path.join(settings.BASE_DIR, 'assets', 'images', 'favicon.ico')
    
    # Open the file and read its contents
    with open(favicon_path, 'rb') as f:
        favicon_data = f.read()
    
    # Return the favicon data with the appropriate content type
    return HttpResponse(favicon_data, content_type="image/x-icon")

urlpatterns = [
    # Admin route
    path('admin/', admin.site.urls),

    # API-style routes
    path('v1/chat/completions', views.chat_completions, name='chat_completions'),
    path('v1/models', views.list_models, name='list_models'),

    # Blueprint routes
    path('<str:blueprint_name>/', views.blueprint_webpage, name='blueprint_webpage'),

    # Favicon route
    path('favicon.ico', favicon, name='favicon'),
]
