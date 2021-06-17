"""
    This module implements Kiwi TCMS interface to external issue tracking systems.
    :class:`tcms.issuetracker.types.IssueTrackerType` provides the interface
    while the rest of the classes in this module implement it! Refer to each
    implementor class for integration specifics!
"""

import os
import re
import tempfile
from urllib.parse import urlencode


import datetime
from django.conf import settings
from production_rest_client.rest_client import RestClient
from production_rest_client.api import Api

STAT_MAP = {
            0 :'FAILED',
            1 :'PASSED',
            2 :'NOT_START',
            3 :'RUNNING',
            4 :'ABORT',
            11:'ERROR_NOT_FOUND',
            12:'ERROR_BASE_EXCEPTION',
            13:'ERROR_TIMEOUT',
            14:'ERROR_CONNECTION',
            15:'ERROR_ABNOMAL_END',
          }

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
                    0:{'stat':STAT_MAP[0], 'kiwi_stat_id':5},
                    1:{'stat':STAT_MAP[1], 'kiwi_stat_id':4},
                    2:{'stat':STAT_MAP[2], 'kiwi_stat_id':3},
                    3:{'stat':STAT_MAP[3], 'kiwi_stat_id':2},
                    4:{'stat':STAT_MAP[4], 'kiwi_stat_id':7, },
                    11:{'stat':STAT_MAP[11], 'kiwi_stat_id':7},
                    12:{'stat':STAT_MAP[12], 'kiwi_stat_id':7},
                    13:{'stat':STAT_MAP[13], 'kiwi_stat_id':3},
                    14:{'stat':STAT_MAP[14], 'kiwi_stat_id':3},
                    15:{'stat':STAT_MAP[15], 'kiwi_stat_id':7},
                  }
        ret = ret_map[rtc_result['state']]
        ret.update({'msg':rtc_result['msg']+' state: '+ret['stat']})
        return ret

    def _convert_result_when_cancel(self, rtc_result):
        ret = {}
        if rtc_result['state'] is not 1:
            ret['kiwi_stat_id'] = 7
        else:
            ret['kiwi_stat_id'] = 1
        ret['msg'] = rtc_result['msg']

        return ret

    def _convert_result_when_run(self, rtc_result):
        ret_map = {
                    0:{'stat':STAT_MAP[0], 'kiwi_stat_id':7},
                    1:{'stat':STAT_MAP[1], 'kiwi_stat_id':3},
                    2:{'stat':STAT_MAP[2], 'kiwi_stat_id':3},
                    3:{'stat':STAT_MAP[3], 'kiwi_stat_id':2},
                    4:{'stat':STAT_MAP[4], 'kiwi_stat_id':7, },
                    11:{'stat':STAT_MAP[11], 'kiwi_stat_id':7},
                    12:{'stat':STAT_MAP[12], 'kiwi_stat_id':7},
                    13:{'stat':STAT_MAP[13], 'kiwi_stat_id':7},
                    14:{'stat':STAT_MAP[14], 'kiwi_stat_id':7},
                    15:{'stat':STAT_MAP[15], 'kiwi_stat_id':7},
                  }
        ret = ret_map[rtc_result['state']]
        if (rtc_result['state'] == 1) and (rtc_result['data']):
            ret.update({'key':rtc_result['data'][0]})
        ret.update({'msg':rtc_result['msg']+' state: '+ret['stat']})
        return ret
    def run_test_in_async_mode(self, test):
        ret = self.rtc.test.run(test_name = test, mode = "async")
        #print(ret)
        return self._convert_result_when_run(ret)

    def cancel_test(self, key):
        ret = self.rtc.test.stop_tests(key)
        #print("[cancel_test]key:%s"%key)
        #print(ret)
        return self._convert_result_when_cancel(ret)

    def query_test_result(self, key):
        ret = self.rtc.test.get_async_result(key)
        #print("[query_test_result]key:%s"%key)
        #print(ret)
        return self._convert_result(ret)

    # pylint: disable = invalid-name, no-self-use
    def update_fw(self, file, device_index=1, slot=2):
        ret = self.rtc.operation.upgrade(file, device_index=device_index, slot=slot)
        return ret

    def check_status(self):
        ret = self.rtc.state.get_state()
        #print(ret)
        if 'state' in ret:
            if ret['state'] == 1:
                return 'on'
        return 'off'

class PerformanceReport(TestExecutorType):
    def __init__(self):
        super(PerformanceReport, self).__init__()
        self.rtc = Api()
        self.pro_summary_field = ['start_time','end_time','duration','tester','environment']
    
    def query_product(self):
        return ['tahoe','ad2']
    
    def __add_space(self, src, num, dst=r"&nnsp;"):
        length = len(src)
        ret = src
        if num > length:
            ret = src+dst*5
        else:
            ret = src[:num]
        return ret

    def __update_summary_with_date(self, src):
        dst = []
        re_com = re.compile(r'^[0-9\.]+$')
        for element in src:
            #print("############")
            #print(element)
            for field in self.pro_summary_field:
                if field in element.keys():
                    #element['test_key'] = element['test_key'][:12]
                    #if isinstance(element[field], str):
                    #    element[field] = element[field].replace("_",'')
                    if isinstance(element[field], datetime.datetime):
                        element[field] = element[field].strftime("%Y-%m-%d %H:%M:%S")
                    if isinstance(element[field], datetime.timedelta):
                        element[field] = str(element[field])
                    if isinstance(element[field], dict):
                        for key in element[field].keys():
                            element[field][key] = str(element[field][key])
                    if element[field] is None:
                        element[field] = str(element[field])
            if 'summary_report' in element.keys():
                for key, val in element['summary_report'].items():
                    if re_com.match(val):
                        element['summary_report'][key] = round(float(val), 2)
            dst.append(element)
        #print(sorted(dst, key=lambda element: element['start_time']))
        return sorted(dst, key=lambda element: element['start_time'], reverse=True)

    def __add_summary(self, src):
        dst = []
        for element in src:
            element['summary'] = element['name'].ljust(20) + ' ' + element['start_time'][:10]
            dst.append(element)
        return dst

    def delete_group(self, keys):
        for key in keys:
            print("delete perf data: %s"%key)
            element = self.rtc.delete_performance_result(key)

    def query_group(self, keys=None):
        summary = self.rtc.search(keys)
        #print(summary)
        return self.__update_summary_with_date(summary)

    def query_tree_group(self, keys=None, confirm=2):
        summary = self.rtc.search()
        
        ret = {}
        date_exist = 0
        summary = sorted(summary, key=lambda element: element['start_time'], reverse=True)
        #print(summary)
        #state = {"opened":0, "selected":0, 'disabled': 0}
        for element in summary:
            state = {"opened":0, "selected":1 if (element['test_key'] in keys) else 0, 'disabled': 0}
            if (element['confirm'] != confirm) and (confirm !=2):
                continue
            project_name = element['project_name'].lower()
            if project_name not in ret.keys():
                ret[project_name] = {'text':project_name, 'children':[], 'state':state}
            
            date = element['start_time'].strftime("%Y-%m-%d")
            for i in range(len(ret[project_name]['children'])):
                if date in ret[project_name]['children'][i]['text']:
                    ret[project_name]['children'][i]['children'].append({'text':element['name'],'id':element['test_key'], 'state':state})
                    date_exist = 1
                    continue
            if not date_exist:
                ret[project_name]['children'].append(\
                    {'text':date, 'children':[{'text':element['name'],'id':element['test_key'], 'state': state},]})
            date_exist = 0
        #print("###########################")
        #print(list(ret.values()))
        return list(ret.values())

    def query_result(self, keys):
        summary = []
        for key in keys:
            #element['key'] = key
            element = self.rtc.get_test_detail_information(key)
            #print(element)
            summary.extend(element)
        #print(summary)
        return self.__update_summary_with_date(summary)

    def __update_detail(self, src):
        ret = []
        #for element in src:
        s_time = src[0]['time']
        for i in range(len(src)):
            element = src[i]
            for key in element.keys():
                if 'bw' in key:
                    element[key] = float(element[key])/1000/1000
                if ('iops' in key) or ('temperature' in key):
                    element[key] = float(element[key])
            element['time'] = (element['time'] - s_time).seconds
            ret.append(element)
        return ret

    def query_detail(self, id):
        #bw_detail = [i*i/100+int(id)*100 for i in range(200,230)]
        #time = [i for i in range(30)]
        #entry0 = {'index':id,'name':'test1','product':'tahoe','pattern':'write','bandwidth':'201 MB/s','duration':'30','date':'2019-09-19','bw_detail':bw_detail,'time':time}
        result = self.rtc.get_step_detail_information(id)
        #print(result)
        if result:
            summary = self.__update_summary_with_date([result])[0]
            #print(summary)
            details = self.rtc.get_real_time_results(id)
            if not details:
                return 0
            #print(id)
            #print(details)
            summary['detail'] = self.__update_detail(details)
            #print(summary)
            return summary
        else:
            return 0

class NodeMonitor(TestExecutorType):
    def __init__(self):
        super(NodeMonitor, self).__init__()
        self.rtc = Api()

    def release_sql(self):
        del self.rtc
        
    def get_info(self, ip):
        ret = self.rtc.get_node_info(ip)
        #print(ret)
        return ret

    def set_attr(self, **argv):
        return self.rtc.set_project_name(ip, argv['project'])

    def get_test_detail(self, ip, num=10):
        detail = self.rtc.get_tests_detail(ip, num)
        for idx, val in enumerate(detail):
            detail[idx]['state_txt'] = STAT_MAP[val['state']]
        return detail

    def get_node_usage(self, ip):
        usage = self.rtc.get_node_usage(ip)
        #print(usage)
        for idx, val in enumerate(usage):
            #print(idx, val)
            usage[idx]['busy'] = round(val['usage']*100, 2)
            usage[idx]['idle'] = 0
            usage[idx]['total_time'] = round(usage[idx]['total_time']/3600, 2)
        #print(usage)
        return usage
