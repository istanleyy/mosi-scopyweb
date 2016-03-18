from django.conf.urls import url
from . import views

urlpatterns = [
    # /scope_core/
    url(r'^$', views.index, name='index'),
    # /scope_core/info
    # url(r'^info/$', views.info, name='info'),
    # /scope_core/hist/TEST-00000-ABC/
    url(r'^hist/(?P<job_id>[^/]+)/$', views.hist, name='history'),
]