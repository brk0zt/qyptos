from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from chat.models import UserStatus

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_status(sender, instance, created, **kwargs):
    if created:
        UserStatus.objects.create(user=instance)
