from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.forms import Widget
from django.forms.utils import flatatt
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


class DropZoneWidget(Widget):
    class Media:
        css = {
            'all': ('dropzone/dropzone.css',)
        }
        js = ('dropzone/dropzone.js',)

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        return mark_safe(
            '<br><div%s style="height:1000px"></div><script>var ds = new Dropzone("#%s", {url: "dropzone/", paramName: "%s"});</script>' % (
                flatatt(final_attrs),
                final_attrs['id'],
                name,
            )
        )


class DropZoneFileField(ArrayField):
    base_field = models.FileField

    def __init__(self, base_field=None, size=None, null=False, default=[], *args, **kwargs):
        base_field = self.base_field(*args, **kwargs)
        super(DropZoneFileField, self).__init__(base_field, size=size, null=null, default=default)

    def formfield(self, **kwargs):
        defaults = {'widget': DropZoneWidget}
        defaults.update(kwargs)
        return super(DropZoneFileField, self).formfield(**defaults)


class DropZoneImageField(DropZoneFileField):
    base_field = models.ImageField
