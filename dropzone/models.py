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

    def write_and_append(self, filefield, obj):
        """
        Writes the the stored data to filename generated from
        filefield, then appends that filename to the model instance
        dropzone field.
        """
        name = filefield.generate_filename(obj, self.name)
        filename = filefield.storage.save(name, self.content, max_length=filefield.max_length)
        data = getattr(obj, self.field) or []
        data.append(filename)
        setattr(obj, self.field, data)
