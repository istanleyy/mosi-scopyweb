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
from scope_core.config import settings
from . import xmlparser
from . import request_sender

# OPSTATUS maintains the state of current machine status
OPSTATUS = const.OFFLINE
CO_OVERRIDE = False

def processQueryResult(source, data, task=None):
    global OPSTATUS
    global CO_OVERRIDE
    if source == 'opStatus':
        session = SessionManagement.objects.first()
        job = SessionManagement.objects.first().job
        
        print(data)
        
        # If the machine is detected to be OFFLINE (FCS DB device), 
        # send corresponding message to server
        if data[0] == const.OFFLINE:
            if OPSTATUS != const.OFFLINE:
                OPSTATUS = const.OFFLINE
                if job.inprogress:
                    job.inprogress = False
                    job.save()
                request_sender.sendPostRequest('false:bye')
	    else:
	        OPSTATUS = data[0]

        # Machine is in ready-to-produce status (RUNNING)
        if data[1] == const.RUNNING or data[1] == const.IDLE:
            # If the machine has been switched to AUTO_MODE
            if data[0] == const.AUTO_MODE:
                # Check job status for current session
                if not job.active:
                    # If current job is completed or removed from work (not active),
                    # should get the correct job to run
                    if performChangeOver(session, task, str(data[2])):
                        # Update job reference
                        job = SessionManagement.objects.first().job
                        
                # Start the job if it has not been started
                if not job.inprogress and job.active:
                    job.inprogress = True
                    job.save()
                        
                    if OPSTATUS == const.CHG_MOLD:
                        # If previous machine status is CHG_MOLD, need to send CO end message
                        sendEventMsg(6, 'ED')
                        CO_OVERRIDE = False
                    elif OPSTATUS == const.CHG_MATERIAL:
                        # If previous status is CHG_MATERIAL, need to send DT end message
                        sendEventMsg(1, 'X1')
                    else:
                        # Sends normal job start message
                        sendEventMsg(1)
                    
                    # Update the state of machine's operation status
                    OPSTATUS = const.RUNNING
            else:
                # Currently job_control is ignoring MANUAL_MODE and SEMI_AUTO_MODE
                pass
        
        # Machine enters line change (change mold)        
        elif data[1] == const.CHG_MOLD or CO_OVERRIDE:
            # If not already in change-over (CO), update machine status and perform CO
            if OPSTATUS != const.CHG_MOLD:
                OPSTATUS = const.CHG_MOLD
                if performChangeOver(session, task, str(data[2])):
                    # Successfully enter CO state, send message to server
                    sendEventMsg(6, 'BG')
                else:
                    # Error in CO procedure, send message to server to end current job without next job
                    sendEventMsg(6, 'NJ')
        
        # Machine is changing material
        elif data[1] == const.CHG_MATERIAL:
            # Stop currently running job and send a downtime message to server
            if job.inprogress:
                job.inprogress = False
                job.save()
                OPSTATUS = const.CHG_MATERIAL
                sendEventMsg(4)
        else:
            # Valid machine status are: IDLE, RUNNING, CHG_MOLD, CHG_MATERIAL
            # Ignore other (undefined) status for now
            pass
        
    elif source == 'opMetrics':
        mct = data[0]
        pcs = data[1]
        #moldSerial = str(data[2])
        
        #machine = Machine.objects.first()
        session = SessionManagement.objects.first()
        #if evalCOCondition(machine, session) == 'mold':
        #    performChangeOver(session, task, moldSerial)
        
        if session.job.inprogress:
            # Log event only when there are actual outputs from the machine
            if pcs != ProductionDataTS.objects.last().output:
                dataEntry = ProductionDataTS.objects.create(job=session.job, output=pcs, mct=mct)
                sendUpdateMsg(pcs, mct)
            
            if task.interval.every != session.job.ct:
                intv, created = IntervalSchedule.objects.get_or_create(
                    every=session.job.ct, period='seconds'
                    )
                task.interval_id = intv.id
                task.save()

    elif source == 'alarmStatus':
        print (data, OPSTATUS)
        if OPSTATUS != const.OFFLINE:
            session = SessionManagement.objects.first()
            errlatch = 'X2'
            print data
            if data[1]:
                print 'Machine error...'
                if not session.errflag:
                    if session.errid != data[0]:
                        session.errid = data[0]
                        errlatch = data[0]
                    session.errflag = True
                    session.save()
                    sendEventMsg(4)
            else:
                if session.errflag:
                    session.errflag = False
                    session.save()
                    #sendEventMsg(1, errlatch)
                    sendEventMsg(1, "X2")
    else:
        pass

def sendEventMsg(evttype, code="", user="", data=""):
    scopemsg = xmlparser.getJobEventXml(evttype, code, user, data)
    result = request_sender.sendPostRequest(scopemsg)
    if result is None:
        xmlparser.logUnsyncMsg(scopemsg)
        sendMsgBuffer()
    else:
        if not result:
            xmlparser.logUnsyncMsg(scopemsg)
        return result

def sendUpdateMsg(pcs=None, mct=None):
    if pcs is None:
        pcs = ProductionDataTS.objects.last().output
    if mct is None:
        mct = ProductionDataTS.objects.last().mct
        
    scopemsg = xmlparser.getJobUpdateXml(pcs, mct)
    result = request_sender.sendPostRequest(scopemsg)
    if result is None:
        xmlparser.logUnsyncMsg(scopemsg)
        sendMsgBuffer()
    else:
        if not result:
            xmlparser.logUnsyncMsg(scopemsg)
    
def sendMsgBuffer():
    # getUnsyncMsgStr() returns None if there's an error getting the xml string
    result = request_sender.sendPostRequest(xmlparser.getUnsyncMsgStr(), True)
    if result:
        # Clear unsync message buffer
        xmlparser.flushUnsyncMsg()
    
def init():
    request_sender.sendPostRequest('false:up')
    getJobsFromServer()
    
def getJobsFromServer():
    # If all jobs in db are done (not active), get new jobs from server
    # Function returns True if there are executable jobs, False otherwise
    activeJobs = Job.objects.filter(active=True)
    if not activeJobs:
        result = request_sender.sendGetRequest()
        if result is not None:
            if result == 'ServerMsg:no more job':
                return False
            else:
                return xmlparser.isScopeXml(result)
    else:
        return True

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
    # Set current job inactive
    oldJob = session.job
    oldJob.inprogress = False
    oldJob.active = False
    oldJob.save()
    
    # Load new job information only if we can find executable jobs in the db
    if getJobsFromServer():
        # If the mold id of the production data has changed, 
        # need to update session reference to the job using the new mold.
        newJob = Job.objects.filter(moldid=moldserial, active=True)
        if newJob:
            session.job = newJob[0]
            session.save()
            if task is None:
                print '!!! Unable to update task period due to missing argument !!!'
                return False
            else:
                # Compare polling period with retrieved mct value
                if session.job.ct != task.interval.every:
                    intv, created = IntervalSchedule.objects.get_or_create(
                        every=session.job.ct, period='seconds'
                        )
                    task.interval_id = intv.id
                    task.save()        
                return True
        else:
            print '\033[91m' + '[Scopy] Unable to find next job matching mold ID: ' + moldserial + '\033[0m'
            return False
            
    # Warn unable to find new job
    else:
        print '\033[91m' + '[Scopy] Unable to obtain job info in CO process!' + '\033[0m'
        return False

def processBarcodeActivity(data):
    global CO_OVERRIDE
    barcodes = data.split(',')
    uid = barcodes[0]
    activity = barcodes[1]
    if len(barcodes) > 3:
        data = barcodes[3]
    else:
        data = barcode[2]

    if activity == 'LOGIN' or activity == 'LOGOUT':
        if sendEventMsg(uid, activity):
            if activity == 'LOGIN':
                settings.USERS.append(uid)
                print "Users: ", settings.USERS
            else:
                settings.USERS.remove(uid)
                print "Users: ", settings.USERS
            return True
        else:
            return False
    else:
        # If performing change-over procedure
        if activity == '1062' or activity == '1063':
            # Barcode CO event over-rides CO status, CO_OVERRIDE will
            # be cleared when the machine is set to auto mode.
            if Machine.objects.first().opmode != 3:
                CO_OVERRIDE = True

        return sendEventMsg(activity, 'WS', uid, data)