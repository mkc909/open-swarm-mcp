from django.contrib import admin
from django.urls import path, re_path, include
from django.http import HttpResponse
from django.conf import settings
import os
from swarm import views
from swarm import consumers

def favicon(request):
    favicon_path = os.path.join(settings.BASE_DIR, 'assets', 'images', 'favicon.ico')
    with open(favicon_path, 'rb') as f:
        favicon_data = f.read()
    return HttpResponse(favicon_data, content_type="image/x-icon")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('v1/chat/completions', views.chat_completions, name='chat_completions'),
    path('v1/models/', views.list_models, name='list_models'),
    path('django_chat/', views.IndexView.as_view(), name='django_chat_index'),
    path('django_chat/start/', views.StartConversationView.as_view(), name='django_chat_start'),
    path('django_chat/<str:conversation_id>/', views.ChatView.as_view(), name='chat_page'),
    re_path(r'ws/django_chat/(?P<conversation_id>[0-9a-fA-F-]+)/$', consumers.DjangoChatConsumer.as_asgi(), name="ws_django_chat"),
    path('favicon.ico', favicon, name='favicon'),
    path('accounts/', include('allauth.urls')),
    path('config/swarm_config.json', views.serve_swarm_config, name='serve_swarm_config'),
    path('<str:blueprint_name>', views.blueprint_webpage, name='blueprint_webpage'),
]