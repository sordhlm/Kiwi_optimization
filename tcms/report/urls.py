# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='overall/', permanent=True)),
    url(r'^overall/$', views.overall, name='report-overall'),
    #url(r'^product/(?P<product_id>\d+)/overview/$', views.overview, name='report-overview'),
    url(r'^product/(?P<product_id>\d+)/overview/$', views.ProductReport.as_view(), name='report-overview'),
    url(r'^product/(?P<product_id>\d+)/build/$', views.ProductBuildReport.as_view(),
        name='report-overall-product-build'),
    url(r'^product/(?P<product_id>\d+)/version/$', views.ProductVersionReport.as_view(),
        name='report-overall-product-version'),
    url(r'^product/(?P<product_id>\d+)/component/$', views.ProductComponentReport.as_view(),
        name='report-overall-product-component'),
    url(r'custom/$', views.CustomReport.as_view(), name='report-custom'),
    url(r'^custom/details/$', views.CustomDetailReport.as_view(), name='report-custom-details'),

    url(r'^testing/$', views.TestingReport.as_view(), name='testing-report'),
    url(r'^testing/case-runs/$', views.TestingReportCaseRuns.as_view(),
        name='testing-report-case-runs'),
    url(r'^performance/$', views.performance_report, name='performance-report'),
    url(r'^query_perf_group/$', views.query_perf_group, name='performance-group'),
    url(r'^delete_perf_group/$', views.delete_perf_group, name='performance-delete'),
    url(r'^query_perf_result/$', views.query_perf_result, name='performance-result'),
    url(r'^query_perf_detail/$', views.query_perf_detail, name='performance-detail'),
    url(r'^update_bug_trend/$', views.update_bug_trend, name='report-update-bug-trend'),
    url(r'^update_progress_trend/$', views.update_progress_trend, name='report-update_progress_trend'),
]
