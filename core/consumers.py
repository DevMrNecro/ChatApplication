import json
import os
import redis
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis_client = self.get_redis_client()

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user_id = self.scope['url_route']['kwargs'].get('user_id')

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        if self.user_id:
            # Mark user as connected in Redis
            await self.mark_user_connected(self.user_id)

            # Send the user the chat history upon connection
            room = await self.get_room(self.room_name)
            chat_history = await self.get_chat_history(room, self.user_id)
            await self.send(text_data=json.dumps({
                'type': 'chat_history',
                'history': chat_history
            }))

            # Deliver queued messages
            await self.deliver_queued_messages(self.user_id)

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        if self.user_id:
            # Mark user as disconnected in Redis
            await self.mark_user_disconnected(self.user_id)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')

        try:
            user = await self.get_user(self.user_id)
            username = user.username if user else 'Anonymous'
            
            room = await self.get_room(self.room_name)
            if user:
                # Save the message to the database
                await self.create_message(user, room, message)

                is_connected = await self.is_user_connected(self.user_id)

                if not is_connected:
                    # Queue the message for disconnected users
                    await self.queue_message(user.id, room.id, message)
                else:
                    # Send the message to the room group
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': message,
                            'username': username
                        }
                    )
        except ObjectDoesNotExist:
            await self.send(text_data=json.dumps({'error': 'Room does not exist'}))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username']
        }))

    @database_sync_to_async
    def get_room(self, room_name):
        from .models import ChatRoom
        try:
            return ChatRoom.objects.get(name=room_name)
        except ChatRoom.DoesNotExist:
            raise ObjectDoesNotExist

    @database_sync_to_async
    def get_user(self, user_id):
        from django.contrib.auth.models import User
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def create_message(self, user, room, content):
        from .models import Message
        if user:
            return Message.objects.create(user=user, room=room, content=content)
        return None

    @database_sync_to_async
    def get_chat_history(self, room, user_id):
        from .models import ChatHistory
        try:
            chat_history = ChatHistory.objects.get(chat_room=room, user_id=user_id)
            history = json.loads(chat_history.history) if isinstance(chat_history.history, str) else chat_history.history
            print(f"Retrieved chat history for user {user_id}: {history}")
            return history
        except ChatHistory.DoesNotExist:
            print(f"No chat history found for user {user_id}")
            return []

    def get_redis_client(self):
        return redis.Redis(
            host=os.getenv('CHANNEL_LAYERS_HOST', 'redis'),
            port=int(os.getenv('CHANNEL_LAYERS_PORT', 6379))
        )

    async def mark_user_connected(self, user_id):
        self.redis_client.set(f'user:{user_id}:connected', 1)

    async def mark_user_disconnected(self, user_id):
        self.redis_client.delete(f'user:{user_id}:connected')

    async def is_user_connected(self, user_id):
        return self.redis_client.exists(f'user:{user_id}:connected')

    async def queue_message(self, user_id, room_id, message):
        self.redis_client.rpush(f'user:{user_id}:queue', json.dumps({'room_id': room_id, 'message': message}))

    async def deliver_queued_messages(self, user_id):
        while self.redis_client.llen(f'user:{user_id}:queue') > 0:
            message_data = json.loads(self.redis_client.lpop(f'user:{user_id}:queue'))
            room = await self.get_room(self.room_name)
            user = await self.get_user(user_id)
            if user:
                await self.create_message(user, room, message_data['message'])
                await self.send(text_data=json.dumps({
                    'type': 'chat_message',
                    'message': message_data['message'],
                    'username': user.username
                }))
