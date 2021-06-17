# -*- coding: utf-8 -*-

from django.conf.urls import url

from .. import views

urlpatterns = [
    url(r'^new/$', views.new, name='testruns-new'),
    url(r'^(?P<run_id>\d+)/$', views.get, name='testruns-get'),
    url(r'^(?P<run_id>\d+)/clone/$', views.clone, name='testruns-clone'),
    url(r'^(?P<run_id>\d+)/edit/$', views.edit, name='testruns-edit'),

    url(r'^(?P<run_id>\d+)/report/$', views.TestRunReportView.as_view(),
        name='run-report'),

    url(r'^(?P<run_id>\d+)/changestatus/$', views.change_status, name='testruns-change_status'),
    url(r'^(?P<run_id>\d+)/removecaserun/$', views.remove_case_run,
        name='testruns-remove_case_run'),

    url(r'^(?P<run_id>\d+)/assigncase/$', views.AddCasesToRunView.as_view(),
        name='add-cases-to-run'),
    url(r'^(?P<run_id>\d+)/assigncase-tree/$', views.AddTreeCasesToRunView.as_view(),
        name='add-tree-cases-to-run'),

    url(r'^(?P<run_id>\d+)/cc/$', views.cc, name='testruns-cc'),
    url(r'^(?P<run_id>\d+)/update/$', views.update_case_run_text,
        name='testruns-update_case_run_text'),
    url(r'^update-assignee/$', views.UpdateAssigneeView.as_view()),
    url(r'^case-run-update-status/$', views.UpdateCaseRunStatusView.as_view(),
        name='testruns-update_caserun_status'),
    url(r'^case-run-update-node/$', views.UpdateCaseNodeView.as_view(),
        name='testruns-update_caserun_node'),
    url(r'^case-run-update-assign/$', views.UpdateCaseAssignView.as_view(),
        name='case-run-update_caserun_assignee'),
    url(r'^export_run_report_pdf/$', views.CustomPDF.as_view(), name='testruns-genpdf'),
    url(r'^update_fw/$', views.updateFW, name='testruns-updatefw'),
    url(r'^update_nodes/$', views.update_all_nodes, name='testruns-update-nodes'),
    url(r'^get_test_detail/$', views.get_test_detail, name='testruns-test-detail'),
    url(r'^get_test_usage/$', views.get_test_usage, name='testruns-test-usage'),
    url(r'^update_tag/$', views.update_tag, name='testruns-update-tag'),
    #url(r'^export_run_report_pdf/$', PDFTemplateView.as_view(template_name='run/report.html',
    #                                       filename='my_pdf.pdf'), name='pdf'),
]
