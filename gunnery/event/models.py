from json_field import JSONField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save
from core.models import Department, Application


class NotificationPreferences(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="notifications")
    event_type = models.CharField(max_length=32, blank=False, null=False)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "event_type", "content_type", "object_id")

    @staticmethod
    def on_save_application(sender, instance, created, **kwargs):
        if created:
            content_type = ContentType.objects.get_for_model(type(instance))
            groups = instance.department.groups.filter(system_name__isnull=False)
            user_model = get_user_model()
            for user in user_model.objects.filter(groups__in=groups):
                NotificationPreferences(user=user,
                                        event_type='ExecutionFinish',
                                        content_type=content_type,
                                        object_id=instance.id,
                                        is_active=True).save()
post_save.connect(NotificationPreferences.on_save_application, sender=Application)


class Activity(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="actions", blank=True, null=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="events")
    type = models.CharField(max_length=128, blank=False)
    data = JSONField()
    time = models.DateTimeField(auto_now=True)

    def get_object_model_name(self):
        if "object_model" in self.data:
            model = self.data["object_model"]
            return model[model.find('.')+1:]
