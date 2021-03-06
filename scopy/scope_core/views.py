from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from .models import ProductionDataTS, Job, SessionManagement, Machine
from scope_core.core import xmlparser

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
    if logname == 'activity' or logname == 'debug':
        if logname == 'activity':
            filename = 'scopepi.log'
            url = '/protected/celery_err.log'
        else:
            filename = 'scopepi_debug.log'
            url = '/protected/scopepi_debug.log'
        response['Content-Disposition'] = "attachment; filename={0}".format(filename)
        response['X-Accel-Redirect'] = url
        return response
    else:
        return HttpResponseNotFound()

def clearlogs(request):
    return HttpResponse("clear logs")

def softreset(request):
    # Set all jobs inactive
    active_jobs = Job.objects.filter(active=True)
    if active_jobs:
        active_jobs.update(active=False)
        for job in active_jobs:
            job.save()
    # Reset session
    session = SessionManagement.objects.first()
    session.reset()
    # Reset machine
    machine = Machine.objects.first()
    machine.reset()
    # Clear message buffer
    xmlparser.flushUnsyncMsg()
    # Reload dashboard
    return HttpResponseRedirect('/dashboard/')