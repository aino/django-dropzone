from django import forms
from django.conf.urls import url
from django.core.exceptions import FieldDoesNotExist
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from dropzone.fields import DropZoneFileField
from functools import update_wrapper


class DropZoneAdminMixin(object):
    @csrf_exempt
    def dropzone_upload(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        for field_name, content in request.FILES.items():
            try:
                dropzone_field = obj._meta.get_field(field_name)
            except FieldDoesNotExist:
                return HttpResponse(status=403)
            if not isinstance(dropzone_field, DropZoneFileField):
                return HttpResponse(status=403)
            file_field = dropzone_field.base_field
            attrs = {}
            attrs[field_name] = file_field.formfield()
            DropZoneForm = type('DropZoneForm', (forms.Form,), attrs)
            form = DropZoneForm(files=request.FILES)
            if form.is_valid():
                name = file_field.generate_filename(obj, content.name)
                name = file_field.storage.save(name, content, max_length=file_field.max_length)
                data = getattr(obj, field_name) or []
                data.append(name)
                setattr(obj, field_name, data)
                obj.save()
        return HttpResponse()

    def get_urls(self):
        urlpatterns = super(DropZoneAdminMixin, self).get_urls()

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        for field_name in self.model._meta.get_all_field_names():
            field = self.model._meta.get_field(field_name)
            if isinstance(field, DropZoneFileField):
                urlpatterns = [
                    url(r'^(.+)/dropzone/$', wrap(self.dropzone_upload)),
                ] + urlpatterns
        return urlpatterns
