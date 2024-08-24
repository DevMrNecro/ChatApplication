from django.db import models
from django.contrib.auth.models import User

class ChatRoom(models.Model):
    name = models.CharField(max_length=255, unique=True)
    users = models.ManyToManyField(User, related_name='chat_rooms', blank=True)  # M2M relationship

    def __str__(self):
        return self.name

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.content[:50]}'

class UserChatActivity(models.Model): #deprecated
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    last_joined_time = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'chat_room')

    def __str__(self):
        return f'{self.user.username} - {self.chat_room.name}'
    

class ChatHistory(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    history = models.JSONField(default=list)  # Stores chat history as a JSON array
    last_updated = models.DateTimeField(auto_now=True)  # Track the last time the history was updated

    def __str__(self):
        return f'{self.user.username} - {self.chat_room.name}'
    

class MessageQueue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    delivered = models.BooleanField(default=False)  # Indicates whether the message has been delivered

    def __str__(self):
        return f'{self.user.username} - {self.room.name} - {self.message.content[:50]}'