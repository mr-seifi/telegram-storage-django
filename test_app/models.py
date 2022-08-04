from django.db import models
from storage.storages import TelegramStorage


class SampleModel(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(
        storage=TelegramStorage,
        upload_to='files'
    )
