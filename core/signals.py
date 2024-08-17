from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.db.models import ManyToManyField
from .models import ChatRoom
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User

@receiver(m2m_changed, sender=ChatRoom.users.through)
def notify_user_join(sender, instance, action, pk_set, **kwargs):
    # Initialize channel_layer
    channel_layer = get_channel_layer()
    
    # Ensure channel_layer is valid before proceeding
    if channel_layer is None:
        raise ValueError("Channel layer is not configured. Ensure CHANNEL_LAYERS is properly set in settings.py")

    room_name = instance.name
    room_group_name = f'chat_{room_name}'

    if action == 'post_add':
        # Notify all users in the room about the new user
        for user_id in pk_set:
            user = User.objects.get(id=user_id)
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'user_joined',
                    'username': user.username
                }
            )
    
    elif action == 'post_remove':
        # Notify all users in the room about the user leaving
        for user_id in pk_set:
            user = User.objects.get(id=user_id)
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'user_left',
                    'username': user.username
                }
            )
