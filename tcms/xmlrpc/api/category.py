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

    print("API: create category********")
    if not (values.get('product') or values.get('parent_category')):
        raise ValueError()
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
