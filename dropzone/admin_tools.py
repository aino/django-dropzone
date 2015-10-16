from django import forms
from django.conf.urls import url
from django.core.exceptions import FieldDoesNotExist
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from dropzone.fields import DropZoneFileField
from dropzone.models import TmpFile
from functools import update_wrapper


class DropZoneAdminMixin(object):

    @csrf_exempt
    def dropzone_upload(self, request, object_id=None):
        """
        Handle the uploaded files and save to tmp file db store
        """
        for fieldname, content in request.FILES.items():
            try:
                dropzonefield = self.opts.get_field(fieldname)
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
                TmpFile.objects.create(
                    user=request.user,
                    app=self.opts.app_label,
                    model=self.opts.object_name,
                    field=fieldname,
                    name=content.name,
                    data=content.read(),
                )
        return HttpResponse()

    def save_model(self, request, obj, form, change):
        params = {
            'user': request.user,
            'app': self.opts.app_label,
            'model': self.opts.object_name,
        }
        for tmp in TmpFile.objects.filter(**params):
            try:
                dropzonefield = self.opts.get_field(tmp.field)
            except FieldDoesNotExist:
                continue
            if not isinstance(dropzonefield, DropZoneFileField):
                continue
            tmp.write_and_append(dropzonefield.base_field, obj)
        TmpFile.objects.filter(user=request.user).delete()
        super(DropZoneAdminMixin, self).save_model(request, obj, form, change)

    def render_change_form(self, request, *args, **kwargs):
        """
        Just to empty tmp files
        """
        if request.method != 'POST':
            TmpFile.objects.filter(user=request.user).delete()
        return super(DropZoneAdminMixin, self).render_change_form(request, *args, **kwargs)

    def get_urls(self):
        """
        Add urls for the dropzone upload
        """
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        urlpatterns = super(DropZoneAdminMixin, self).get_urls()
        for field in self.opts.fields:
            if isinstance(field, DropZoneFileField):
                return [
                    url(r'^(.+)/dropzone/$', wrap(self.dropzone_upload)),
                ] + urlpatterns
        return urlpatterns
