# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors
import json
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.db.models import Count, OuterRef, Subquery
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic import View
from django.views.decorators.http import require_POST

from tcms.management.models import Priority
from tcms.management.models import Product
from tcms.testruns.models import TestRun, TestCaseRunStatus, TestCaseRun
from tcms.testcases.models import TestCase, TestCasePlan, BugSystem
from tcms.testplans.models import TestPlan
from tcms.report.forms import TestingReportForm
from tcms.report.forms import TestingReportCaseRunsListForm
from tcms.report.data import CustomDetailsReportData
from tcms.report.data import CustomReportData
from tcms.report.data import ProductBuildReportData
from tcms.report.data import ProductReportData
from tcms.report.data import ProductComponentReportData
from tcms.report.data import ProductVersionReportData
from tcms.report.data import TestingReportByCasePriorityData
from tcms.report.data import TestingReportByCaseRunTesterData
from tcms.report.data import TestingReportByPlanBuildData
from tcms.report.data import TestingReportByPlanBuildDetailData
from tcms.report.data import TestingReportByPlanTagsData
from tcms.report.data import TestingReportByPlanTagsDetailData
from tcms.report.data import TestingReportCaseRunsData
from tcms.report.forms import CustomSearchForm
from tcms.search import remove_from_request_path
from tcms.issuetracker.types import IssueTrackerType
from tcms.testexecutor.types import TestExecutorType
from .forms import CustomSearchDetailsForm


def overall(request, template_name='report/list.html'):
    """Overall of products report"""
    cases_count_query = Product.objects.filter(pk=OuterRef('pk')) \
                                       .annotate(cases_num=Count('plan__case')) \
                                       .values('cases_num')
    products = Product.objects.annotate(plans_count=Count('plan', distinct=True),
                                        runs_count=Count('plan__run', distinct=True),
                                        cases_count=Subquery(cases_count_query))

    context_data = {
        'products': products
    }
    return render(request, template_name, context_data)

def overview(request, product_id, template_name='report/overview.html'):
    """Product for a product"""
    try:
        product = Product.objects.only('name').get(pk=product_id)
    except Product.DoesNotExist as error:
        raise Http404(error)

    query = TestRun.objects.filter(plan__product=product_id)
    runs_count = {
        'TOTAL': query.count(),
        'finished': query.filter(stop_date__isnull=False).count(),
    }
    runs_count['running'] = runs_count['TOTAL'] - runs_count['finished']

    query = TestCaseRun.objects.filter(run__plan__product=product_id)
    caserun_status_count = {}
    total = 0
    for row in TestCaseRun.objects.filter(
            run__plan__product=product_id
        ).values('case_run_status__name').annotate(
            status_count=Count('case_run_status__name')):
        caserun_status_count[row['case_run_status__name']] = row['status_count']
        total += row['status_count']
    caserun_status_count['TOTAL'] = total
    case_total = TestCase.objects.filter(category__suite__product=product_id).count()
    total_plans_tclist = {}
    query = TestPlan.objects.filter(product=product_id).order_by("plan_id")

    total_plans_cnt = []
    single_plans_cnt = []

    for i in range(len(query)):
        plan_list = []
        single_cnt = {}
        total_cnt = {}
        for j in range(0,i+1):
            plan_list.append(query[j].plan_id)
        plan_tclist = TestCaseRun.objects.filter(
                    run__plan__in=plan_list).order_by("case_run_id").values()
        total_cnt.update(calReportData(plan_tclist))
        total_cnt['TOTAL'] = TestCasePlan.objects.filter(plan__in = plan_list).count()
        plan_tclist = TestCaseRun.objects.filter(
                    run__plan=query[i].plan_id).order_by("case_run_id").values()
        single_cnt.update(calReportData(plan_tclist))
        single_cnt['TOTAL'] = TestCasePlan.objects.filter(plan = query[i].plan_id).count()
        single_cnt['name'] = query[i].name
        total_cnt['name'] = query[i].name
        single_cnt['IDLE'] = single_cnt['TOTAL'] - single_cnt['PASSED'] - \
                                single_cnt['FAILED'] - single_cnt['BLOCKED']
        total_cnt['IDLE'] = total_cnt['TOTAL'] - total_cnt['PASSED'] - \
                                total_cnt['FAILED'] - total_cnt['BLOCKED']
        total_plans_cnt.append(total_cnt)
        single_plans_cnt.append(single_cnt)


    bug_system = BugSystem.objects.get(name=product.tracker_type)
    tracker = IssueTrackerType.from_name(bug_system.tracker_type)(bug_system)
    bug_trend = tracker.gen_bug_trend_data({'product':product.bug_system_product,'delta':'1'})

    context_data = {
        'SUB_MODULE_NAME': 'overview',
        'product': product,
        'runs_count': runs_count,
        'case_run_count': caserun_status_count,
        'case_total':case_total,
        'total_plan_count':json.dumps(total_plans_cnt),
        'single_plan_count':single_plans_cnt,
        'bug_trend':json.dumps(bug_trend)
    }
    return render(request, template_name, context_data)

def filter_result(results, confirm):
    ret = []
    text = ""
    if confirm == 2:
        return 'All Data', results
    else:
        text = 'Confirm Data' if confirm else 'UNConfirm Data'
    for result in results:
        print(result)
        print(result['confirm'])
        print(confirm)
        print(result['confirm'] == confirm)
        if result['confirm'] == confirm:
            ret.append(result)
    return text, ret

def performance_report(request, template_name='report/performance.html'):
    executor_class = TestExecutorType.from_name('PerformanceReport')
    client = executor_class()
    #results = client.query_group()
    #print(results)
    #for i in results:
    #    print(i['summary'])
    text = ['UNCONFIRM DATA', 'CONFIRM DATA', 'ALL DATA']
    confirm = (request.GET.get("confirm"))
    if confirm not in ['0','1','2']:
        confirm = '2'
        #return JsonResponse({'ok':0, 'msg': 'Not valid confirm flag'})
    confirm = int(confirm)
    #confirm_text = 'ALL_DATA'
    #print(confirm)
    #if confirm:
    #    confirm_text, results = filter_result(results, confirm)

    keys = request.GET.getlist("keys")
    groups = []
    if keys:
        groups = client.query_group(keys)   
    #print(groups)  
    tree_data = client.query_tree_group(keys, confirm)
    #print(tree_data)
    context_data = {
        #'results': results,
        'groups': groups,
        'tree_data': tree_data,
        'confirm': text[confirm]
    }
    return render(request, template_name, context_data)

@require_POST
def delete_perf_group(request):
    #print("query group")
    keys = request.POST.getlist("keys[]")
    #print(keys)
    executor_class = TestExecutorType.from_name('PerformanceReport')
    client = executor_class()
    client.delete_group(keys)
    #print(result)
    return JsonResponse({'result': 0})

@require_POST
def query_perf_group(request):
    #print("query group")
    keys = request.POST.getlist("keys[]")
    #print(keys)
    executor_class = TestExecutorType.from_name('PerformanceReport')
    client = executor_class()
    result = client.query_group(keys)
    #print(result)
    return JsonResponse({'result': result})

@require_POST
def query_perf_result(request):
    #print("query result")
    executor_class = TestExecutorType.from_name('PerformanceReport')
    client = executor_class()
    keys = request.POST.getlist("keys[]")
    #print(keys)
    if(len(keys) > 50):
        return JsonResponse({'result': 'Load too many results!', 'ok':0})
    result = client.query_result(keys)
    #print(result)
    return JsonResponse({'result': result, 'ok':1})

@require_POST
def query_perf_detail(request):
    executor_class = TestExecutorType.from_name('PerformanceReport')
    id = request.POST.get('key')
    print(id)
    client = executor_class()
    result = client.query_detail(id)
    if result:
        return JsonResponse({'result': result, 'ok':1})
    else:
        return JsonResponse({'result': {}, 'ok':0})

def calReportData(tclist):
    #{'id': 6, 'name': 'BLOCKED'}, 
    #{'id': 7, 'name': 'ERROR'}, 
    #{'id': 5, 'name': 'FAILED'}, 
    #{'id': 1, 'name': 'IDLE'}, 
    #{'id': 4, 'name': 'PASSED'}, 
    #{'id': 3, 'name': 'PAUSED'}, 
    #{'id': 2, 'name': 'RUNNING'}, 
    #{'id': 8, 'name': 'WAIVED'}
    length = len(tclist)-1
    exist_tc = {}
    pass_cnt = 0
    fail_cnt = 0
    block_cnt = 0

    for i in range(length,-1,-1):
        if(tclist[i]['case_id'] not in exist_tc):
            if tclist[i]['case_run_status_id'] == 6:
                block_cnt += 1
                exist_tc[tclist[i]['case_id']] = 1
            elif tclist[i]['case_run_status_id'] == 5:
                fail_cnt += 1
                exist_tc[tclist[i]['case_id']] = 1
            elif tclist[i]['case_run_status_id'] == 4:
                pass_cnt += 1
                exist_tc[tclist[i]['case_id']] = 1
    return {'PASSED':pass_cnt,'FAILED':fail_cnt,'BLOCKED':block_cnt}

@require_POST
def update_bug_trend(request):
    product = request.POST.get('product_id')
    delta = request.POST.get('step')
    print(product)
    product = Product.objects.only('name').get(pk=product)
    result = ProductReportData.bug_trend(product, int(delta))
    print(result)
    return JsonResponse({'result': result})

@require_POST
def update_progress_trend(request):
    product = request.POST.get('product_id')
    delta = request.POST.get('step')
    is_run_base = request.POST.get('is_run_base')
    print("is_run_base: %s"%is_run_base)
    version_id = request.POST.get('version_id')
    product = Product.objects.only('name').get(pk=product)
    print("product: %s"%product)
    print("version: %s"%version_id)
    if version_id:
        result = ProductVersionReportData.case_runs_date_list(
                product, version_id, is_run_base=int(is_run_base), step=int(delta))
    else:
        result = ProductReportData.case_runs_date_list(product, int(is_run_base), int(delta))
    #print(result)
    return JsonResponse({'result': result})

class ProductReport(TemplateView, ProductReportData):
    template_name = 'report/overview.html'
    product = None

    def get(self, request, *args, **kwargs):
        try:
            self.product = Product.objects.only('name').get(pk=kwargs.get('product_id'))
        except (TypeError, ValueError, ObjectDoesNotExist) as error:
            raise Http404(error)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        product_id = self.product.pk
        #print("product_id:%d"%product_id)
        query = TestRun.objects.filter(plan__product=product_id)
        runs_count = {
            'TOTAL': query.count(),
            'finished': query.filter(stop_date__isnull=False).count(),
        }
        runs_count['running'] = runs_count['TOTAL'] - runs_count['finished']
    
        query = TestCaseRun.objects.filter(run__plan__product=product_id)
        caserun_status_count = {}
        total = 0
        for row in TestCaseRun.objects.filter(
                run__plan__product=product_id
            ).values('case_run_status__name').annotate(
                status_count=Count('case_run_status__name')):
            caserun_status_count[row['case_run_status__name']] = row['status_count']
            total += row['status_count']
        caserun_status_count['TOTAL'] = total
        case_total = TestCase.objects.filter(category__suite__product=product_id).count()
        total_plans_cnt = self.case_runs_date_list(product_id, is_run_base=0)
        #print(total_plans_cnt)
        data = super().get_context_data(**kwargs)
        data.update({
            'SUB_MODULE_NAME': 'overview',
            'product': self.product,
            'runs_count': runs_count,
            'case_run_count': caserun_status_count,
            'case_total':case_total,
            'total_plan_count':json.dumps(total_plans_cnt),
            'single_plan_count':self.case_plan_status(product_id),
            'bug_trend':json.dumps(self.bug_trend(self.product)),
            #'runs_trend':json.dumps(self.case_runs_date_list(product_id=product_id))
        })

        return data

class ProductVersionReport(TemplateView, ProductVersionReportData):
    template_name = 'report/version.html'
    product = None
    selected_version = None

    def get(self, request, *args, **kwargs):
        try:
            self.product = Product.objects.only('name').get(pk=kwargs.get('product_id'))
            version_id = request.GET.get('version_id')
            if version_id is not None:
                qs = self.product.version.only('value')
                self.selected_version = qs.get(pk=int(version_id))
        except (TypeError, ValueError, ObjectDoesNotExist) as error:
            raise Http404(error)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        product_id = self.product.pk

        case_runs_status_subtotal = None
        case_count_list = None
        selected_version = getattr(self, 'selected_version', None)
        if selected_version is not None:
            case_runs_status_subtotal = self.case_runs_status_subtotal(
                product_id, selected_version.pk)
            case_count_list = self.case_runs_date_list(
                product_id, selected_version.pk, is_run_base=1)

        data = super().get_context_data(**kwargs)
        data.update({
            'SUB_MODULE_NAME': 'version',
            'product': self.product,
            'versions': self._get_updated_versions(product_id),
            'version': selected_version,
            'case_runs_status_subtotal': case_runs_status_subtotal,
            'case_count_list': json.dumps(case_count_list)
        })

        return data

    def _get_updated_versions(self, product_id):
        versions = self.product.version.only('product', 'value')

        plans_subtotal = self.plans_subtotal(product_id)
        running_runs_subtotal = self.runs_subtotal(product_id, True)
        finished_runs_subtotal = self.runs_subtotal(product_id, False)
        cases_subtotal = self.cases_subtotal(product_id)
        case_runs_subtotal = self.case_runs_subtotal(product_id)
        #case_runs_subtotal = self.case_plans_subtotal(product_id)
        finished_case_runs_subtotal = self.finished_case_runs_subtotal(product_id)
        failed_case_runs_subtotal = self.failed_case_runs_subtotal(product_id)

        for version in versions:
            version_id = version.pk

            version.plans_count = plans_subtotal.get(version_id, 0)
            version.running_runs_count = running_runs_subtotal.get(version_id, 0)
            version.finished_runs_count = finished_runs_subtotal.get(version_id, 0)
            version.cases_count = cases_subtotal.get(version_id, 0)
            version.failed_case_runs_count = failed_case_runs_subtotal.get(version_id, 0)

            subtotal_finished_runs = finished_case_runs_subtotal.get(version_id, 0)
            subtotal_runs = case_runs_subtotal.get(version_id, 0)

            if subtotal_finished_runs and subtotal_runs:
                version.case_run_percent = round(subtotal_finished_runs * 100.0 / subtotal_runs, 1)
            else:
                version.case_run_percent = .0

        return versions


class ProductBuildReport(TemplateView, ProductBuildReportData):
    template_name = 'report/build.html'
    product = None
    selected_build = None

    def get(self, request, *args, **kwargs):
        try:
            self.product = Product.objects.only('name').get(pk=kwargs.get('product_id'))

            build_id = request.GET.get('build_id')
            if build_id is not None:
                qs = self.product.build.only('name')
                self.selected_build = qs.get(pk=int(build_id))
        except (TypeError, ValueError, ObjectDoesNotExist) as error:
            raise Http404(error)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        product_id = self.product.pk

        case_runs_status_subtotal = None
        selected_build = getattr(self, 'selected_build', None)

        if selected_build is not None:
            case_runs_status_subtotal = self.caserun_status_subtotal(
                product_id, selected_build.pk)

        data = super(ProductBuildReport, self).get_context_data(**kwargs)

        data.update({
            'SUB_MODULE_NAME': 'build',
            'product': self.product,
            'builds': self._get_updated_builds(product_id),
            'build': selected_build,
            'case_runs_status_subtotal': case_runs_status_subtotal,
        })

        return data

    def _get_updated_builds(self, product_id):
        builds = self.product.build.only('product', 'name')

        builds_total_runs = self.total_runs_count(product_id)
        builds_finished_runs = self.finished_runs_count(product_id)
        builds_finished_caseruns = self.finished_caseruns_count(product_id)
        builds_caseruns = self.caseruns_count(product_id)
        builds_failed_caseruns = self.failed_caseruns_count(product_id)

        for build in builds:
            build_id = build.pk
            build.total_runs = builds_total_runs.get(build_id, 0)
            build.finished_runs = builds_finished_runs.get(build_id, 0)
            build.failed_case_run_count = builds_failed_caseruns.get(build_id, 0)

            finished_caseruns = builds_finished_caseruns.get(build_id, 0)
            caseruns = builds_caseruns.get(build_id, 0)

            if finished_caseruns and caseruns:
                build.finished_case_run_percent = round(finished_caseruns * 100.0 / caseruns, 1)
            else:
                build.finished_case_run_percent = .0

        return builds


class ProductComponentReport(TemplateView, ProductComponentReportData):
    template_name = 'report/component.html'
    product = None
    selected_component = None

    def get(self, request, *args, **kwargs):
        try:
            self.product = Product.objects.only('name').get(pk=kwargs.get('product_id'))

            component_id = request.GET.get('component_id')
            if component_id is not None:
                qs = self.product.component.only('name')
                self.selected_component = qs.get(pk=int(component_id))
        except (TypeError, ValueError, Product.DoesNotExist) as error:
            raise Http404(error)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        components = self.product.component.select_related('product')
        components = components.only('name', 'product__name')

        product_id = self.product.pk
        total_cases = self.total_cases(product_id)
        failed_case_runs_count = self.failed_case_runs_count(product_id)
        finished_case_runs_count = self.finished_case_runs_count(product_id)
        com_cnt = {'PENDING':0,'RUNNING':0,'FAIL':0,'PASS':0}

        for component in components:
            component_id = component.pk
            component.total_cases = total_cases.get(component_id, 0)
            component.failed_case_run_count = failed_case_runs_count.get(component_id, 0)

            total_runs = finished_case_runs_count.get(component_id, 0)
            total_cases_of_component = component.total_cases
            stat = self.case_runs_count(component.pk)

            component.PASSED = stat['PASSED'] if 'PASSED' in stat else 0
            component.FAILED = stat['FAILED'] if 'FAILED' in stat else 0
            component.BLOCKED = stat['BLOCKED'] if 'BLOCKED' in stat else 0
            component.IDLE = component.total_cases - total_runs
            if total_cases_of_component == 0:
                component.status = 'PENDING'
            else:
                if component.IDLE:
                    component.status = 'RUNNING'
                else:
                    if component.failed_case_run_count:
                        component.status = 'FAIL'
                    else:
                        component.status = 'PASS'
            com_cnt[component.status] += 1
        # To show detail statistics upon case run status if user clicks a
        # component
        case_runs_status_subtotal = None
        selected_component = getattr(self, 'selected_component', None)
        if selected_component is not None:
            case_runs_status_subtotal = self.case_runs_count(
                selected_component.pk)

        data = super(ProductComponentReport, self).get_context_data(**kwargs)
        data.update({
            'SUB_MODULE_NAME': 'component',
            'product': self.product,
            'components': components,
            'component': selected_component,
            'case_runs_status_subtotal': case_runs_status_subtotal,
            'com_cnt': json.dumps(com_cnt),
        })

        return data


class CustomReport(TemplateView):
    template_name = 'report/custom_search.html'
    form_class = CustomSearchForm
    data_class = CustomReportData
    product = None
    _data = None

    def _get_search_form(self):
        req = self.request.GET
        form = self.form_class(req)
        form.populate(product_id=req.get('product'))
        return form

    def _do_search(self):
        return self.request.GET.get('a', '').lower() == 'search'

    def _report_data_context(self):
        form = self._get_search_form()
        context = {'form': form}

        if not form.is_valid():
            context.update({'builds': ()})
            return context

        self._data = self.data_class(form)

        builds = self._data.get_builds()

        build_ids = []
        for build in builds:
            build_ids.append(build['build'])

        if builds:
            # Summary header data
            runs_total = 0
            case_runs_total = 0
            automation_total = self._data.automation_total(build_ids)

            # Status matrix used to render progress bar for each build
            status_matrix = self._data.status_matrix(build_ids)

            for build in builds:
                bid = build['build']
                runs_total += build['runs_count']

                # skip if we have builds for which there are TestRuns but
                # no cases have been executed
                if bid not in status_matrix:
                    continue

                passed_count = status_matrix[bid].get('PASSED', 0)
                failed_count = status_matrix[bid].get('FAILED', 0)

                case_runs_count = build['case_runs_count']
                case_runs_total += build['case_runs_count']

                if case_runs_count:
                    build['passed_case_runs_percent'] = passed_count * 100.0 / case_runs_count
                    build['failed_case_runs_percent'] = failed_count * 100.0 / case_runs_count
                else:
                    build['passed_case_runs_percent'] = .0
                    build['failed_case_runs_percent'] = .0

                build['passed_case_runs_count'] = passed_count
                build['failed_case_runs_count'] = failed_count

            context.update({
                'total_runs_count': runs_total,
                # todo: what if plan product was changed after the TR was created
                # with that particular build ?
                'total_plans_count': TestRun.objects.filter(
                    build__in=build_ids
                ).values('plan').distinct().count(),
                'total_count': case_runs_total,
                'manual_count': automation_total.get('Manual', 0),
                'auto_count': automation_total.get('Auto', 0),
                'both_count': automation_total.get('Both', 0),
            })

        context.update({'builds': builds})
        return context

    def _initial_context(self):
        return {
            'form': self.form_class(),
            'builds': (),
        }

    def _get_report_data_context(self):
        if self._do_search():
            return self._report_data_context()
        return self._initial_context()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data.update(self._get_report_data_context())
        return data


def walk_matrix_row_by_row(matrix_dataset):
    status_total_line = None
    if None in matrix_dataset:
        status_total_line = matrix_dataset[None]
        del matrix_dataset[None]

    prev_plan = None
    # TODO: replace this with collections.OrderedDict after
    # upgrading to Python 2.7
    ordered_plans = sorted(matrix_dataset.items(),
                           key=lambda item: item[0].pk)
    for plan, runs in ordered_plans:
        plan_runs_count = len(runs)
        # TODO: and also this line
        ordered_runs = sorted(runs.items(),
                              key=lambda item: item[0].pk)
        for run, status_subtotal in ordered_runs:
            if plan == prev_plan:
                yield None, run, status_subtotal
            else:
                yield (plan, plan_runs_count), run, status_subtotal
                prev_plan = plan

    # Finally, yield the total line for rendering the complete report
    if status_total_line is not None:
        yield None, None, status_total_line


class CustomDetailReport(CustomReport):
    """Custom detail report

    Reuse CustomReport._search_context to get build and its summary statistics
    """

    template_name = 'report/custom_details.html'
    form_class = CustomSearchDetailsForm
    data_class = CustomDetailsReportData

    def _get_report_data_context(self):
        """Override to generate report by disabling check of argument a"""
        return self._report_data_context()

    def read_case_runs(self, build_ids, status_ids):
        """Generator for reading case runs and related objects"""
        case_runs = self._data.get_case_runs(build_ids, status_ids)
        bugs = self._data.get_case_runs_bugs(build_ids, status_ids)
        comments = self._data.get_case_runs_comments(build_ids, status_ids)
        
        for case_run in case_runs.iterator():
            related_bugs = bugs.get(case_run.pk, ())
            related_comments = comments.get(case_run.pk, ())
            yield case_run, related_bugs, related_comments

    def _report_data_context(self):
        data = {}
        form = self._get_search_form()
        if form.is_valid():
            summary_header_data = super(CustomDetailReport,
                                        self)._report_data_context()
            data.update(summary_header_data)
            
            build_ids = []
            for build in data['builds']:
                build_ids.append(build['build'])

            status_matrix = walk_matrix_row_by_row(
                self._data.generate_status_matrix(build_ids)
            )
            
            status_ids = (TestCaseRunStatus.objects.get(name=TestCaseRunStatus.FAILED).pk,)
            failed_case_runs = self.read_case_runs(build_ids, status_ids)
            
            status_ids = (TestCaseRunStatus.objects.get(name=TestCaseRunStatus.BLOCKED).pk,)
            blocked_case_runs = self.read_case_runs(build_ids, status_ids)

            data.update({
                'status_matrix': status_matrix,
                'failed_case_runs': failed_case_runs,
                'blocked_case_runs': blocked_case_runs,
            })
        else:
            data['report_errors'] = form.errors


        data['form'] = form
        return data


class TestingReportBase(TemplateView):
    """Base class for each type of report"""

    form_class = TestingReportForm

    def _get_form(self, data=None):
        product_id = self.request.GET.get('product')
        if data is not None:
            form = self.form_class(data)
        else:
            form = self.form_class()
        form.populate(product_id)
        return form

    def _init_context(self):
        """Provide very initial page without any report data

        Basically, in 2 senariors, user will be lead to this context

            - no parameters in query string
            - no report_type parameter in query string
        """
        return {
            'run_form': self._get_form(),
        }

    def _report_context(self):
        errors = None
        report_data = None

        if self.request.GET:
            form = self._get_form(self.request.GET)

            if form.is_valid():
                report_data = self.get_report_data(form)
            else:
                errors = form.errors

        request_path = remove_from_request_path(self.request, 'report_type')

        data = {
            'errors': errors,
            'request_path': request_path,
            'run_form': form,
            'report_data': report_data,
        }

        if request_path:
            data['path_without_build'] = remove_from_request_path(request_path, 'build')

        return data

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        if 'report_type' not in self.request.GET:
            context = self._init_context()
        else:
            context = self._report_context()

        data.update(context)
        data.update({
            'report_url': reverse('testing-report-case-runs'),
        })
        return data


class TestingReportByCaseRunTester(TestingReportBase,
                                   TestingReportByCaseRunTesterData):
    template_name = 'report/testing-report/per_build_report.html'


class TestingReportByCasePriority(TestingReportBase,
                                  TestingReportByCasePriorityData):
    template_name = 'report/testing-report/per_priority_report.html'


class TestingReportByPlanTags(TestingReportBase,
                              TestingReportByPlanTagsData):
    template_name = 'report/testing-report/by_plan_tag_with_rates.html'


class TestingReportByPlanTagsDetail(TestingReportBase,
                                    TestingReportByPlanTagsDetailData):
    template_name = 'report/testing-report/per_plan_tag.html'


class TestingReportByPlanBuild(TestingReportBase,
                               TestingReportByPlanBuildData):
    template_name = 'report/testing-report/by_plan_build_with_rates.html'


class TestingReportByPlanBuildDetail(TestingReportBase,
                                     TestingReportByPlanBuildDetailData):
    template_name = 'report/testing-report/per_plan_build.html'


class TestingReport(View):
    """Dispatch testing report according to report type"""

    testing_report_views = {
        None: TestingReportByCaseRunTester,
        'per_build_report': TestingReportByCaseRunTester,
        'per_priority_report': TestingReportByCasePriority,
        'runs_with_rates_per_plan_tag': TestingReportByPlanTags,
        'per_plan_tag_report': TestingReportByPlanTagsDetail,
        'runs_with_rates_per_plan_build': TestingReportByPlanBuild,
        'per_plan_build_report': TestingReportByPlanBuildDetail,
    }

    def _get_testing_report_view(self, report_type):
        view_class = self.testing_report_views.get(report_type, None)
        if view_class is None:
            return self.testing_report_views[None].as_view()
        return view_class.as_view()

    def get(self, request, *args, **kwargs):
        report_type = request.GET.get('report_type', None)
        view = self._get_testing_report_view(report_type)
        return view(request, *args, **kwargs)


def _get_testers_assignees_ids(case_runs):
    testers_ids = set()
    assignees_ids = set()

    for case_run in case_runs:
        if case_run.tested_by_id:
            testers_ids.add(case_run.tested_by_id)

        if case_run.assignee_id:
            assignees_ids.add(case_run.assignee_id)

    return list(testers_ids), list(assignees_ids)


class TestingReportCaseRuns(TestingReportBase, TestingReportCaseRunsData):
    template_name = 'report/caseruns.html'
    form_class = TestingReportCaseRunsListForm

    def get_context_data(self, **kwargs):
        data = super(TestingReportCaseRuns, self).get_context_data(**kwargs)

        query_args = self.request.GET
        form = self._get_form(query_args)

        if form.is_valid():
            test_case_runs = self.get_case_runs(form)

            data['test_case_runs_count'] = len(test_case_runs)
            data['test_case_runs'] = self.walk_case_runs(test_case_runs)
        else:
            data['form_errors'] = form.errors

        return data

    def walk_case_runs(self, test_case_runs):
        # todo: this is the same method as in testruns/views.py

        status_names = TestCaseRunStatus.get_names()
        priority_values = dict(Priority.objects.values_list('pk', 'value'))

        testers_ids, assignees_ids = _get_testers_assignees_ids(test_case_runs)
        testers = self.get_related_users(testers_ids)
        assignees = self.get_related_users(assignees_ids)

        for case_run in test_case_runs:
            status_name = status_names[case_run.case_run_status_id]
            priority_value = priority_values[case_run.case.priority_id]
            tester_username = testers.get(case_run.tested_by_id, None)
            assignee_username = assignees.get(case_run.assignee_id, None)
            yield case_run, status_name, priority_value, (
                case_run.assignee_id, assignee_username), (
                    case_run.tested_by_id, tester_username)
