from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
import os
from swarm import views

# Function to serve favicon
def favicon(request):
    favicon_path = os.path.join(settings.BASE_DIR, 'assets', 'images', 'favicon.ico')
    with open(favicon_path, 'rb') as f:
        favicon_data = f.read()
    return HttpResponse(favicon_data, content_type="image/x-icon")

# Check environment variables for route enabling
ENABLE_ADMIN = os.getenv("ENABLE_ADMIN", "false").lower() in ("true", "1", "t")
ENABLE_WEBUI = os.getenv("ENABLE_WEBUI", "false").lower() in ("true", "1", "t")

# Always available API endpoints
urlpatterns = [
    re_path(r'^v1/chat/completions/?$', views.chat_completions, name='chat_completions'),
    re_path(r'^v1/models/?$', views.list_models, name='list_models'),
]

# Enable /admin/ if ENABLE_ADMIN is set
if ENABLE_ADMIN:
    urlpatterns += [path('admin/', admin.site.urls)]

# Enable Web UI routes if ENABLE_WEBUI is set
if ENABLE_WEBUI:
    urlpatterns += [
        path('favicon.ico', favicon, name='favicon'),
        path('config/swarm_config.json', views.serve_swarm_config, name='serve_swarm_config'),
        path('<str:blueprint_name>', views.blueprint_webpage, name='blueprint_webpage'),
        path('', views.chatbot, name="chatbot"),
    ]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

