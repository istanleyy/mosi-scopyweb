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
from django.contrib import admin
from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets
from dashing.utils import router as dash_router
from .widgets import JobListWidget, JobCountWidget, MachineCycleWidget, MachineStatusWidget

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff')

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

rest_router = routers.DefaultRouter()
rest_router.register(r'users', UserViewSet)

dash_router.register(JobListWidget, 'joblist_widget')
dash_router.register(JobCountWidget, 'jobcount_widget')
dash_router.register(MachineCycleWidget, 'machinecycle_widget')
dash_router.register(MachineStatusWidget, 'machinestatus_widget')

urlpatterns = [
    url(r'^', include(rest_router.urls)),
    url(r'^admin/', admin.site.urls),
    url(r'^scope_core/', include('scope_core.urls')),
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^dashboard/', include(dash_router.urls)),
]
