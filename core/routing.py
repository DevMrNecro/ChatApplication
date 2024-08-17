# core/routing.py
from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/<int:user_id>/', consumers.ChatConsumer.as_asgi()),
]
