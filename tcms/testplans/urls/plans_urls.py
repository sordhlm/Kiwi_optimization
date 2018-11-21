# -*- coding: utf-8 -*-

from django.conf.urls import url

from tcms.testplans import views


urlpatterns = [
    url(r'^$', views.get_all, name='plans-all'),
    url(r'^search/$', views.search, name='plans-search'),
    url(r'^view/$', views.search, name='plans-view'),
    url(r'^new/$', views.new, name='plans-new'),
    url(r'^clone/$', views.clone, name='plans-clone'),
    url(r'^printable/$', views.printable, name='plans-printable'),
]
