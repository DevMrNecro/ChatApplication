from rest_framework import serializers
from .models import ChatRoom, Message, UserChatActivity, ChatHistory

class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'

class UserChatActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserChatActivity
        fields = '__all__'

class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = '__all__'