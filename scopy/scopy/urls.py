"""scopy URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.views.generic.base import RedirectView
from django.contrib import admin
from dashing.utils import router
from .widgets import JobListWidget, JobCountWidget, MachineCycleWidget, MachineStatusWidget

router.register(JobListWidget, 'joblist_widget')
router.register(JobCountWidget, 'jobcount_widget')
router.register(MachineCycleWidget, 'machinecycle_widget')
router.register(MachineStatusWidget, 'machinestatus_widget')

urlpatterns = [
    url(r'^favicon\.ico$', RedirectView.as_view('/static/favicon.ico', permanent=True)),
    url(r'^admin/', admin.site.urls),
    url(r'^scope_core/', include('scope_core.urls')),
    url(r'^rest-api/', include('rest_framework.urls')),
    url(r'^dashboard/', include(router.urls)),
]
