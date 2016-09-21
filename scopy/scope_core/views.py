from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from .models import ProductionDataTS, Job, SessionManagement, Machine

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
    # Reload dashboard
    return HttpResponseRedirect('/dashboard/')