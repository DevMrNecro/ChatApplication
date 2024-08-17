# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from .models import ChatRoom, Message
# from django.contrib.auth.models import User

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_name = self.scope['url_route']['kwargs']['room_name']
#         self.room_group_name = f'chat_{self.room_name}'

#         # Join room group
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )

#         await self.accept()

#     async def disconnect(self, close_code):
#         # Leave room group
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         message = text_data_json['message']
#         username = self.scope['user'].username

#         # Save the message to the database
#         room = await self.get_room(self.room_name)
#         user = self.scope['user']
#         await self.create_message(user, room, message)

#         # Send message to room group
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',
#                 'message': message,
#                 'username': username
#             }
#         )

#     async def chat_message(self, event):
#         message = event['message']
#         username = event['username']

#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({
#             'message': message,
#             'username': username
#         }))

#     @database_sync_to_async
#     def get_room(self, room_name):
#         return ChatRoom.objects.get(name=room_name)

#     @database_sync_to_async
#     def create_message(self, user, room, content):
#         return Message.objects.create(user=user, room=room, content=content)
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user_id = self.scope['url_route']['kwargs'].get('user_id')

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # # Notify room of new user joining
        # if self.user_id:
        #     user = await self.get_user(self.user_id)
        #     username = user.username if user else 'Anonymous'
        #     await self.channel_layer.group_send(
        #         self.room_group_name,
        #         {
        #             'type': 'user_joined',
        #             'username': username
        #         }
        #     )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')

        # Fetch user instance using user_id
        try:
            user = await self.get_user(self.user_id)
            username = user.username if user else 'Anonymous'
            
            # Save the message to the database
            room = await self.get_room(self.room_name)
            if user:
                await self.create_message(user, room, message)

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username
                }
            )
        except ObjectDoesNotExist:
            # Handle the case where the room does not exist
            await self.send(text_data=json.dumps({
                'error': 'Room does not exist'
            }))

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username
        }))

    async def user_joined(self, event):
        username = event['username']

        # Notify WebSocket about the new user
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'username': username
        }))

    @database_sync_to_async
    def get_room(self, room_name):
        from .models import ChatRoom
        try:
            return ChatRoom.objects.get(name=room_name)
        except ChatRoom.DoesNotExist:
            # If the room does not exist, raise an exception
            raise ObjectDoesNotExist

    @database_sync_to_async
    def get_user(self, user_id):
        from django.contrib.auth.models import User
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            # If the user does not exist, return None
            return None

    @database_sync_to_async
    def create_message(self, user, room, content):
        from .models import Message
        # Ensure that user is a proper instance of User model
        if user:
            return Message.objects.create(user=user, room=room, content=content)
        else:
            # Handle the case where user is None
            return None
