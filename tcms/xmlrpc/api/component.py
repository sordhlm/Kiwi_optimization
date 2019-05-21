# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

from modernrpc.core import rpc_method, REQUEST_KEY

from tcms.management.models import Component
from tcms.xmlrpc.utils import pre_check_product
from tcms.xmlrpc.decorators import permissions_required
from tcms.testcases.models import TestCase

__all__ = (
    'create',
    'update',
    'filter',
)


@rpc_method(name='Component.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Component.filter(query)

        Search and return the resulting list of components.

        :param query: Field lookups for :class:`tcms.management.models.Component`
        :type query: dict
        :return: List of serialized :class:`tcms.management.models.Component` objects
        :rtype: list(dict)
    """
    ret = Component.to_xmlrpc(query)
    return ret

@rpc_method(name='Component.filter_for_view')
def filter_for_view(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Component.filter(query)

        Search and return the resulting list of components.

        :param query: Field lookups for :class:`tcms.management.models.Component`
        :type query: dict
        :return: List of serialized :class:`tcms.management.models.Component` objects
        :rtype: list(dict)
    """
    #ret = Component.to_xmlrpc(query)
    #print(ret)
    ret = []
    if "product" in query.keys():
        #print(query["product"])
        #for case in TestCase.objects.filter(category__suite__product=query["product"]).distinct():
        #    for component in case.component.all():
        #        #print("%s %s"%(case.summary, component.name))
        #        add_case_to_component(ret, component.id, case.case_id)
        for component in Component.objects.filter(product=query['product']):
            #print(component.serialize())
            s_com = component.serialize()
            s_com['case_id'] = list(component.cases.all().values_list('pk', flat=True))
            #print(component.cases.all().values_list('pk', flat=True))
            print(s_com)
            ret.append(s_com)
        #print(ret)
        #ret = []
    #else:
    #    ret = []
    return ret

def add_case_to_component(com_list, fid, cid):
    for com in com_list:
        #print(com['id'])
        if com['id'] == fid:
            #print("find component")
            if('case_id' in com):
                #print("case list exit")
                com['case_id'].append(cid)
            else:
                #print("case list not exit")
                com['case_id'] = []
                com['case_id'].append(cid)


@permissions_required('management.add_component')
@rpc_method(name='Component.create')
def create(values, **kwargs):
    """
    .. function:: XML-RPC Component.create(values)

        Create new component.

        :param values: Field values for :class:`tcms.management.models.Component`
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Component` object
        :rtype: dict
        :raises: PermissionDenied if missing *management.add_component* permission

    .. note::

        If ``initial_owner_id`` or ``initial_qa_owner_id`` are
        not specified or don't exist in the database these fields are set to the
        user issuing the RPC request!
    """
    initial_owner_id = values.get('initial_owner_id', None)
    initial_qa_contact_id = values.get('initial_qa_contact_id', None)
    description = values.get('description', None)
    product = pre_check_product(values)

    request = kwargs.get(REQUEST_KEY)
    if User.objects.filter(pk=initial_owner_id).exists():
        _initial_owner_id = initial_owner_id
    else:
        _initial_owner_id = request.user.pk

    if User.objects.filter(pk=initial_qa_contact_id).exists():
        _initial_qa_contact_id = initial_qa_contact_id
    else:
        _initial_qa_contact_id = request.user.pk



    return Component.objects.create(
        name=values['name'],
        product=product,
        initial_owner_id=_initial_owner_id,
        initial_qa_contact_id=_initial_qa_contact_id,
        description=description,
    ).serialize()


@permissions_required('management.change_component')
@rpc_method(name='Component.update')
def update(component_id, values):
    """
    .. function:: XML-RPC Component.update

        Update component with new values.

        :param component_id: PK of Component to be updated
        :type component_id: int
        :param values: Fields and values to be updated
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Component` object
        :rtype: dict
        :raises: ValueError if ``name`` is missing or empty string
        :raises: PermissionDenied if missing *management.change_component* permission
    """
    if not isinstance(values, dict) or 'name' not in values:
        raise ValueError('Component name is not in values {0}.'.format(values))

    name = values['name']
    if not isinstance(name, str) or not name:
        raise ValueError('Component name {0} is not a string value.'.format(name))

    component = Component.objects.get(pk=int(component_id))
    component.name = name
    if values.get('initial_owner_id') and \
            User.objects.filter(pk=values['initial_owner_id']).exists():
        component.initial_owner_id = values['initial_owner_id']
    if values.get('initial_qa_contact_id') and \
            User.objects.filter(pk=values['initial_qa_contact_id']).exists():
        component.initial_qa_contact_id = values['initial_qa_contact_id']
    if values.get('description'):
        component.description = values['description']
    component.save()
    return component.serialize()
