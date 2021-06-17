# -*- coding: utf-8 -*-
import inspect
from django import forms
from django.contrib import admin
from django.forms.widgets import Select
from tcms.issuetracker import types
from tcms.management.models import Classification
from tcms.management.models import Component, Version
from tcms.management.models import Priority
from tcms.management.models import Product
from tcms.management.models import Build, Tag, Node


class ClassificationAdmin(admin.ModelAdmin):
    search_fields = ('name', 'id')
    list_display = ('id', 'name', 'description')

class IssueTrackerTypeSelectWidget(Select):
    """
    A select widget which displays the names of all classes
    derived from IssueTrackerType. Skip IssueTrackerType
    because it is doesn't provide implementations for most of its methods.
    """
    _choices = None

    @property
    def choices(self):
        if self._choices is None:
            self._choices = self._types_as_choices()
        return self._choices

    @choices.setter
    def choices(self, _):
        # ChoiceField.__init__ sets ``self.choices = choices``
        # which would override ours.
        pass

    @staticmethod
    def _types_as_choices():
        trackers = []
        for module_object in types.__dict__.values():
            if inspect.isclass(module_object) and \
               issubclass(module_object, types.IssueTrackerType) and \
               module_object != types.IssueTrackerType:  # noqa: E721
                trackers.append(module_object.__name__)
        return (('', ''), ) + tuple(zip(trackers, trackers))


class IssueTrackerTypeField(forms.ChoiceField):
    """Special choice field which uses the widget above"""
    widget = IssueTrackerTypeSelectWidget

    def valid_value(self, value):
        return True

class ProductAdminForm(forms.ModelForm):
    # select only tracker types for which we have available integrations
    tracker_type = IssueTrackerTypeField(
        label='Type',
        help_text='This determines how Kiwi TCMS integrates with the IT system',
    )

    class Meta:
        model = Product
        fields = '__all__'

class ProductsAdmin(admin.ModelAdmin):
    search_fields = ('name', 'id')
    list_display = ('id', 'name', 'classification', 'description')
    list_filter = ('id', 'name', 'classification')
    form = ProductAdminForm

class PriorityAdmin(admin.ModelAdmin):
    search_fields = ('value', 'id')
    list_display = ('id', 'value', 'sortkey', 'is_active')
    list_filter = ('is_active', )


class ComponentAdmin(admin.ModelAdmin):
    search_fields = ('name', 'id')
    list_display = ('id', 'name', 'product', 'initial_owner', 'description')
    list_filter = ('product',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'initial_owner')


class VersionAdmin(admin.ModelAdmin):
    search_fields = ('value', 'id')
    list_display = ('id', 'product', 'value')
    list_filter = ('product',)


class BuildAdmin(admin.ModelAdmin):
    search_fields = ('name', 'build_id')
    list_display = ('build_id', 'name', 'product', 'is_active')
    list_filter = ('product',)


class AttachmentAdmin(admin.ModelAdmin):
    search_fields = ('file_name', 'attachment_id')
    list_display = ('attachment_id', 'file_name', 'submitter', 'description',
                    'create_date', 'mime_type')


class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name')

class NodeAdmin(admin.ModelAdmin):
    search_fields = (('name',))
    list_display = ('id', 'name', 'ip' , 'description')
    list_filter = ('name','ip', )

admin.site.register(Classification, ClassificationAdmin)
admin.site.register(Product, ProductsAdmin)
admin.site.register(Priority, PriorityAdmin)
admin.site.register(Component, ComponentAdmin)
admin.site.register(Version, VersionAdmin)
admin.site.register(Build, BuildAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Node, NodeAdmin)