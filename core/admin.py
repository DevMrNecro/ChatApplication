from django.contrib import admin
from .models import ChatRoom, Message, UserChatActivity, ChatHistory, MessageQueue

admin.site.register(ChatRoom)
admin.site.register(Message)
admin.site.register(UserChatActivity)
admin.site.register(ChatHistory)
admin.site.register(MessageQueue)



