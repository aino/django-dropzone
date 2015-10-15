from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models


class TmpFile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    app = models.CharField(max_length=500)
    model = models.CharField(max_length=500)
    field = models.CharField(max_length=500)
    name = models.CharField(max_length=500)
    data = models.BinaryField()

    @property
    def content(self):
        return ContentFile(self.data, self.name)
