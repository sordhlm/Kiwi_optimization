# -*- coding: utf-8 -*-
import time
from datetime import datetime
from http import HTTPStatus

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.db.models import Count
from django.db.models import Q
from django.forms import ValidationError
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from django.views.generic.base import View

from django_comments.models import Comment

from tcms.core.utils import clean_request
from tcms.core.utils.validations import validate_bug_id
from tcms.management.models import Priority, Tag, Node
from tcms.testcases.forms import CaseBugForm
from tcms.testcases.models import TestCasePlan, TestCaseStatus, BugSystem, Category, Suite
from tcms.testcases.views import get_selected_testcases
from tcms.testplans.models import TestPlan
from tcms.testruns.data import get_run_bug_ids
from tcms.testruns.data import TestCaseRunDataMixin
from tcms.testruns.forms import NewRunForm, SearchRunForm, BaseRunForm
from tcms.testruns.models import TestRun, TestCaseRun, TestCaseRunStatus
from tcms.issuetracker.types import IssueTrackerType
from tcms.testexecutor.types import TestExecutorType
# from tcms.rest_client.rest_client import RestClient
from production_rest_client.rest_client import RestClient
from wkhtmltopdf.views import PDFTemplateView
from tcms.testruns.forms import DocumentForm
from tcms.testruns.models import Document

class CustomPDF(PDFTemplateView, TestCaseRunDataMixin):
    filename = 'my_report_pdf.pdf'
    template_name = 'run/report.html'
    cmd_options = {
        'margin-top': 3,
    }
    def get(self, request):
        self.run_id = request.GET.get("id")
        return super(CustomPDF, self).get(request, self.run_id)
    def get_context_data(self, **kwargs):
        run = TestRun.objects.select_related('manager', 'plan').get(pk=self.run_id)

        case_runs = TestCaseRun.objects.filter(
            run=run
        ).select_related(
            'case_run_status', 'case', 'tested_by'
        ).only(
            'close_date',
            'case_run_status__name',
            'case__category__name',
            'case__summary', 'case__is_automated',
            'case__is_automated_proposed',
            'tested_by__username'
        )
        mode_stats = self.stats_mode_case_runs(case_runs)
        summary_stats = self.get_summary_stats(case_runs)

        test_case_run_bugs = []
        bug_system_types = {}
        for _bug in get_run_bug_ids(self.run_id):
            # format the bug URLs based on DB settings
            test_case_run_bugs.append((
                _bug['bug_id'],
                _bug['bug_system__url_reg_exp'] % _bug['bug_id'],
            ))
            # find out all unique bug tracking systems which were used to record
            # bugs in this particular test run. we use this data for reporting
            if _bug['bug_system'] not in bug_system_types:
                # store a tracker type object for producing the report URL
                tracker_class = IssueTrackerType.from_name(_bug['bug_system__tracker_type'])
                bug_system = BugSystem.objects.get(pk=_bug['bug_system'])
                tracker = tracker_class(bug_system)
                bug_system_types[_bug['bug_system']] = (tracker, [])

            # store the list of bugs as well
            bug_system_types[_bug['bug_system']][1].append(_bug['bug_id'])

        # list of URLs which opens all bugs reported to every different
        # issue tracker used in this test run
        report_urls = []
        for (issue_tracker, ids) in bug_system_types.values():
            report_url = issue_tracker.all_issues_link(ids)
            # if IT doesn't support this feature or report url is not configured
            # the above method will return None
            if report_url:
                report_urls.append((issue_tracker.tracker.name, report_url))

        case_run_bugs = self.get_case_runs_bugs(run.pk)
        comments = self.get_case_runs_comments(run.pk)

        for case_run in case_runs:
            case_run.bugs = case_run_bugs.get(case_run.pk, ())
            case_run.user_comments = comments.get(case_run.pk, [])

        context = super().get_context_data(**kwargs)
        context.update({
            'test_run': run,
            'test_case_runs': case_runs,
            'test_case_runs_count': len(case_runs),
            'test_case_run_bugs': test_case_run_bugs,
            'mode_stats': mode_stats,
            'summary_stats': summary_stats,
            'report_urls': report_urls,
        })

        return context

@require_GET
def genPDF(request):
    filename = 'my_pdf.pdf'
    template_name = 'run/report.html'
    #print("start genPDF")
    return PDFTemplateView.as_view(filename=filename, template_name=template_name)(request,1)

@require_POST
@permission_required('testruns.add_testrun')
def new(request):
    """Display the create test run page."""

    # If from_plan does not exist will redirect to plans for select a plan
    if not request.POST.get('from_plan'):
        messages.add_message(request,
                             messages.ERROR,
                             _('Creating a TestRun requires a TestPlan, select one'))
        return HttpResponseRedirect(reverse('plans-search'))

    plan_id = request.POST.get('from_plan')
    # case is required by a test run
    # NOTE: currently this is handled in JavaScript but in the TestRun creation
    # form cases can be deleted
    if not request.POST.get('case'):
        messages.add_message(request,
                             messages.ERROR,
                             _('Creating a TestRun requires at least one TestCase'))
        return HttpResponseRedirect(reverse('test_plan_url_short', args=[plan_id]))

    # Ready to write cases to test plan
    test_cases = get_selected_testcases(request)
    test_plan = TestPlan.objects.get(plan_id=plan_id)

    # note: ordered by case_id for test_show_create_new_run_page()
    tcs_values = test_cases.select_related('author',
                                           'case_status',
                                           'category',
                                           'priority').order_by('case_id')

    if request.POST.get('POSTING_TO_CREATE'):
        form = NewRunForm(request.POST)
        form.populate(product_id=test_plan.product_id)

        if form.is_valid():
            # Process the data in form.cleaned_data
            default_tester = form.cleaned_data['default_tester']

            test_run = TestRun.objects.create(
                product_version=test_plan.product_version,
                stop_date=None,
                summary=form.cleaned_data.get('summary'),
                notes=form.cleaned_data.get('notes'),
                plan=test_plan,
                build=form.cleaned_data['build'],
                manager=form.cleaned_data['manager'],
                default_tester=default_tester,
            )

            try:
                assignee_tester = User.objects.get(username=default_tester)
            except ObjectDoesNotExist:
                assignee_tester = None

            loop = 1
            for case in form.cleaned_data['case']:
                try:
                    tcp = TestCasePlan.objects.get(plan=test_plan, case=case)
                    sortkey = tcp.sortkey
                except ObjectDoesNotExist:
                    sortkey = loop * 10

                test_run.add_case_run(case=case,
                                      sortkey=sortkey,
                                      assignee=assignee_tester)
                loop += 1

            return HttpResponseRedirect(
                reverse('testruns-get', args=[test_run.run_id, ])
            )

    else:
        form = NewRunForm(initial={
            'summary': 'Test run for %s' % test_plan.name,
            'manager': test_plan.author.email,
            'default_tester': request.user.email,
            'notes': '',
        })
        form.populate(product_id=test_plan.product_id)

    context_data = {
        'test_plan': test_plan,
        'test_cases': tcs_values,
        'form': form,
    }
    return render(request, 'testruns/mutable.html', context_data)


@require_GET
def search(request):
    form = SearchRunForm(request.GET)
    form.populate(product_id=request.GET.get('product'))

    context_data = {
        'form': form,
    }
    return render(request, 'testruns/search.html', context_data)


def open_run_get_case_runs(request, run):
    """Prepare for case runs list in a TestRun page

    This is an internal method. Do not call this directly.
    """
    tcrs = run.case_run.select_related('run', 'case')
    tcrs = tcrs.only('run__run_id',
                     'run__plan',
                     'case_run_status',
                     'assignee', 'tested_by',
                     'case_text_version',
                     'sortkey',
                     'case__summary',
                     'case__is_automated_proposed',
                     'case__is_automated',
                     'case__priority',
                     'case__category__name',
                     'node__ip')
    # Get the bug count for each case run
    # 5. have to show the number of bugs of each case run
    tcrs = tcrs.annotate(num_bug=Count('case_run_bug', distinct=True))

    # todo: is this last distinct necessary
    tcrs = tcrs.distinct()
    # Continue to search the case runs with conditions
    # 4. case runs preparing for render case runs table
    tcrs = tcrs.filter(**clean_request(request))
    order_by = request.GET.get('order_by')
    if order_by:
        tcrs = tcrs.order_by(order_by)
    else:
        tcrs = tcrs.order_by('sortkey', 'pk')
    return tcrs


def open_run_get_comments_subtotal(case_run_ids):
    content_type = ContentType.objects.get_for_model(TestCaseRun)
    query_set = Comment.objects.filter(
        content_type=content_type,
        site_id=settings.SITE_ID,
        object_pk__in=case_run_ids,
        is_removed=False).values('object_pk').annotate(comment_count=Count('pk')).order_by(
            'object_pk')

    result = ((int(row['object_pk']), row['comment_count']) for row in query_set)
    return dict(result)


def open_run_get_users(case_runs):
    tester_ids = set()
    assignee_ids = set()
    for case_run in case_runs:
        if case_run.tested_by_id:
            tester_ids.add(case_run.tested_by_id)
        if case_run.assignee_id:
            assignee_ids.add(case_run.assignee_id)
    testers = User.objects.filter(
        pk__in=tester_ids).values_list('pk', 'username')
    assignees = User.objects.filter(
        pk__in=assignee_ids).values_list('pk', 'username')
    return (dict(testers.iterator()), dict(assignees.iterator()))

def update_node_status(node):
    executor_class = TestExecutorType.from_name(settings.RUNNER_NAME)
    client = executor_class(node.ip, timeout=0.5)
    node.state = client.check_status()
    print("[update_node_status] node state:%s"%node.state)
    node.save()

def update_runnig_test_status(case_run):
    if case_run.runkey:
        executor_class = TestExecutorType.from_name(settings.RUNNER_NAME)
        client = executor_class(case_run.node.ip, timeout=0.5)
        case_run.markResult(client.query_test_result(case_run.runkey))

@require_POST
def update_all_nodes(request):
    nodes = Node.objects.all()
    #print(nodes)

    dst = []
    executor_class = TestExecutorType.from_name("NodeMonitor")
    client = executor_class()
    for node in nodes:
        info = client.get_info(node.ip)
        #update_node_status(node)
        if info:
            node_up = node.update(info[0])
        else:
            node_up = node
        dst.append(node_up.serialize())
    client.release_sql()
    #return HttpResponseRedirect(reverse('core-views-index'))
    return JsonResponse({'ok':1, 'result': dst})

@require_POST
def update_tag(request):
    ip = request.POST.get('ip')
    tag = request.POST.get('text')
    key = request.POST.get('key')
    node = Node.objects.get(ip=ip)
    print(node)
    print(ip)
    print(tag)
    node.update({key:tag})
    return JsonResponse({'ok':1, 'msg': 'update done'})

@require_POST
def get_test_detail(request):
    ip = request.POST.get('ip')
    dst = {}
    #print(ip)
    executor_class = TestExecutorType.from_name("NodeMonitor")
    client = executor_class()

    test_detail = client.get_test_detail(ip)
    test_usage = client.get_node_usage(ip)
    #update_node_status(node)
    #print(test_detail)
    #print("##############")
    #print(test_usage)
    context = {
        'detail': test_detail,
        'usage': test_usage
    }
    client.release_sql()
    return JsonResponse(context)

@require_POST
def get_test_usage(request):
    dst = {}
    return JsonResponse({'ok':1, 'result': dst})

@require_GET
def get(request, run_id, template_name='run/get.html'):
    """Display testrun's detail"""
    # Get the test run
    try:
        # 1. get test run itself
        test_run = TestRun.objects.select_related().get(run_id=run_id)
    except ObjectDoesNotExist:
        raise Http404

    # Get the test case runs belong to the run
    # 2. get test run's all case runs
    test_case_runs = open_run_get_case_runs(request, test_run)

    case_run_status = TestCaseRunStatus.objects.only('pk', 'name').order_by('pk')

    # Count the status
    # 3. calculate number of case runs of each status
    status_stats_result = test_run.stats_caseruns_status(case_run_status)

    # Get the test case run bugs summary
    # 6. get the number of bugs of this run
    test_case_run_bugs_count = test_run.get_bug_count()

    # Get tag list of testcases
    # 7. get tags
    # Get the list of testcases belong to the run
    test_cases = []
    node_list = []
    case_run_status_name = TestCaseRunStatus.get_names()
    for test_case_run in test_case_runs:
        test_cases.append(test_case_run.case_id)
        if test_case_run.node:
            #if settings.REST_API_RUN:
            #    if ('RUNNING' in case_run_status_name[test_case_run.case_run_status_id]) or \
            #        ('PAUSED' in case_run_status_name[test_case_run.case_run_status_id]):
            #        print("case:%s, ip:%s"%(test_case_run.case_id,test_case_run.node.ip))
            #        update_runnig_test_status(test_case_run)
            if (test_case_run.node.ip is not "--default--"):
                node_list.append(test_case_run.node)

    tags = Tag.objects.filter(case__in=test_cases).values_list('name', flat=True)
    tags = list(set(tags))
    tags.sort()
    node_list = set(node_list)
    print(node_list)
    for node in node_list:
        update_node_status(node)
        print("node state:%s"%node.state)
    def walk_case_runs():
        """Walking case runs for helping rendering case runs table"""
        priorities = dict(Priority.objects.values_list('pk', 'value'))
        #nodes = dict(Node.objects.values_list('pk', 'name'))
        testers, assignees = open_run_get_users(test_case_runs)
        #test_case_run_pks = []
        #for test_case_run in test_case_runs:
        #    test_case_run_pks.append(test_case_run.pk)
        comments_subtotal = open_run_get_comments_subtotal(test_cases)

        for case_run in test_case_runs:
            #node = nodes.get(case_run.node.id) if case_run.node else "Not Configured"
            node = case_run.node if case_run.node else None

            yield (case_run,
                   node,
                   testers.get(case_run.tested_by_id, None),
                   assignees.get(case_run.assignee_id, None),
                   priorities.get(case_run.case.priority_id),
                   case_run_status_name[case_run.case_run_status_id],
                   comments_subtotal.get(case_run.pk, 0))
    assignees = User.objects.all()
    context_data = {
        'test_run': test_run,
        'from_plan': request.GET.get('from_plan', False),
        'test_case_runs': walk_case_runs(),
        'test_case_runs_count': len(test_case_runs),
        'status_stats': status_stats_result,
        'test_case_run_bugs_count': test_case_run_bugs_count,
        'test_case_run_status': case_run_status,
        'priorities': Priority.objects.all(),
        'case_own_tags': tags,
        'bug_trackers': BugSystem.objects.all(),
        'nodes': Node.objects.all(),
        'choosen_nodes': node_list,
        'assignees':assignees
    }
    print("finish generate data")
    return render(request, template_name, context_data)


@permission_required('testruns.change_testrun')
def edit(request, run_id):
    """Edit test plan view"""

    try:
        test_run = TestRun.objects.select_related().get(run_id=run_id)
    except ObjectDoesNotExist:
        raise Http404

    # If the form is submitted
    if request.method == "POST":
        form = BaseRunForm(request.POST)
        form.populate(product_id=test_run.plan.product_id)

        # FIXME: Error handler
        if form.is_valid():
            test_run.summary = form.cleaned_data['summary']
            # Permission hack
            if test_run.manager == request.user or test_run.plan.author == request.user:
                test_run.manager = form.cleaned_data['manager']
            test_run.default_tester = form.cleaned_data['default_tester']
            test_run.build = form.cleaned_data['build']
            test_run.product_version = test_run.plan.product_version
            test_run.notes = form.cleaned_data['notes']
            test_run.save()

            return HttpResponseRedirect(reverse('testruns-get', args=[run_id, ]))
    else:
        # Generate a blank form
        form = BaseRunForm(initial={
            'summary': test_run.summary,
            'manager': test_run.manager.email,
            'default_tester': (test_run.default_tester and
                               test_run.default_tester.email or None),
            'version': test_run.product_version_id,
            'build': test_run.build_id,
            'notes': test_run.notes,
        })
        form.populate(test_run.plan.product_id)

    context_data = {
        'test_run': test_run,
        'test_plan': test_run.plan,
        'form': form,
    }
    return render(request, 'testruns/mutable.html', context_data)


class TestRunReportView(TemplateView, TestCaseRunDataMixin):
    """Test Run report"""

    template_name = 'run/report.html'
    run_id = None

    def get(self, request, run_id):
        self.run_id = run_id
        return super(TestRunReportView, self).get(request, run_id)

    def get_context_data(self, **kwargs):
        """Generate report for specific TestRun

        There are four data source to generate this report.
        1. TestRun
        2. Test case runs included in the TestRun
        3. Comments associated with each test case run
        4. Statistics
        5. bugs
        """
        run = TestRun.objects.select_related('manager', 'plan').get(pk=self.run_id)

        case_runs = TestCaseRun.objects.filter(
            run=run
        ).select_related(
            'case_run_status', 'case', 'tested_by'
        ).only(
            'close_date',
            'case_run_status__name',
            'case__category__name',
            'case__summary', 'case__is_automated',
            'case__is_automated_proposed',
            'tested_by__username'
        )
        mode_stats = self.stats_mode_case_runs(case_runs)
        summary_stats = self.get_summary_stats(case_runs)

        test_case_run_bugs = []
        bug_system_types = {}
        for _bug in get_run_bug_ids(self.run_id):
            # format the bug URLs based on DB settings
            test_case_run_bugs.append((
                _bug['bug_id'],
                _bug['bug_system__url_reg_exp'] % _bug['bug_id'],
            ))
            # find out all unique bug tracking systems which were used to record
            # bugs in this particular test run. we use this data for reporting
            if _bug['bug_system'] not in bug_system_types:
                # store a tracker type object for producing the report URL
                tracker_class = IssueTrackerType.from_name(_bug['bug_system__tracker_type'])
                bug_system = BugSystem.objects.get(pk=_bug['bug_system'])
                tracker = tracker_class(bug_system)
                bug_system_types[_bug['bug_system']] = (tracker, [])

            # store the list of bugs as well
            bug_system_types[_bug['bug_system']][1].append(_bug['bug_id'])

        # list of URLs which opens all bugs reported to every different
        # issue tracker used in this test run
        report_urls = []
        for (issue_tracker, ids) in bug_system_types.values():
            report_url = issue_tracker.all_issues_link(ids)
            # if IT doesn't support this feature or report url is not configured
            # the above method will return None
            if report_url:
                report_urls.append((issue_tracker.tracker.name, report_url))

        case_run_bugs = self.get_case_runs_bugs(run.pk)
        comments = self.get_case_runs_comments(run.pk)

        for case_run in case_runs:
            case_run.bugs = case_run_bugs.get(case_run.pk, ())
            case_run.user_comments = comments.get(case_run.pk, [])

        context = super().get_context_data(**kwargs)
        context.update({
            'test_run': run,
            'test_case_runs': case_runs,
            'test_case_runs_count': len(case_runs),
            'test_case_run_bugs': test_case_run_bugs,
            'mode_stats': mode_stats,
            'summary_stats': summary_stats,
            'report_urls': report_urls,
        })

        return context

@require_GET
@permission_required('testruns.change_testrun')
def bug(request, case_run_id, template_name='run/execute_case_run.html'):
    """Process the bugs for case runs."""

    class CaseRunBugActions:

        def __init__(self, request, case_run, template_name):
            self.request = request
            self.case_run = case_run
            self.template_name = template_name

        def add(self):
            if not self.request.user.has_perm('testcases.add_bug'):
                return JsonResponse({'rc': 1, 'response': 'Permission denied'})

            bug_id = request.GET.get('bug_id')
            bug_system_id = request.GET.get('bug_system_id')

            try:
                validate_bug_id(bug_id, bug_system_id)
            except ValidationError as error:
                return JsonResponse({'rc': 1,
                                     'response': str(error)})

            bz_external_track = True if request.GET.get('bz_external_track',
                                                        False) else False

            try:
                test_case_run.add_bug(bug_id=bug_id,
                                      bug_system_id=bug_system_id,
                                      bz_external_track=bz_external_track)
            except ValueError as error:
                msg = str(error) if str(error) else 'Failed to add bug %s' % bug_id
                return JsonResponse({'rc': 1,
                                     'response': msg})

            return JsonResponse({'rc': 0,
                                 'response': 'ok',
                                 'run_bug_count': self.get_run_bug_count(),
                                 'caserun_bugs_count': self.case_run.get_bugs_count()})

        def file(self):
            values = {}
            bug_system_id = request.GET.get('bug_system_id')
            bug_system = BugSystem.objects.get(pk=bug_system_id)
            product_name = request.GET.get('product_name')
            dut = request.GET.get('dut')
            assign_to = request.GET.get('assign_to')
            values['product'] = product_name
            values['assign_to'] = assign_to
            values['case_run'] = self.case_run
            values['dut'] = dut
            if bug_system.base_url:
                tracker = IssueTrackerType.from_name(bug_system.tracker_type)(bug_system)
                url, bug_id = tracker.report_issue_from_testcase(values)
                if bug_id != -1:
                    response = {'rc': 0, 'response': url}
                    try:
                        test_case_run.add_bug(bug_id=bug_id,
                                      bug_system_id=bug_system_id)
                    except ValueError as error:
                        msg = str(error) if str(error) else 'Failed to add bug %s' % bug_id
                        response = {'rc': 1, 'response': msg}
                else:
                    response = {'rc': 1, 'response': url}
            else:
                response = {'rc': 1, 'response': 'Enable Redmine reporting to this Issue Tracker '
                                             'by configuring its base_url!'}
            return JsonResponse(response)

        def remove(self):
            if not self.request.user.has_perm('testcases.delete_bug'):
                response = {'rc': 1, 'response': 'Permission denied'}
                return self.render(response=response)

            try:
                bug_id = self.request.GET.get('bug_id')
                run_id = self.request.GET.get('case_run')
                self.case_run.remove_bug(bug_id, run_id)
            except ObjectDoesNotExist as error:
                return JsonResponse({'rc': 1, 'response': str(error)})

            return JsonResponse({'rc': 0,
                                 'response': 'ok',
                                 'run_bug_count': self.get_run_bug_count()})

        def render_form(self):
            form = CaseBugForm(initial={
                'case_run': self.case_run.case_run_id,
                'case': self.case_run.case_id,
            })
            if self.request.GET.get('type') == 'table':
                return HttpResponse(form.as_table())

            return HttpResponse(form.as_p())

        def get_run_bug_count(self):
            run = self.case_run.run
            return run.get_bug_count()

    try:
        test_case_run = TestCaseRun.objects.get(case_run_id=case_run_id)
    except ObjectDoesNotExist:
        raise Http404

    case_run_bug_actions = CaseRunBugActions(request=request,
                                             case_run=test_case_run,
                                             template_name=template_name)

    func = getattr(case_run_bug_actions, request.GET['a'], None)
    if func is None:
        return JsonResponse({'rc': 1,
                             'response': 'Unrecognizable actions'})

    return func()

def handle_uploaded_file(file):
    time_now = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    save_name = "%s_%s"%(time_now, file)
    with open('%s/%s'%(settings.FW_BIN_SAVE_PATH, save_name), 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    print("%s/%s"%(settings.FW_BIN_SAVE_PATH, save_name))
    return "%s/%s"%(settings.FW_BIN_SAVE_PATH, save_name)

@require_POST
def updateFW(request):
    # print(request.__dict__)
    file = request.FILES["bin_file"]
    ip = request.POST.getlist("ip")
    slot = request.POST.getlist("slot")
    did = request.POST.getlist("did")
    nodes = []
    ip = ip[0].split(",")
    did = did[0].split(",")
    slot = slot[0].split(",")
    for i in range(len(ip)):
        node = {"ip": ip, "did": slot, "slot": did}
        node["ip"] = ip[i]
        node["did"] = did[i]
        node["slot"] = slot[i]
        nodes.append(node)
    print(nodes)
    if request.is_ajax():
        fw_file = handle_uploaded_file(file)
        # form = DocumentForm(request.POST, request.FILES)
        # if form.is_valid():
        #     print("this is form \n")
        #     newdoc = Document(docfile=request.FILES['bin_file'])
        #     newdoc.save()
        # print(file)
    print("\n\n**Start Update FW ...%s\n\n"%file)
    result = {}
    if settings.REST_API_RUN:
        for i in range(len(nodes)):
            executor_class = TestExecutorType.from_name(settings.RUNNER_NAME)
            client = executor_class(nodes[i]["ip"], timeout=5)
            device_id = 1 if 'None' in did[i] else eval(did[i])
            slot_id = 2 if 'None' in slot[i] else eval(slot[i])
            # print("did: %d, slot: %d"%(device_id, slot_id))
            ret = client.update_fw(fw_file, device_index=device_id, slot=slot_id)
            print(ret)
            result[nodes[i]["ip"]] = ret
    else:
        result = "No Runner Found"

    return JsonResponse({'result': result})


@require_POST
def clone(request, run_id):
    """Clone cases from filter caserun"""

    test_run = get_object_or_404(TestRun, run_id=run_id)
    confirmed_case_status = TestCaseStatus.get_confirmed()
    disabled_cases = 0

    if request.POST.get('case_run'):
        test_cases = []
        for test_case_run in test_run.case_run.filter(pk__in=request.POST.getlist('case_run')):
            if test_case_run.case.case_status == confirmed_case_status:
                test_cases.append(test_case_run.case)
            else:
                disabled_cases += 1
    else:
        test_cases = None

    if not test_cases:
        messages.add_message(request,
                             messages.ERROR,
                             _('At least one TestCase is required'))
        return HttpResponseRedirect(reverse('testruns-get', args=[run_id]))

    form = NewRunForm(initial={
        'summary': _('Clone of ') + test_run.summary,
        'notes': test_run.notes,
        'manager': test_run.manager,
        'build': test_run.build_id,
        'default_tester': test_run.default_tester,
    })
    form.populate(product_id=test_run.plan.product_id)

    context_data = {
        'is_cloning': True,
        'disabled_cases': disabled_cases,
        'test_plan': test_run.plan,
        'test_cases': test_cases,
        'form': form,
    }
    return render(request, 'testruns/mutable.html', context_data)


@permission_required('testruns.change_testrun')
def change_status(request, run_id):
    """Change test run finished or running"""
    test_run = get_object_or_404(TestRun, run_id=run_id)

    test_run.update_completion_status(request.GET.get('finished') == '1')
    test_run.save()

    return HttpResponseRedirect(reverse('testruns-get', args=[run_id, ]))


@require_POST
@permission_required('testruns.delete_testcaserun')
def remove_case_run(request, run_id):
    """Remove specific case run from the run"""

    # Ignore invalid case run ids
    case_run_ids = []
    for item in request.POST.getlist('case_run'):
        try:
            case_run_ids.append(int(item))
        except (ValueError, TypeError):
            pass

    # If no case run to remove, no further operation is required, just return
    # back to run page immediately.
    if not case_run_ids:
        return HttpResponseRedirect(reverse('testruns-get',
                                            args=[run_id, ]))

    run = get_object_or_404(TestRun.objects.only('pk'), pk=run_id)

    # Restrict to delete those case runs that belongs to run
    TestCaseRun.objects.filter(run_id=run.pk, pk__in=case_run_ids).delete()

    caseruns_exist = TestCaseRun.objects.filter(run_id=run.pk).exists()
    if caseruns_exist:
        redirect_to = 'testruns-get'
    else:
        redirect_to = 'add-cases-to-run'

    return HttpResponseRedirect(reverse(redirect_to, args=[run_id, ]))

@method_decorator(permission_required('testruns.add_testcaserun'), name='dispatch')
class AddTreeCasesToRunView(View):
    """Add cases to a TestRun"""

    def post(self, request, run_id):
        # Selected cases' ids to add to run
        test_cases_ids = request.POST.getlist('treecase')

        if not test_cases_ids:
            # user clicked Update button without selecting new Test Cases
            # to be dded to TestRun
            messages.add_message(request,
                                 messages.ERROR,
                                 _('At least one TestCase is required'))
            return HttpResponseRedirect(reverse('add-cases-to-run', args=[run_id]))

        try:
            test_run = TestRun.objects.select_related('plan').only('plan__plan_id').get(
                run_id=run_id)
        except ObjectDoesNotExist:
            raise Http404

        test_case_runs_ids = test_run.case_run.values_list('case', flat=True)

        # avoid add cases that are already in current run with pk run_id
        test_case_exist_ids = [str(i) for i in test_case_runs_ids]

        test_cases_ids = set(test_cases_ids) - set(test_case_exist_ids)
        test_plan = test_run.plan
        test_cases = test_run.plan.case.filter(case_status__name='CONFIRMED').select_related(
            'default_tester').only('default_tester__id').filter(
                case_id__in=test_cases_ids)

        for test_case in test_cases:
            test_run.add_case_run(case=test_case)

        return HttpResponseRedirect(reverse('testruns-get',
                                            args=[test_run.run_id, ]))

@method_decorator(permission_required('testruns.add_testcaserun'), name='dispatch')
class AddCasesToRunView(View):
    """Add cases to a TestRun"""

    def post(self, request, run_id):
        # Selected cases' ids to add to run
        test_cases_ids = request.POST.getlist('case')
        if not test_cases_ids:
            # user clicked Update button without selecting new Test Cases
            # to be dded to TestRun
            messages.add_message(request,
                                 messages.ERROR,
                                 _('At least one TestCase is required'))
            return HttpResponseRedirect(reverse('add-cases-to-run', args=[run_id]))

        try:
            test_cases_ids = list(map(int, test_cases_ids))
        except (ValueError, TypeError):
            # this will happen only on malicious requests
            messages.add_message(request,
                                 messages.ERROR,
                                 _('TestCase ID is not a valid integer'))
            return HttpResponseRedirect(reverse('add-cases-to-run', args=[run_id]))

        try:
            test_run = TestRun.objects.select_related('plan').only('plan__plan_id').get(
                run_id=run_id)
        except ObjectDoesNotExist:
            raise Http404

        test_case_runs_ids = test_run.case_run.values_list('case', flat=True)

        # avoid add cases that are already in current run with pk run_id
        test_cases_ids = set(test_cases_ids) - set(test_case_runs_ids)

        test_plan = test_run.plan
        test_cases = test_run.plan.case.filter(case_status__name='CONFIRMED').select_related(
            'default_tester').only('default_tester__id').filter(
                case_id__in=test_cases_ids)

        if request.POST.get('_use_plan_sortkey'):
            test_case_pks = (test_case.pk for test_case in test_cases)
            query_set = TestCasePlan.objects.filter(
                plan=test_plan, case__in=test_case_pks).values('case', 'sortkey')
            sort_keys_in_plan = dict((row['case'], row['sortkey']) for row in query_set.iterator())
            for test_case in test_cases:
                sort_key = sort_keys_in_plan.get(test_case.pk, 0)
                test_run.add_case_run(case=test_case, sortkey=sort_key)
        else:
            for test_case in test_cases:
                test_run.add_case_run(case=test_case)

        return HttpResponseRedirect(reverse('testruns-get',
                                            args=[test_run.run_id, ]))

    def get(self, request, run_id):
        # information about TestRun, used in the page header
        test_run = TestRun.objects.select_related(
            'plan', 'manager', 'build'
        ).only(
            'plan', 'plan__name',
            'manager__email', 'build__name'
        ).get(run_id=run_id)

        # select all CONFIRMED cases from the TestPlan that is a parent
        # of this particular TestRun
        #default_cate = Category.objects.get(product=test_run.plan.product, name='--default--')
        #category = Category.objects.filter(product=test_run.plan.product)
        #tree = genNodeList(test_run.plan,default_cate,category)

        rows = TestCasePlan.objects.values(
            'case',
            'case__category__suite__product_id',
            'case__create_date', 'case__summary',
            'case__category__name',
            'case__category_id',
            'case__category__parent_category_id',
            'case__priority__value',
            'case__author__username'
        ).filter(
            plan_id=test_run.plan,
            case__case_status=TestCaseStatus.objects.filter(name='CONFIRMED').first().pk
        ).order_by('case')  # order b/c of PostgreSQL

        # also grab a list of all TestCase IDs which are already present in the
        # current TestRun so we can mark them as disabled and not allow them to
        # be selected
        test_case_runs = TestCaseRun.objects.filter(run=run_id).values_list('case', flat=True)

        data = {
            'product_id':rows[0]["case__category__suite__product_id"],
            'test_run': test_run,
            'confirmed_cases': rows,
            'confirmed_cases_count': rows.count(),
            'test_case_runs_count': len(test_case_runs),
            'exist_case_run_ids': test_case_runs,
            'confirmed_status_id': TestCaseStatus.objects.filter(name='CONFIRMED').first().pk,
            'suites': Suite.objects.filter(product=test_run.plan.product_id)
        }

        return render(request, 'run/assign_case.html', data)

@require_GET
def cc(request, run_id):  # pylint: disable=invalid-name
    """Add or remove cc from a test run"""

    test_run = get_object_or_404(TestRun, run_id=run_id)
    action = request.GET.get('do')
    username_or_email = request.GET.get('user')
    context_data = {'test_run': test_run, 'is_ajax': True}

    if action:
        if not username_or_email:
            context_data['message'] = 'User name or email is required by this operation'
        else:
            try:
                user = User.objects.get(
                    Q(username=username_or_email) |
                    Q(email=username_or_email)
                )
            except ObjectDoesNotExist:
                context_data['message'] = 'The user you typed does not exist in database'
            else:
                if action == 'add':
                    test_run.add_cc(user=user)

                if action == 'remove':
                    test_run.remove_cc(user=user)

    return render(request, 'run/get_cc.html', context_data)


@require_POST
def update_case_run_text(request, run_id):
    """Update the IDLE cases to newest text"""

    test_run = get_object_or_404(TestRun, run_id=run_id)

    if request.POST.get('case_run'):
        test_case_runs = test_run.case_run.filter(pk__in=request.POST.getlist('case_run'))
    else:
        test_case_runs = test_run.case_run.all()

    test_case_runs = test_case_runs.filter(case_run_status__name='IDLE')

    count = 0
    updated_test_case_runs = ''
    for test_case_run in test_case_runs:
        latest_text = test_case_run.latest_text().case_text_version
        if test_case_run.case_text_version != latest_text:
            count += 1
            updated_test_case_runs += '<li>%s: %s -> %s</li>' % (
                test_case_run.case.summary, test_case_run.case_text_version, latest_text
            )
            test_case_run.case_text_version = latest_text
            test_case_run.save()

    info = "<p>%s</p><ul>%s</ul>" % (_("%d CaseRun(s) updated:") % count, updated_test_case_runs)
    message_level = messages.INFO
    if count:
        message_level = messages.SUCCESS

    messages.add_message(request, message_level, info)
    return HttpResponseRedirect(reverse('testruns-get', args=[run_id]))


def get_caseruns_of_runs(runs, kwargs=None):
    """
    Filtering argument -
        priority
        tester
        plan tag
    """

    if kwargs is None:
        kwargs = {}
    plan_tag = kwargs.get('plan_tag', None)
    if plan_tag:
        runs = runs.filter(plan__tag__name=plan_tag)
    caseruns = TestCaseRun.objects.filter(run__in=runs)
    priority = kwargs.get('priority', None)
    if priority:
        caseruns = caseruns.filter(case__priority__pk=priority)
    tester = kwargs.get('tester', None)
    if not tester:
        caseruns = caseruns.filter(tested_by=None)
    if tester:
        caseruns = caseruns.filter(tested_by__pk=tester)
    status = kwargs.get('status', None)
    if status:
        caseruns = caseruns.filter(case_run_status__name__iexact=status)
    return caseruns


@method_decorator(permission_required('testruns.change_testcaserun'), name='dispatch')
class UpdateAssigneeView(View):
    """Updates TestCaseRun.assignee. Called from the front-end."""

    http_method_names = ['post']

    def post(self, request):
        assignee = request.POST.get('assignee')
        try:
            user = User.objects.get(username=assignee)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=assignee)
            except User.DoesNotExist:
                return JsonResponse({'rc': 1,
                                     'response': _('User %s not found!' % assignee)},
                                    status=HTTPStatus.NOT_FOUND)

        object_ids = request.POST.getlist('ids[]')

        for caserun_pk in object_ids:
            test_case_run = get_object_or_404(TestCaseRun, pk=int(caserun_pk))
            test_case_run.assignee = user
            test_case_run.save()

        return JsonResponse({'rc': 0, 'response': 'ok'})


@method_decorator(permission_required('testruns.change_testcaserun'), name='dispatch')
class UpdateCaseRunStatusView(View):
    """Updates TestCaseRun.case_run_status_id. Called from the front-end."""

    http_method_names = ['post']

    def post(self, request):
        status_id = int(request.POST.get('status_id'))
        object_ids = request.POST.getlist('object_pk[]')
        case_run_status_name = TestCaseRunStatus.get_names()
        for caserun_pk in object_ids:
            test_case_run = get_object_or_404(TestCaseRun, pk=int(caserun_pk))
            test_case_run.tested_by = request.user
            test_case_run.close_date = datetime.now()
            test_case_run.notes = ""
            ret = self.manageTest(test_case_run, status_id)
            if ret['result']:
                test_case_run.case_run_status_id = status_id
                test_case_run.notes = ret['msg']
                test_case_run.save()

        return JsonResponse({'rc': 0, 'response': 'ok'})

    def manageTest(self, test_case_run, status_id):
        if not settings.REST_API_RUN:
            return {'result':1, 'msg':'No Runner is configured'}
        case_run_status_name = TestCaseRunStatus.get_names()
        pre_stat = case_run_status_name[test_case_run.case_run_status_id]
        cur_stat = case_run_status_name[status_id]
        if ('PAUSED' in pre_stat) or ('RUNNING' in pre_stat):
            if 'RUNNING' in cur_stat:
                return {'result':1, 'msg':'Test is already running'}
            elif 'IDLE' in cur_stat:
                return self.cancelTest(test_case_run)
        else:
            if 'RUNNING' in cur_stat:
                return self.runTest(test_case_run)
        return {'result':1, 'msg':'No available Test operation'}

    def runTest(self, test_case_run):
        host = test_case_run.node.ip
        test_case_script = test_case_run.case.script
        if test_case_run.node:
           if test_case_script != "" and host != "":
                executor_class = TestExecutorType.from_name(settings.RUNNER_NAME)
                client = executor_class(host, timeout=10)
                test_case_run.markResult(client.run_test_in_async_mode(test_case_script))
                return {'result':0, 'msg':'ok'}
           else:
               #print("Run case Error. please check node(ip) or case script")
               return {'result':1, 'msg':'No IP or Script'}
        else:
             return {'result':1, 'msg':'No Node'}

    def cancelTest(self, test_case_run):
        if test_case_run.node:
            host = test_case_run.node.ip
            print("[CancelTest] host:%s, key:%s"%(host, test_case_run.runkey))
            if (host != "") and (test_case_run.runkey):
                executor_class = TestExecutorType.from_name(settings.RUNNER_NAME)
                client = executor_class(host, timeout=5)
                test_case_run.markResult(client.cancel_test(test_case_run.runkey))
                return {'result':0, 'msg':'ok'}
            else:
                return {'result':1, 'msg':'No IP or Key'}
        else:
            return {'result':1, 'msg':'No Node'}

@method_decorator(permission_required('testruns.change_testcaserun'), name='dispatch')
class UpdateCaseNodeView(View):
    """Updates TestCaseRun.case_run_status_id. Called from the front-end."""

    http_method_names = ['post']

    def post(self, request):
        node_name = request.POST.get('node_name')
        object_ids = request.POST.getlist('object_pk[]')
        node = get_object_or_404(Node, name=(node_name))
        #print(node)
        for caserun_pk in object_ids:
            test_case_run = get_object_or_404(TestCaseRun, pk=int(caserun_pk))
            test_case_run.node = node
            test_case_run.close_date = datetime.now()
            test_case_run.save()

        return JsonResponse({'rc': 0, 'response': 'ok'})

@method_decorator(permission_required('testruns.change_testcaserun'), name='dispatch')
class UpdateCaseAssignView(View):
    """Updates TestCaseRun.case_run_status_id. Called from the front-end."""

    http_method_names = ['post']

    def post(self, request):
        assignee_id = request.POST.get('assign')
        object_ids = request.POST.getlist('object_pk[]')
        assignee = get_object_or_404(User, id=(assignee_id))
        #print(node)
        for caserun_pk in object_ids:
            test_case_run = get_object_or_404(TestCaseRun, pk=int(caserun_pk))
            test_case_run.assignee = assignee
            test_case_run.close_date = datetime.now()
            test_case_run.save()

        return JsonResponse({'rc': 0, 'response': 'ok'})


