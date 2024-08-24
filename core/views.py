from rest_framework import viewsets
from .models import ChatRoom, Message, UserChatActivity, ChatHistory
from .serializers import ChatRoomSerializer, MessageSerializer, UserChatActivitySerializer, ChatHistorySerializer
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist

class ChatRoomViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

class UserActivityViewSet(viewsets.ModelViewSet):
    queryset = UserChatActivity.objects.all()
    serializer_class = UserChatActivitySerializer

class ChatHistoryViewSet(viewsets.ModelViewSet):
    queryset = ChatHistory.objects.all()
    serializer_class = ChatHistorySerializer

def chat_room(request, room_name, user_id):
    return render(request, 'core/chat.html', {
        'room_name': room_name,
        'user_id': user_id
    })


def chat_history(request, room_name, user_id):
    try:
        # Fetch messages for the room and optionally filter by user_id
        messages = Message.objects.filter(room__name=room_name).order_by('timestamp')
        history = [{
            'username': msg.user.username,  # Assuming `user` is a ForeignKey to Django's User model
            'message': msg.content
        } for msg in messages]

        return JsonResponse({'history': history}, status=200)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Messages not found'}, status=404)
    except Exception as e:
        print(f"Error fetching chat history: {e}")
        return JsonResponse({'error': 'Internal Server Error'}, status=500)

