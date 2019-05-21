"""
    This module implements Kiwi TCMS interface to external issue tracking systems.
    :class:`tcms.issuetracker.types.IssueTrackerType` provides the interface
    while the rest of the classes in this module implement it! Refer to each
    implementor class for integration specifics!
"""

import os
import tempfile
from urllib.parse import urlencode


import datetime
from django.conf import settings
from production_rest_client.rest_client import RestClient


class TestExecutorType:
    """
        Represents actions which can be performed with issue trackers.
        This is a common interface for all issue trackers that Kiwi TCMS
        supports!
    """

    def __init__(self):
        pass

    @classmethod
    def from_name(cls, name):
        """
            Return the class which matches ``name`` if it exists inside this
            module or raise an exception.
        """
        if name not in globals():
            raise NotImplementedError('IT of type %s is not supported' % name)
        return globals()[name]

    def run_test_in_async_mode(self, test):
        raise NotImplementedError()

    def cancel_all_test(self):
        raise NotImplementedError()

    def query_test_result(self, key):
        raise NotImplementedError()

    # pylint: disable = invalid-name, no-self-use
    def update_fw(self, file):
        raise NotImplementedError()

class CnexExecutor(TestExecutorType):
    def __init__(self, ip, timeout=0.5):
        super(CnexExecutor, self).__init__()
        self.ip = ip
        self.rtc = RestClient(self.ip, time_out=timeout)

    def _convert_result(self, rtc_result):
        #{'id': 6, 'name': 'BLOCKED'}, 
        #{'id': 7, 'name': 'ERROR'}, 
        #{'id': 5, 'name': 'FAILED'}, 
        #{'id': 1, 'name': 'IDLE'}, 
        #{'id': 4, 'name': 'PASSED'}, 
        #{'id': 3, 'name': 'PAUSED'}, 
        #{'id': 2, 'name': 'RUNNING'}, 
        #{'id': 8, 'name': 'WAIVED'}
        ret_map = {
                    0:{'stat':'FAILED', 'kiwi_stat_id':5},
                    1:{'stat':'PASSED', 'kiwi_stat_id':4},
                    2:{'stat':'NOT_START', 'kiwi_stat_id':3},
                    3:{'stat':'RUNNING', 'kiwi_stat_id':2},
                    4:{'stat':'ABORT', 'kiwi_stat_id':7, },
                    11:{'stat':'ERROR_NOT_FOUND', 'kiwi_stat_id':7},
                    12:{'stat':'ERROR_BASE_EXCEPTION', 'kiwi_stat_id':7},
                    13:{'stat':'ERROR_TIMEOUT', 'kiwi_stat_id':3},
                    14:{'stat':'ERROR_CONNECTION', 'kiwi_stat_id':3},
                  }
        ret = ret_map[rtc_result['state']]
        ret.update({'msg':rtc_result['msg']})
        return ret

    def _convert_result_when_cancel(self, rtc_result):
        ret = {}
        if rtc_result['state'] is not 1:
            ret['kiwi_stat_id'] = 7
        ret['msg'] = rtc_result['msg']

        return ret

    def _convert_result_when_run(self, rtc_result):
        ret_map = {
                    0:{'stat':'FAILED', 'kiwi_stat_id':7},
                    1:{'stat':'PASSED', 'kiwi_stat_id':3},
                    2:{'stat':'NOT_START', 'kiwi_stat_id':3},
                    3:{'stat':'RUNNING', 'kiwi_stat_id':2},
                    4:{'stat':'ABORT', 'kiwi_stat_id':7, },
                    11:{'stat':'ERROR_NOT_FOUND', 'kiwi_stat_id':7},
                    12:{'stat':'ERROR_BASE_EXCEPTION', 'kiwi_stat_id':7},
                    13:{'stat':'ERROR_TIMEOUT', 'kiwi_stat_id':7},
                    14:{'stat':'ERROR_CONNECTION', 'kiwi_stat_id':7},
                  }
        ret = ret_map[rtc_result['state']]
        if (rtc_result['state'] == 1) and (rtc_result['data']):
            ret.update({'key':rtc_result['data'][0]})
        ret.update({'msg':rtc_result['msg']})
        return ret
    def run_test_in_async_mode(self, test):
        ret = self.rtc.test_case.run(test_case = test, mode = "async")
        #print(ret)
        return self._convert_result_when_run(ret)

    def cancel_all_test(self):
        ret = self.rtc.test_case.stop_tests()
        #print(ret)
        return self._convert_result_when_cancel(ret)

    def query_test_result(self, key):
        ret = self.rtc.test_case.get_async_result(key)
        #print(ret)
        return self._convert_result(ret)

    # pylint: disable = invalid-name, no-self-use
    def update_fw(self, file, device_index=1, slot=2):
        ret = self.rtc.operation.upgrade(file, device_index=device_index, slot=slot)
        return ret