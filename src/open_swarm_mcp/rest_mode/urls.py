from django.urls import path
from . import views

urlpatterns = [
    path('chat/completions', views.chat_completions, name='chat_completions'),
    path('models', views.list_models, name='list_models'),
]
