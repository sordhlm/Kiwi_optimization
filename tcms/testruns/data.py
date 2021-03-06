# -*- coding: utf-8 -*-

from itertools import groupby

from django.conf import settings
from django.db.models import F
from django.contrib.contenttypes.models import ContentType
from django_comments.models import Comment

from tcms.testcases.models import Bug
from tcms.testruns.models import TestCaseRun
from tcms.testruns.models import TestCaseRunStatus


def get_run_bug_ids(run_id):
    """Get list of pairs of bug ID and bug link that are added to a run

    :param int run_id: ID of test run.
    :return: list of pairs of bug ID and bug link.
    :rtype: list
    """
    return Bug.objects.values(
        'bug_id',
        'bug_system',
        'bug_system__tracker_type',
        'bug_system__url_reg_exp'
    ).distinct().filter(case_run__run=run_id)


class TestCaseRunDataMixin:
    """Data for test case runs"""

    @staticmethod
    def stats_mode_case_runs(case_runs):
        """Statistics from case runs mode

        @param case_runs: iteratable object to access each case run
        @type case_runs: iterable, list, tuple
        @return: mapping between mode and the count. Example return value is
            { 'manual': I, 'automated': J, 'manual_automated': N }
        @rtype: dict
        """
        manual_count = 0
        automated_count = 0
        manual_automated_count = 0

        for case_run in case_runs:
            is_automated = case_run.case.is_automated
            if is_automated == 1:
                automated_count += 1
            elif is_automated == 0:
                manual_count += 1
            else:
                manual_automated_count += 1

        return {
            'manual': manual_count,
            'automated': automated_count,
            'manual_automated': manual_automated_count,
        }

    @staticmethod
    def get_case_runs_bugs(run_pk):
        """Get case run bugs for run report

        :param int run_pk: run's pk whose case runs' bugs will be retrieved.
        :return: the mapping between case run id and bug information containing
            formatted bug URL.
        :rtype: dict
        """

        bugs = Bug.objects.filter(
            case_run__run=run_pk
        ).values(
            'case_run',
            'bug_id',
            'bug_system__url_reg_exp'
        ).order_by('case_run')

        rows = []
        for row in bugs:
            row['bug_url'] = row['bug_system__url_reg_exp'] % row['bug_id']
            rows.append(row)

        case_run_bugs = {}
        for case_run_id, bugs_info in groupby(rows, lambda row: row['case_run']):
            case_run_bugs[case_run_id] = list(bugs_info)

        return case_run_bugs

    @staticmethod
    def get_case_runs_comments(run_pk):
        """Get case runs' comments

        @param run_pk: run's pk whose comments will be retrieved.
        @type run_pk: int
        @return: the mapping between case run id and comments
        @rtype: dict
        """
        # note: cast to string b/c object_pk is a Textield and PostgreSQL
        # doesn't like TEXT in <list of integers>
        # in Django 1.10 we have the Cast() function for similar cases, see
        # https://docs.djangoproject.com/en/1.10/ref/models/database-functions/#cast
        object_pks = []
        for test_case_run in TestCaseRun.objects.filter(run=run_pk).only('pk'):
            object_pks.append(str(test_case_run.pk))

        comments = Comment.objects.filter(
            site=settings.SITE_ID,
            content_type=ContentType.objects.get_for_model(TestCaseRun).pk,
            is_public=True,
            is_removed=False,
            object_pk__in=object_pks
        ).annotate(
            case_run_id=F('object_pk')
        ).values(
            'case_run_id',
            'submit_date',
            'comment',
            'user_name'
        ).order_by('case_run_id')

        rows = []
        for row in comments:
            rows.append(row)

        case_run_comments = {}
        for key, groups in groupby(rows, lambda row: row['case_run_id']):
            case_run_comments[int(key)] = list(groups)

        return case_run_comments

    @staticmethod
    def get_summary_stats(case_runs):
        """Get summary statistics from case runs

        Statistics targets:
        - the number of pending test case runs, whose status is IDLE
        - the number of completed test case runs, whose status are PASSED,
          ERROR, FAILED, WAIVED

        @param case_runs: iterable object containing case runs
        @type case_runs: iterable
        @return: a mapping between statistics target and its value
        @rtype: dict
        """
        idle_count = 0
        complete_count = 0
        fail_count = 0
        block_count = 0
        pass_count = 0
        complete_status_names = TestCaseRunStatus.complete_status_names
        idle_status_names = TestCaseRunStatus.idle_status_names
        failure_status_names = TestCaseRunStatus.failure_status_names
        block_status_names = TestCaseRunStatus.block_status_names
        pass_status_names = TestCaseRunStatus.pass_status_names

        for case_run in case_runs:
            status_name = case_run.case_run_status.name
            if status_name in idle_status_names:
                idle_count += 1
            elif status_name in complete_status_names:
                complete_count += 1

            if status_name in failure_status_names:
                fail_count += 1
            elif status_name in block_status_names:
                block_count += 1
            elif status_name in pass_status_names:
                pass_count += 1

        return {'idle': idle_count, 'complete': complete_count, \
                'fail': fail_count, 'block': block_count, 'pass': pass_count}
