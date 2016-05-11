#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT 
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

job_control.py
    Manage Job activities and send corresponding Scope message to the server
"""

from djcelery.models import IntervalSchedule
from lxml import etree
from scope_core.models import Machine, Job, ProductionDataTS, SessionManagement
from scope_core.device import device_definition as const
from . import xmlparser
from . import request_sender

def processQueryResult(source, data, task=None):
    if source == 'opStatus':
        if data == const.OFFLINE:
            request_sender.sendPostRequest('false:bye', 'text')
        else:
            pass
        
    elif source == 'opMetrics':
        mct = data[0]
        pcs = data[1]
        moldSerial = str(data[2])
        
        machine = Machine.objects.first()
        session = SessionManagement.objects.first()
        if evalCOCondition(machine, session) == 'mold':
            performChangeOver(session, task, moldSerial)
        
        if task.interval.every != session.job.ct:
            intv, created = IntervalSchedule.objects.get_or_create(
                every=session.job.ct, period='seconds'
                )
            task.interval_id = intv.id
            task.save()
        
        if session.job.inprogress:
            dataEntry = ProductionDataTS.objects.create(job=session.job, output=pcs, mct=mct)
            sendUpdateMsg(pcs, mct)

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

def sendUpdateMsg(pcs=None, mct=None):
    if pcs is None:
        pcs = ProductionDataTS.objects.last().output
    if mct is None:
        mct = ProductionDataTS.objects.last().mct
    scopemsg = xmlparser.getJobUpdateXml(pcs, mct)
    request_sender.sendPostRequest(scopemsg)
    
def init():
    request_sender.sendPostRequest('false:up')
    activeJobs = Job.objects.filter(active=True)
    if not activeJobs:
        jobxml = getJobsFromServer()
        if jobxml is not None:
            xmlparser.isScopeXml(jobxml)
    
def getJobsFromServer():
    return request_sender.sendGetRequest()

def evalCOCondition(machine, session):
    # Evaluate CO condition only if machine is not offline nor in auto mode
    if (0 < machine.opmode < 3):
    
        # Conditions for the machine to enter mold change status:
        #   - current job's demanded quantity has been made
        #   - machine is not having erronous downtime
        #   - motor of the machine is switched OFF
        if (ProductionDataTS.objects.last().output >= session.job.quantity and
            not session.errflag and
            not Machine.objects.first().motorOnOffStatus):
            return 'mold'
        
        # Conditions for the machine to enter material pipe cleaning status:
        #   - machine is not having erronous downtime
        #   - machine's mold adjustment switch is ON
        elif (not session.errflag and  
                Machine.objects.first().moldAdjustStatus):
            return 'moldadjust'
        
        # Conditions for the machine to enter material pipe cleaning status:
        #   - machine is not having erronous downtime
        #   - machine's material pipe cleaning switch is ON
        elif (not session.errflag and  
                Machine.objects.first().cleaningStatus):
            return 'material'
        
        else:
            pass
    
    return 'nochange'

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