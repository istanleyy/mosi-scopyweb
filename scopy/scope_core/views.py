from django.shortcuts import render
from django.http import HttpResponse
from .models import ProductionDataTS, Document

def index(request):
    return HttpResponse("Welcome to the Scope Device microserver!")

# Shows production history for the job with the given job ID
def hist(request, job_id):
    job_history = ProductionDataTS.objects.filter(job__jobid__contains=job_id)
    if not job_history:
        return HttpResponse("No record found.")
    else:
        return HttpResponse(job_history)

@login_required
def getlog(request):
    response = HttpResponse()
    url = 'protected/celery_worker.log'
    response['Content-Type'] = ""
    response['X-Accel-Redirect'] = url
    return response