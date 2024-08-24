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

        print(f"Connecting: room_name={self.room_name}, user_id={self.user_id}")

        # Check if the user is authorized to join the room
        if not await self.is_user_in_room(self.user_id, self.room_name):
            # Accept the connection before sending an error message
            await self.accept()
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'You do not have permission to chat in this room. Contact admin.'
            }))
            # Close the WebSocket connection
            await self.close()
            return

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



    async def is_user_in_room(self, user_id, room_name):
        room = await self.get_room(room_name)
        if room:
            return await database_sync_to_async(room.users.filter(id=user_id).exists)()
        return False


    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        if self.user_id:
            # Mark user as disconnected in Redis
            await self.mark_user_disconnected(self.user_id)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        timestamp = text_data_json.get('timestamp', '')


        print(f"Received message: {message}, user_id={self.user_id}")

        try:
            user = await self.get_user(self.user_id)
            if user:
                username = user.username
            else:
                username = 'Anonymous'
                print(f"User not found for user_id={self.user_id}")

            room = await self.get_room(self.room_name)
            if room:
                # Save the message to the database and update chat history
                message_obj = await self.create_message(user, room, message)

                # Check if user is connected and send the message to the room group
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
                            'username': username,
                            'timestamp': timestamp
                        }
                    )
            else:
                await self.send(text_data=json.dumps({'error': 'Room does not exist'}))
        except ObjectDoesNotExist:
            await self.send(text_data=json.dumps({'error': 'Room does not exist'}))
        except Exception as e:
            print(f"Error receiving message: {e}")

    async def chat_message(self, event):
        print(f"Sending message: {event['message']}, username={event['username']}")
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp']

        }))

    async def user_joined(self, event):
        print(f"User joined: {event['username']}")
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'username': event['username'],
            'room': self.room_name  # Added room information
        }))

    async def user_left(self, event):
        print(f"User left: {event['username']}")
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'username': event['username'],
            'room': self.room_name  # Added room information
        }))

    @database_sync_to_async
    def get_room(self, room_name):
        from .models import ChatRoom
        try:
            return ChatRoom.objects.get(name=room_name)
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def get_user(self, user_id):
        from django.contrib.auth.models import User
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def create_message(self, user, room, content):
        from .models import Message, ChatHistory
        if user and room:
            message = Message.objects.create(user=user, room=room, content=content)
            
            # Get or create chat history entry for the user
            chat_history, created = ChatHistory.objects.get_or_create(chat_room=room, user_id=user.id)
            
            # Load existing history or initialize as empty list
            history = json.loads(chat_history.history) if chat_history.history else []
            
            # Append the new message
            history.append({
                'message': message.content,
                'username': user.username,
                'timestamp': message.timestamp.isoformat()
            })
            chat_history.history = json.dumps(history)
            chat_history.save()

            return message
        return None

    @database_sync_to_async
    def get_chat_history(self, room, user_id):
        from .models import ChatHistory
        if room:
            try:
                chat_history, created = ChatHistory.objects.get_or_create(chat_room=room, user_id=user_id)
                history = json.loads(chat_history.history) if isinstance(chat_history.history, str) else chat_history.history
                return history
            except ChatHistory.DoesNotExist:
                return []
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
            if user and room:
                await self.create_message(user, room, message_data['message'])
                await self.send(text_data=json.dumps({
                    'type': 'chat_message',
                    'message': message_data['message'],
                    'username': user.username
                }))
