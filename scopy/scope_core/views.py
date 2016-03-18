from django.shortcuts import render
from django.http import HttpResponse
from .models import ProductionDataTS

def index(request):
    return HttpResponse("Welcome to the Scope Device microserver!")
    
# Shows current device information (list of jobs, current running status)
def info(request):
    pass

# Shows production history for the job with the given job ID
def hist(request, job_id):
    job_history = ProductionDataTS.objects.filter(job__jobid__contains=job_id)
    if not job_history:
        return HttpResponse("No record found.")
    else:
        return HttpResponse(job_history)