from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
from .models import ProductionDataTS

def index(request):
    return HttpResponse("Welcome to the Scope Device microserver!")

# Shows production history for the job with the given job ID
def hist(request, job_id):
    job_history = ProductionDataTS.objects.filter(job__jobid__contains=job_id)
    if not job_history:
        return HttpResponse("No record found.")
    else:
        return HttpResponse(job_history)

def getlog(request, logname):
    response = HttpResponse()
    response['Content-Type'] = ""
    if logname == 'activity':
        url = '/protected/celery_worker.log'
        response['Content-Disposition'] = "attachment; filename={0}".format("scopepi.log")
        response['X-Accel-Redirect'] = url
        return response
    else:
        return HttpResponseNotFound()

def softreset(request):
    pass