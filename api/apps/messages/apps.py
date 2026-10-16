from django.apps import AppConfig


class MessagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.messages"
    # django.contrib.messages already answers to "messages", and two apps can't share a label.
    label = "gym_messages"
