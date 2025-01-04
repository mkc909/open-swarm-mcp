from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from django.conf import settings
import os
from swarm import views

def favicon(request):
    favicon_path = os.path.join(settings.BASE_DIR, 'assets', 'images', 'favicon.ico')
    with open(favicon_path, 'rb') as f:
        favicon_data = f.read()
    return HttpResponse(favicon_data, content_type="image/x-icon")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('v1/chat/completions', views.chat_completions, name='chat_completions'),
    path('v1/models', views.list_models, name='list_models'),
    path('<str:blueprint_name>/', views.blueprint_webpage, name='blueprint_webpage'),
    path('favicon.ico', favicon, name='favicon'),
]
