# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.testcases.models import Category
from tcms.xmlrpc.decorators import permissions_required

@permissions_required('testcases.add_testcase')
@rpc_method(name='Category.create')
def create(values, **kwargs):
    """
    .. function:: XML-RPC TestCase.create(values)

        Create a new Category object and store it in the database.

        :param values: Field values for :class:`tcms.testcases.models.Category`
        :type values: dict
        :return: Serialized :class:`tcms.testcases.models.Category` object
        :rtype: dict
        :raises: PermissionDenied if missing *testcases.add_testcase* permission

        Minimal test case parameters::

            >>> values = {
                'category': 135,
                'description': 61,
                'parent_category': 'Testing XML-RPC',
            }
            >>> TestCase.create(values)
    """
    if (not values.get('product_id')) and (not(values.get('product') and values.get('classification'))):
        raise ValueError("product or product_id is not specified")
    if not (values.get('parent_category_id') or values.get('parent_category')):
        raise ValueError("parent_category_id or parent_category is not specified")
    if not (values.get('description')):
        values['description'] = ''

    cate = Category.create(values=values)
    cate.save()
    
    result = cate.serialize()
    return result

@rpc_method(name='Category.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Category.filter(query)

        Search and return Category objects matching query.

        :param query: Field lookups for :class:`tcms.testcases.models.Category`
        :type query: dict
        :return: List of serialized :class:`tcms.testcases.models.Category` objects
        :rtype: list(dict)
    """
    return Category.to_xmlrpc(query)

@permissions_required('testcases.change_testcase')
@rpc_method(name='Category.update')
def update(cate_id, values, **kwargs):
    """
    .. function:: XML-RPC Category.update(case_id, values)

        Update the fields of the selected Category.

        :param cate_id: PK of Category to be modified
        :type cate_id: int
        :param values: Field values for :class:`tcms.testcases.models.Category`.
        :type values: dict
        :return: Serialized :class:`tcms.testcases.models.Category` object
        :rtype: dict
        :raises: Category.DoesNotExist if object specified by PK doesn't exist
        :raises: PermissionDenied if missing *testcases.change_testcase* permission
    """
    if not (values.get('parent_category_id') or values.get('name')):
        raise ValueError("Only support update parent_category_id or name")
    cate = Category.objects.get(pk=cate_id)
    if values.get('parent_category_id'):
        parent = Category.objects.get(id=values.get('parent_category_id'))
        if parent.product.pk != cate.product.pk:
            raise ValueError("Category product not match")
        setattr(cate, 'parent_category', parent)

    if values.get('name'):  
        setattr(cate, 'name', values['name'])

    cate.save()

    return cate.serialize()