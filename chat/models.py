from django.db import models


class Message(models.Model):
    username = models.CharField(max_length=255)
    room = models.CharField(max_length=255)
    content = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    label = models.TextField(null=True, blank=True, default='')
    humanRequired = models.BooleanField(default=False)
    nonGG = models.BooleanField(default=False)

    class Meta:
        ordering = ("date_added",)
