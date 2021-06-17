# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings

from tcms.core.models import TCMSActionModel

class Node(TCMSActionModel):
    id = models.AutoField(db_column='node_id', primary_key=True)
    name = models.CharField(max_length=10)
    ip = models.CharField(max_length=255)
    did = models.CharField(max_length=255, blank=True, null=True)
    slot = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=10, blank=True)
    #project = models.CharField(max_length=255, blank=True, null=True)
    product = models.ForeignKey('management.Product', related_name="node",  
                                on_delete=models.SET_NULL, null=True)
    fw = models.CharField(max_length=255, blank=True, null=True)
    vendor = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    os = models.CharField(max_length=255, blank=True, null=True)
    tag = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        verbose_name_plural = u'test node'
        unique_together = ('name','ip')

    def __str__(self):
        return self.name

    def update(self, values):
        #print("[Node Update]============")
        #print(values)
        if values.get('ip'):
            self.ip = values['ip']
        if values.get('system'):
            self.os = values['system']
        if values.get('did'):
            self.did = values['did']
        if values.get('slot'):
            self.slot = values['slot']
        if values.get('state'):
            self.state = values['state']
        #if values.get('project'):
        #    self.project = values['project']
        if values.get('fw'):
            self.fw = values['fw']
        if values.get('vendor'):
            self.vendor = values['vendor']
        if values.get('description'):
        #if 'description' in values.keys():
            self.description = values['description']
        if 'tag' in values.keys():
            self.tag = values['tag']
        self.save()
        return self

class Classification(TCMSActionModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=64)
    description = models.TextField(blank=True)
    sortkey = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Product(TCMSActionModel):
    id = models.AutoField(max_length=5, primary_key=True)
    name = models.CharField(unique=True, max_length=64)
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    tracker_type = models.CharField(
        max_length=128,
        verbose_name='Type',
        help_text='This determines how Kiwi TCMS integrates with the IT system',
        null=True
    )
    bug_system_product = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.name

    @classmethod
    def to_xmlrpc(cls, query=None):
        from tcms.xmlrpc.serializer import ProductXMLRPCSerializer
        _query = query or {}
        query_set = cls.objects.filter(**_query).order_by('pk')
        serializer = ProductXMLRPCSerializer(model_class=cls, queryset=query_set)
        return serializer.serialize_queryset()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save(force_insert=force_insert,
                     force_update=force_update,
                     using=using,
                     update_fields=update_fields)

        #self.suite.get_or_create(name='--default--')
        self.version.get_or_create(value='unspecified')
        self.build.get_or_create(name='unspecified')


class Priority(TCMSActionModel):
    id = models.AutoField(max_length=5, primary_key=True)
    value = models.CharField(unique=True, max_length=64)
    sortkey = models.IntegerField(default=0)
    is_active = models.BooleanField(db_column='isactive', default=True)

    class Meta:
        verbose_name_plural = u'priorities'

    def __str__(self):
        return self.value


class Component(TCMSActionModel):
    id = models.AutoField(max_length=5, primary_key=True)
    name = models.CharField(max_length=128)
    product = models.ForeignKey(Product, related_name='component', on_delete=models.CASCADE)
    initial_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column='initialowner',
        related_name='initialowner',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    initial_qa_contact = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column='initialqacontact',
        related_name='initialqacontact',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    description = models.TextField(blank=True)

    # Auto-generated attributes from back-references:
    #   'cases' : list of TestCases (from TestCases.components)

    class Meta:
        unique_together = ('product', 'name')

    def __str__(self):
        return self.name


class Version(TCMSActionModel):
    id = models.AutoField(primary_key=True)
    value = models.CharField(max_length=192)
    product = models.ForeignKey(Product, related_name='version', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('product', 'value')

    def __str__(self):
        return self.value

    @classmethod
    def string_to_id(cls, product_id, value):
        try:
            return cls.objects.get(product__id=product_id,
                                   value=value).pk
        except cls.DoesNotExist:
            return None


class Build(TCMSActionModel):
    build_id = models.AutoField(max_length=10, unique=True, primary_key=True)
    name = models.CharField(max_length=255)
    product = models.ForeignKey(Product, related_name='build', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(db_column='isactive', default=True)

    class Meta:
        unique_together = ('product', 'name')
        verbose_name = u'build'
        verbose_name_plural = u'builds'

    @classmethod
    def to_xmlrpc(cls, query=None):
        from tcms.xmlrpc.serializer import BuildXMLRPCSerializer
        query = query or {}
        query_set = cls.objects.filter(**query).order_by('pk')
        serializer = BuildXMLRPCSerializer(model_class=cls, queryset=query_set)
        return serializer.serialize_queryset()

    def __str__(self):
        return self.name


class Tag(TCMSActionModel):
    id = models.AutoField(db_column='tag_id', max_length=10, primary_key=True)
    name = models.CharField(db_column='tag_name', max_length=255)

    class Meta:
        verbose_name = u'tag'
        verbose_name_plural = u'tags'

    def __str__(self):
        return self.name

    @classmethod
    def get_or_create(cls, user, tag_name):
        """
            Helper method used to check if @user is allowed
            to automatically create new Tag in the database!

            If they are not, e.g. in environment where users
            are forced to use pre-existing tags created by admin,
            then it will raise a DoesNotExist exception.
        """
        if user.has_perm('management.add_tag'):
            return cls.objects.get_or_create(name=tag_name)

        return cls.objects.get(name=tag_name), False
