from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
import os

from swarm import views
from swarm.views import HiddenSpectacularAPIView, ChatMessageViewSet
from drf_spectacular.views import SpectacularSwaggerView  # type: ignore
from rest_framework.routers import DefaultRouter  # type: ignore

def favicon(request):
    favicon_path = os.path.join(settings.BASE_DIR, 'assets', 'images', 'favicon.ico')
    with open(favicon_path, 'rb') as f:
        favicon_data = f.read()
    return HttpResponse(favicon_data, content_type="image/x-icon")

ENABLE_ADMIN = os.getenv("ENABLE_ADMIN", "false").lower() in ("true", "1", "t")
ENABLE_WEBUI = os.getenv("ENABLE_WEBUI", "false").lower() in ("true", "1", "t")

router = DefaultRouter()
router.register(r'v1/chat/messages', ChatMessageViewSet, basename='chatmessage')

urlpatterns = [
    re_path(r'^v1/chat/completions/?$', views.chat_completions, name='chat_completions'),
    re_path(r'^v1/models/?$', views.list_models, name='list_models'),
    path('schema/', HiddenSpectacularAPIView.as_view(), name='schema'),
    path('swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
] + router.urls

if ENABLE_ADMIN:
    urlpatterns += [path('admin/', admin.site.urls)]
if ENABLE_WEBUI:
    urlpatterns += [
        path('favicon.ico', favicon, name='favicon'),
        path('config/swarm_config.json', views.serve_swarm_config, name='serve_swarm_config'),
        path('<str:blueprint_name>', views.blueprint_webpage, name='blueprint_webpage'),
        path('', views.chatbot, name='chatbot'),
    ]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
