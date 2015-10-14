from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.forms import Widget
from django.forms.utils import flatatt
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


class DropZoneImageWidget(Widget):
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
            '<br><div%s style="height:200px"></div><script>var ds = new Dropzone("#%s", {url: "."});</script>' % (
                flatatt(final_attrs),
                final_attrs['id'],
            )
        )


class DropZoneImageField(ArrayField):
    def __init__(self, base_field=None, size=None, null=False, default=[], *args, **kwargs):
        base_field = models.ImageField(*args, **kwargs)
        super(DropZoneImageField, self).__init__(base_field, size=size, null=null, default=default)

    def formfield(self, **kwargs):
        defaults = {'widget': DropZoneImageWidget}
        defaults.update(kwargs)
        return super(DropZoneImageField, self).formfield(**defaults)
