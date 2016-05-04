#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Manage Job activities and send corresponding Scope message
to the server
"""

from djcelery.models import IntervalSchedule
from lxml import etree
from scope_core.models import Machine, Job, ProductionDataTS, SessionManagement
from . import xmlparser
from . import request_sender

def processQueryResult(source, data, task=None):
    if source == 'opStatus':
        machine = Machine.objects.first()
        if data[0] == u'離線':
            print 'Device is offline!'
            if machine.opmode != 0:
                machine.opmode = 0
                machine.save()
                request_sender.sendPostRequest('false:bye', 'text')
        elif str(data[0])[0] == '1':
            if machine.opmode != 1:
                machine.opmode = 1
                machine.save()
                print 'Device in manual mode.'
        elif str(data[0])[0] == '2':
            if machine.opmode != 2:
                machine.opmode = 2
                machine.save()
                print 'Device in semi-auto mode.'
        elif str(data[0])[0] == '3':
            if machine.opmode != 3:
                machine.opmode = 3
                machine.save()
                print 'Device in auto mode.'
        else:
            pass
        
    elif source == 'opMetrics':
        mct = data[0]
        pcs = data[1]
        moldSerial = str(data[2])
        
        session = SessionManagement.objects.first()
        if evalCOCondition() == 'mold':
            performChangeOver(session, task, moldSerial)
        
        if task.interval.every != session.job.ct:
            intv, created = IntervalSchedule.objects.get_or_create(
                every=session.job.ct, period='seconds'
                )
            task.interval_id = intv.id
            task.save()
        
        if session.job.inprogress:
            dataEntry = ProductionDataTS.objects.create(job=session.job)
            dataEntry.output = pcs
            dataEntry.mct = mct
            dataEntry.save()
        
            scopemsg = xmlparser.getJobUpdateXml(pcs, mct)
            request_sender.sendPostRequest(scopemsg)

    elif source == 'alarmStatus':
        session = SessionManagement.objects.first()
        
        if str(data[2]) == '1':
            if not session.errflag:
                if session.errid != data[1]:
                    session.errid = data[1]
                session.errflag = True
                session.save()
                sendEventMsg(4, session.errid)
        else:
            if session.errflag:
                session.errflag = False
                session.save()
                sendEventMsg(1)
    
    else:
        pass

def sendEventMsg(type, code=""):
    scopemsg = xmlparser.getJobEventXml(type, code)
    request_sender.sendPostRequest(scopemsg)
    
def init():
    request_sender.sendPostRequest('false:up')
    activeJobs = Job.objects.filter(active=True)
    if not activeJobs:
        getJobsFromServer()
    
def getJobsFromServer():
    request_sender.sendGetRequest()

def evalCOCondition():
    return 'mold'

def performChangeOver(session, task, moldserial):
    if moldserial != session.job.moldid:
        # if the mold id of the production data has changed, 
        # need to update session reference to the job using the new mold.
        session.job = Job.objects.get(moldid=moldserial)
        session.save()
            
    if task is None:
        print '!!! Unable to update task period due to missing argument !!!'
    else:
        # Compare polling period with retrieved mct value
        if session.job.ct != task.interval.every:
            intv, created = IntervalSchedule.objects.get_or_create(
                every=session.job.ct, period='seconds'
                )
            task.interval_id = intv.id
            task.save()