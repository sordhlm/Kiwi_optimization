"""
    This module implements Kiwi TCMS interface to external issue tracking systems.
    :class:`tcms.issuetracker.types.IssueTrackerType` provides the interface
    while the rest of the classes in this module implement it! Refer to each
    implementor class for integration specifics!
"""

import os
import tempfile
from urllib.parse import urlencode

import jira
import github
import bugzilla
import redminelib
import datetime
from django.conf import settings

from tcms.issuetracker import bugzilla_integration
from tcms.issuetracker import jira_integration
from tcms.issuetracker import github_integration


class IssueTrackerType:
    """
        Represents actions which can be performed with issue trackers.
        This is a common interface for all issue trackers that Kiwi TCMS
        supports!
    """

    def __init__(self, tracker):
        """
            :tracker: - BugSystem object
        """
        self.tracker = tracker

    @classmethod
    def from_name(cls, name):
        """
            Return the class which matches ``name`` if it exists inside this
            module or raise an exception.
        """
        if name not in globals():
            raise NotImplementedError('IT of type %s is not supported' % name)
        return globals()[name]

    def report_issue_from_testcase(self, values):
        """
            When marking Test Case results inside a Test Run there is a
            'Report' link. When the `Report' link is clicked this method is called
            to help the user report an issue in the IT.

            This is implemented by constructing an URL string which will pre-fill
            bug details like steps to reproduce, product, version, etc from the
            test case. Then we open this URL into another browser window!

            :caserun: - TestCaseRun object
            :return: - string - URL
        """
        raise NotImplementedError()

    def add_testcase_to_issue(self, testcases, issue):
        """
            When adding issues to TestCase Run results there is a
            'Check to add test cases to Issue tracker' checkbox. If
            selected this method is called to link the bug report to the
            test case which was used to discover the bug.

            Usually this is implemented by adding a new comment pointing
            back to the test case via the internal RPC object.

            :testcases: - list of TestCase objects
            :issue: - Bug object
        """
        raise NotImplementedError()

    # pylint: disable = invalid-name, no-self-use
    def is_adding_testcase_to_issue_disabled(self):
        """
            When is linking a TC to a Bug report disabled?
            Usually when all the required credentials are provided.

            :return: - boolean
        """
        return not (self.tracker.api_url
                    and self.tracker.api_username
                    and self.tracker.api_password)

    def all_issues_link(self, _ids):
        """
            Used in testruns.views.get() aka run/report.html to produce
            a single URL which will open all reported issues into a single
            page in the Issue tracker. For example Bugzilla supports listing
            multiple bugs into a table. GitHub on the other hand doesn't
            support this functionality.

            :ids: - list of issues reported against test case runs

            :return: - None if not suported or string representing the URL
        """
        pass

class Redmine(IssueTrackerType):
    def __init__(self, tracker):
        super(Redmine, self).__init__(tracker)
        self.rpc = redminelib.Redmine(self.tracker.base_url,\
            username = self.tracker.api_username, password = self.tracker.api_password)

    def _get_user_id(self, name):
        users = self.rpc.user.filter(name=name)
        if len(users) == 1:
            return users[0].id
        return -1

    def add_testcase_to_issue(self, testcases, issue):
        pass

    def is_adding_testcase_to_issue_disabled(self):
        return not (self.tracker.base_url and self.tracker.api_password)

    def report_issue_from_testcase(self, values):
        """
            report issue to Redmine
        """
        # because of circular dependencies
        from tcms.testcases.models import TestCaseText
        caserun = values['case_run']
        args = {
            'title': 'Failed test: %s' % caserun.case.summary,
        }

        txt = caserun.get_text_with_version(case_text_version=caserun.case_text_version)

        if isinstance(txt, TestCaseText):
            setup = txt.setup
            action = txt.action
            effect = txt.effect
        else:
            setup = 'None'
            action = 'None'
            effect = 'None'

        comment = "Filed from caserun %s\n\n" % caserun.get_full_url()
        comment += "Product:\n%s\n\n" % caserun.run.plan.product.name
        comment += "DUT:\n%s\n\n" % values["dut"]
        comment += "Version-Release number of selected " \
                   "component (if applicable):\n"
        comment += "%s\n\n" % caserun.build.name
        comment += "Steps to Reproduce: \n%s\n%s\n\n" % (setup, action)
        comment += "Actual results: \n<describe what happened>\n\n"
        comment += "Expected results:\n%s\n\n" % effect
        args['body'] = comment

        tmp = dir(self.rpc.project.get('kiwi'))
        assign_id = self._get_user_id(values['assign_to'])
        if assign_id == -1:
            return "assign_to id is not valid", -1
        redmine_issue = self.rpc.issue.create(
            project_id=values['product'],
            subject=args['title'],
            description=comment,
            status_id=2,
            priority_id=2,
            assigned_to_id=assign_id
        )
        url = self.tracker.base_url
        if not url.endswith('/'):
            url += '/'

        return url+'issues/'+str(redmine_issue.id), redmine_issue.id

    def gen_bug_trend_data(self, values):
        date_label = []
        total_bugs = []
        open_bugs = []
        close_bugs = []
        try:
            project = self.rpc.project.get(values['product'])
        except:
            return {'date': date_label, 'total':total_bugs, 'open':open_bugs, 'close':close_bugs}

        issues = self.rpc.issue.filter(project_id=values['product'], sort='id', status_id='*')
        now = datetime.datetime.now().date()

        date = issues[0].created_on.date()
        while date < now:
            bopen = 0
            bclose = 0
            btotal = 0
            for issue in issues:
                if issue.created_on.date() <= date:
                    btotal += 1
                    if hasattr(issue, "closed_on"):
                        if (issue.closed_on.date() <= date):
                            bclose += 1
                elif issue.created_on.date() > date:
                    break
            bopen = btotal - bclose
            date_label.append(date.strftime('%Y-%m-%d'))
            total_bugs.append(btotal)
            close_bugs.append(bclose)
            open_bugs.append(bopen)
            date = date + datetime.timedelta(days=values['delta'])
        return {'date': date_label, 'total':total_bugs, 'open':open_bugs, 'close':close_bugs}



class Bugzilla(IssueTrackerType):
    """
        Support for Bugzilla. Requires:

        :api_url: - the XML-RPC URL for your Bugzilla instance
        :api_username: - a username registered in Bugzilla
        :api_password: - the password for this username

        You can also provide the ``BUGZILLA_AUTH_CACHE_DIR`` setting (in ``product.py``)
        to control where authentication cookies for Bugzilla will be saved. If this
        is not provided a temporary directory will be used each time we try to login
        into Bugzilla!
    """
    def __init__(self, tracker):
        super(Bugzilla, self).__init__(tracker)

        # directory for Bugzilla credentials
        bugzilla_cache_dir = getattr(
            settings,
            "BUGZILLA_AUTH_CACHE_DIR",
            tempfile.mkdtemp(prefix='.bugzilla-')
        )
        if not os.path.exists(bugzilla_cache_dir):
            os.makedirs(bugzilla_cache_dir, 0o700)

        # passing user & password will attemt to authenticate
        # when the __init__ method runs. Do it here so that we don't
        # have to do it everywhere else where it might be needed.
        self.rpc = bugzilla.Bugzilla(
            tracker.api_url,
            user=self.tracker.api_username,
            password=self.tracker.api_password,
            cookiefile=bugzilla_cache_dir + 'cookie',
            tokenfile=bugzilla_cache_dir + 'token',
        )

    def add_testcase_to_issue(self, testcases, issue):
        for case in testcases:
            bugzilla_integration.BugzillaThread(self.rpc, case, issue).start()

    def all_issues_link(self, ids):
        if not self.tracker.base_url:
            return None

        if not self.tracker.base_url.endswith('/'):
            self.tracker.base_url += '/'

        return self.tracker.base_url + 'buglist.cgi?bugidtype=include&bug_id=%s' % ','.join(ids)

    def report_issue_from_testcase(self, values):
        # because of circular dependencies
        from tcms.testcases.models import TestCaseText
        caserun = values['case_run']
        args = {}
        args['cf_build_id'] = caserun.run.build.name

        txt = caserun.get_text_with_version(case_text_version=caserun.case_text_version)

        if isinstance(txt, TestCaseText):
            setup = txt.setup
            action = txt.action
            effect = txt.effect
        else:
            setup = 'None'
            action = 'None'
            effect = 'None'

        comment = "Filed from caserun %s\n\n" % caserun.get_full_url()
        comment += "Version-Release number of selected " \
                   "component (if applicable):\n"
        comment += '%s\n\n' % caserun.build.name
        comment += "Steps to Reproduce: \n%s\n%s\n\n" % (setup, action)
        comment += "Actual results: \n<describe what happened>\n\n"
        comment += "Expected results:\n%s\n\n" % effect

        args['comment'] = comment
        args['component'] = caserun.case.component.values_list('name',
                                                               flat=True)
        args['product'] = caserun.run.plan.product.name
        args['short_desc'] = 'Test case failure: %s' % caserun.case.summary
        args['version'] = caserun.run.product_version

        url = self.tracker.base_url
        if not url.endswith('/'):
            url += '/'

        return url + 'enter_bug.cgi?' + urlencode(args, True)


class JIRA(IssueTrackerType):
    """
        Support for JIRA. Requires:

        :api_url: - the API URL for your JIRA instance
        :api_username: - a username registered in JIRA
        :api_password: - the password for this username

        Additional control can be applied via the ``JIRA_OPTIONS`` configuration
        setting (in ``product.py``). By default this setting is not provided and
        the code uses ``jira.JIRA.DEFAULT_OPTIONS`` from the ``jira`` Python module!
    """
    def __init__(self, tracker):
        super(JIRA, self).__init__(tracker)

        if hasattr(settings, 'JIRA_OPTIONS'):
            options = settings.JIRA_OPTIONS
        else:
            options = None

        # b/c jira.JIRA tries to connect when object is created
        # see https://github.com/kiwitcms/Kiwi/issues/100
        if not self.is_adding_testcase_to_issue_disabled():
            self.rpc = jira.JIRA(
                tracker.api_url,
                basic_auth=(self.tracker.api_username, self.tracker.api_password),
                options=options,
            )

    def add_testcase_to_issue(self, testcases, issue):
        for case in testcases:
            jira_integration.JiraThread(self.rpc, case, issue).start()

    def all_issues_link(self, ids):
        if not self.tracker.base_url:
            return None

        if not self.tracker.base_url.endswith('/'):
            self.tracker.base_url += '/'

        return self.tracker.base_url + 'issues/?jql=issueKey%%20in%%20(%s)' % '%2C%20'.join(ids)

    def report_issue_from_testcase(self, values):
        """
            For the HTML API description see:
            https://confluence.atlassian.com/display/JIRA050/Creating+Issues+via+direct+HTML+links
        """
        # because of circular dependencies
        from tcms.testcases.models import TestCaseText
        caserun = values['case_run']
        # note: your jira instance needs to have the same projects
        # defined otherwise this will fail!
        project = self.rpc.project(caserun.run.plan.product.name)

        try:
            issue_type = self.rpc.issue_type_by_name('Bug')
        except KeyError:
            issue_type = self.rpc.issue_types()[0]

        args = {
            'pid': project.id,
            'issuetype': issue_type.id,
            'summary': 'Failed test: %s' % caserun.case.summary,
        }

        try:
            # apparently JIRA can't search users via their e-mail so try to
            # search by username and hope that it matches
            tested_by = caserun.tested_by
            if not tested_by:
                tested_by = caserun.assignee

            args['reporter'] = self.rpc.user(tested_by.username).key
        except jira.JIRAError:
            pass

        txt = caserun.get_text_with_version(case_text_version=caserun.case_text_version)

        if isinstance(txt, TestCaseText):
            setup = txt.setup
            action = txt.action
            effect = txt.effect
        else:
            setup = 'None'
            action = 'None'
            effect = 'None'

        comment = "Filed from caserun %s\n\n" % caserun.get_full_url()
        comment += "Product:\n%s\n\n" % caserun.run.plan.product.name
        comment += "Component(s):\n%s\n\n" % caserun.case.component.values_list('name', flat=True)
        comment += "Version-Release number of selected " \
                   "component (if applicable):\n"
        comment += "%s\n\n" % caserun.build.name
        comment += "Steps to Reproduce: \n%s\n%s\n\n" % (setup, action)
        comment += "Actual results: \n<describe what happened>\n\n"
        comment += "Expected results:\n%s\n\n" % effect
        args['description'] = comment

        url = self.tracker.base_url
        if not url.endswith('/'):
            url += '/'

        return url + '/secure/CreateIssueDetails!init.jspa?' + urlencode(args, True)


class GitHub(IssueTrackerType):
    """
        Support for GitHub. Requires:

        :base_url: - URL to a GitHub repository for which we're going to report issues
        :api_password: - GitHub API token.

        .. note::

            You can leave the ``api_url`` and ``api_username`` fields blank because
            the integration code doesn't use them!

        .. note::

            GitHub does not support displaying multiple issues in a table format like
            Bugzilla and JIRA do. This means that in Test Case Run Report view you will
            see GitHub issues listed one by one and there will not be a link to open all
            of them inside GitHub's interface!
    """
    def __init__(self, tracker):
        super(GitHub, self).__init__(tracker)

        # NOTE: we use an access token so only the password field is required
        self.rpc = github.Github(self.tracker.api_password)

    def add_testcase_to_issue(self, testcases, issue):
        for case in testcases:
            github_integration.GitHubThread(self.rpc, self.tracker, case, issue).start()

    def is_adding_testcase_to_issue_disabled(self):
        return not (self.tracker.base_url and self.tracker.api_password)

    def report_issue_from_testcase(self, values):
        """
            GitHub only supports title and body parameters
        """
        # because of circular dependencies
        from tcms.testcases.models import TestCaseText
        caserun = values['case_run']
        args = {
            'title': 'Failed test: %s' % caserun.case.summary,
        }

        txt = caserun.get_text_with_version(case_text_version=caserun.case_text_version)

        if isinstance(txt, TestCaseText):
            setup = txt.setup
            action = txt.action
            effect = txt.effect
        else:
            setup = 'None'
            action = 'None'
            effect = 'None'

        comment = "Filed from caserun %s\n\n" % caserun.get_full_url()
        comment += "Product:\n%s\n\n" % caserun.run.plan.product.name
        comment += "Component(s):\n%s\n\n" % caserun.case.component.values_list('name', flat=True)
        comment += "Version-Release number of selected " \
                   "component (if applicable):\n"
        comment += "%s\n\n" % caserun.build.name
        comment += "Steps to Reproduce: \n%s\n%s\n\n" % (setup, action)
        comment += "Actual results: \n<describe what happened>\n\n"
        comment += "Expected results:\n%s\n\n" % effect
        args['body'] = comment

        url = self.tracker.base_url
        if not url.endswith('/'):
            url += '/'

        return url + '/issues/new?' + urlencode(args, True)

