from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, MessageViewSet, chat_room, chat_history


router = DefaultRouter()
router.register(r'chatrooms', ChatRoomViewSet)
router.register(r'messages', MessageViewSet)

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('chat/<str:room_name>/<int:user_id>/', chat_room, name='chat_room'),
    path('chat_history/<str:room_name>/<int:user_id>/', chat_history, name='chat_history'),
    path('', include(router.urls)),
]

