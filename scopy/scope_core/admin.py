from django.contrib import admin

# Register your models here.
from .models import Machine
from .models import Job
from .models import SessionManagement
from .models import UserActivity
from .models import ProductionDataTS

admin.site.site_header = 'ScopeDevice Admin'
admin.site.site_title = 'Device Admin'

admin.site.register(Machine)
admin.site.register(Job)
admin.site.register(SessionManagement)
admin.site.register(UserActivity)
admin.site.register(ProductionDataTS)