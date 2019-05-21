# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.testcases.models import Suite
from tcms.xmlrpc.decorators import permissions_required

@permissions_required('testcases.add_testcase')
@rpc_method(name='Suite.create')
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
    if not (values.get('description')):
        values['description'] = ''

    suite = Suite.create(values=values)
    cate.save()
    
    result = suite.serialize()
    return result

@rpc_method(name='Suite.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Category.filter(query)

        Search and return Category objects matching query.

        :param query: Field lookups for :class:`tcms.testcases.models.Category`
        :type query: dict
        :return: List of serialized :class:`tcms.testcases.models.Category` objects
        :rtype: list(dict)
    """
    ret = Suite.to_xmlrpc(query)
    return ret

@permissions_required('testcases.change_testcase')
@rpc_method(name='Suite.update')
def update(suite_id, values, **kwargs):
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

    suite = Suite.objects.get(pk=suite_id)

    for key in values.keys():
        if key not in ['product']:
            setattr(suite, key, values[key])

    suite.save()

    return suite.serialize()