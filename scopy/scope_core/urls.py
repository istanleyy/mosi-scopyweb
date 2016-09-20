from django.conf.urls import url
from . import views

app_name = 'scopecore'
urlpatterns = [
    # /scope_core/
    url(r'^$', views.index, name='index'),
    # /scope_core/hist/TEST-00000-ABC/
    url(r'^hist/(?P<job_id>[^/]+)/$', views.hist, name='history'),
    # /scope_core/getlog/activity
    url(r'^getlog/(?P<logname>[^/]+)/$', views.getlog, name='log'),
    # /scope_core/softreset
    url(r'^softreset/$', views.softreset, name='reset'),
]