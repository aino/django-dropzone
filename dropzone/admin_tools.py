import os
from django import forms
from django.conf.urls import url
from django.core.exceptions import FieldDoesNotExist
from django.core.exceptions import FieldError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from dropzone.fields import DropZoneFileField
from dropzone.models import TmpFile
from functools import update_wrapper


class DropZoneAdminMixin(object):

    @csrf_exempt
    def dropzone_upload(self, request, pk=None):
        """
        Handle the uploaded files and save to tmp file db if no object is
        created
        """
        if pk is None:
            obj = None
        else:
            obj = get_object_or_404(self.model, pk=pk)
        for fieldname, content in request.FILES.items():
            try:
                dropzonefield = self.model._meta.get_field(fieldname)
            except FieldDoesNotExist:
                return HttpResponse(status=403)
            if not isinstance(dropzonefield, DropZoneFileField):
                return HttpResponse(status=403)
            filefield = dropzonefield.base_field
            attrs = {}
            attrs[fieldname] = filefield.formfield()
            DropZoneForm = type('DropZoneForm', (forms.Form,), attrs)
            form = DropZoneForm(files=request.FILES)
            if form.is_valid():
                if obj:
                    self.save_dropzone_file(filefield, content, obj, fieldname)
                else:
                    TmpFile.objects.create(
                        user=request.user,
                        app=self.model._meta.app_label,
                        model=self.model.__name__,
                        field=fieldname,
                        name=content.name,
                        data=content.read(),
                    )
        if obj:
            obj.save()
        return HttpResponse()

    def save_dropzone_file(self, filefield, content, obj, fieldname):
        """
        Save the contents in the using filefields upload_to attibute and then
        append the filenames to the objects fieldname attribute (the dropzone
        field)
        """
        if callable(filefield.upload_to):
            raise FieldError('`upload_to` cannot be a callable')
        filename = os.path.join(filefield.get_directory_name(), filefield.get_filename(content.name))
        filename = filefield.storage.save(filename, content, max_length=filefield.max_length)
        data = getattr(obj, fieldname) or []
        data.append(filename)
        setattr(obj, fieldname, data)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            params = {
                'user': request.user,
                'app': self.model._meta.app_label,
                'model': self.model.__name__,
            }
            for tmp in TmpFile.objects.filter(**params):
                try:
                    dropzonefield = self.model._meta.get_field(tmp.field)
                except FieldDoesNotExist:
                    continue
                if not isinstance(dropzonefield, DropZoneFileField):
                    continue
                filefield = dropzonefield.base_field
                self.save_dropzone_file(filefield, tmp.content, obj, tmp.field)
        TmpFile.objects.filter(user=request.user).delete()
        obj.save()

    def changelist_view(self, request, *args, **kwargs):
        """
        Just to empty tmp files
        """
        TmpFile.objects.filter(user=request.user).delete()
        return super(DropZoneAdminMixin, self).changelist_view(request, *args, **kwargs)

    def render_change_form(self, request, *args, **kwargs):
        """
        Just to empty tmp files
        """
        if request.method != 'POST':
            TmpFile.objects.filter(user=request.user).delete()
        return super(DropZoneAdminMixin, self).render_change_form(request, *args, **kwargs)

    def get_urls(self):
        """
        Add urls for new objects and existing
        """
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
                    url(r'^add/dropzone/$', wrap(self.dropzone_upload)),
                    url(r'^(.+)/dropzone/$', wrap(self.dropzone_upload)),
                ] + urlpatterns
        return urlpatterns
