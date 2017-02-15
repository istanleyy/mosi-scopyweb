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

import pytz
import logging
from datetime import datetime
from djcelery.models import IntervalSchedule, PeriodicTask
from lxml import etree
from scope_core.models import Machine, Job, ProductionDataTS, SessionManagement, UserActivity
from scope_core.device import device_definition as const
from scope_core.config import settings
from . import xmlparser, request_sender, socket_server

LOGGER = logging.getLogger('scopepi.debug')
DEVICE_REFERENCE = None
LAST_OUTPUT = 0
CYCLE_COUNT = 0

def poll_device_status():
    global DEVICE_REFERENCE
    if DEVICE_REFERENCE:
        processQueryResult(
            'opStatus',
            DEVICE_REFERENCE.get_device_status(),
            PeriodicTask.objects.filter(name='scope_core.tasks.poll_metrics_task')[0]
            )

def poll_alarm_status():
    global DEVICE_REFERENCE
    result = DEVICE_REFERENCE.get_alarm_status()
    if DEVICE_REFERENCE and result:
        processQueryResult(
            'alarmStatus',
            result)

def poll_prod_status():
    global DEVICE_REFERENCE
    result = DEVICE_REFERENCE.get_production_status()
    if DEVICE_REFERENCE and result:
        processQueryResult(
            'opMetrics',
            result,
            PeriodicTask.objects.filter(name='scope_core.tasks.poll_metrics_task')[0]
            )

def processQueryResult(source, data, task=None):
    global LOGGER
    global DEVICE_REFERENCE
    session = SessionManagement.objects.first()
    machine = Machine.objects.first()

    if data == 'fail':
        print 'Communication error...'
        if not machine.commerr:
            machine.commerr = True
            machine.save()
            if session.job.inprogress and source != 'app':
                # If communication error is detected when a job is in progress,
                # notify server with code=X5
                sendEventMsg(4, 'X5')
            else:
                # If communication error is detected when a job is not running,
                # send 'bye' message to server to hang up the job
                request_sender.sendPostRequest('false:bye')
    else:
        if machine.commerr:
            machine.commerr = False
            machine.save()
            if session.job.inprogress:
                sendEventMsg(1, 'X5')

    if source == 'opStatus' and data != 'fail':
        job = SessionManagement.objects.first().job

        print(data, machine.opmode, machine.opstatus, machine.lastHaltReason)
        # If the machine is detected to be OFFLINE (FCS DB device),
        # send corresponding message to server
        if machine.opmode == 0:
            if job.inprogress:
                job.inprogress = False
                job.save()
                request_sender.sendPostRequest('false:bye')

        # If the machine has been switched to AUTO_MODE or SEMI_AUTO_MODE
        elif machine.opmode > 1:
            # Machine is in ready-to-produce status (RUNNING)
            if machine.opstatus == const.RUNNING or machine.opstatus == const.IDLE:
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

                    if machine.lastHaltReason == const.CHG_MOLD:
                        # If previous machine status is CHG_MOLD, need to send CO end message
                        machine.cooverride = False
                        sendEventMsg(6, 'ED')
                        DEVICE_REFERENCE.total_output = 0
                    elif (machine.lastHaltReason == const.CHG_MATERIAL or machine.lastHaltReason == const.SETUP):
                        # If previous status is CHG_MATERIAL, need to send DT end message
                        sendEventMsg(1, 'X1')
                    else:
                        # Sends normal job start message
                        sendEventMsg(1)

                    # Clear halt states
                    machine.lastHaltReason = 0
                    machine.save()

                else:
                    # Cannot load new job, simply clear any halt states
                    machine.cooverride = False
                    machine.lastHaltReason = 0
                    machine.save()

            else:
                # When the machine is in auto or semi-auto mode, it cannot be changing mold or
                # material, so the system should ignore such mode-status combinations
                pass

        # Machine is in MANUAL mode
        else:
            # Machine enters line change (change mold)
            if machine.opstatus == const.CHG_MOLD or machine.cooverride:
                if machine.lastHaltReason != const.CHG_MOLD:
                    print 'CO_OVERRIDE: ' + str(machine.cooverride)
                    # perform change-over
                    if performChangeOver(session, task, str(data[2])):
                        # Successfully enter CO state, send message to server
                        sendEventMsg(6, 'BG')
                        machine.lastHaltReason = const.CHG_MOLD
                        machine.save()
                    else:
                        if machine.lastHaltReason != const.NOJOB:
                            # Error in CO procedure, send message to server to
                            # end current job without next job
                            sendEventMsg(6, 'NJ')
                            machine.lastHaltReason = const.NOJOB
                            if machine.cooverride:
                                machine.cooverride = False
                            machine.save()

            # Machine is changing material
            elif machine.opstatus == const.CHG_MATERIAL:
                if machine.lastHaltReason != const.CHG_MATERIAL:
                    # Stop currently running job and send a downtime message to server
                    if job.inprogress:
                        job.inprogress = False
                        job.save()
                        sendEventMsg(4)

                    machine.lastHaltReason = const.CHG_MATERIAL
                    machine.save()

            # Machine is under SETUP
            elif machine.opstatus == const.SETUP:
                if machine.lastHaltReason != const.SETUP:
                    machine.lastHaltReason = const.SETUP
                    machine.save()

            # Machine in RUNNING or IDLE state
            else:
                pass

    elif source == 'opMetrics' and data != 'fail':
        mct = data[0]
        pcs = data[1]
        #moldSerial = str(data[2])
        #if evalCOCondition(machine, session) == 'mold':
        #    performChangeOver(session, task, moldSerial)

        if session.job.inprogress:
            # Machine idle check
            # If machine is not down nor changing mold, and the output has not change
            # in defined number of cycles, then the machine is idling
            if idleDetect(pcs) and not session.errflag and machine.opstatus != 2:
                sendEventMsg(2)
                LOGGER.warning('job_control detect machine idle.')

            # Log event only when there are actual outputs from the machine
            if ProductionDataTS.objects.last() is None or pcs != ProductionDataTS.objects.last().output:
                dataEntry = ProductionDataTS.objects.create(job=session.job, output=pcs, mct=mct)
                sendUpdateMsg(pcs, mct)

            ct = int(session.job.ct)
            if ct == 0:
                ct = 60
                session.job.ct = ct
                session.job.save()
            if task.interval.every != ct:
                intv, created = IntervalSchedule.objects.get_or_create(
                    every=ct, period='seconds'
                    )
                task.interval_id = intv.id
                task.save()

    elif source == 'alarmStatus' and data != 'fail':
        print (data, machine.opstatus)
        if machine.opmode != 0:
            if data[1]:
                print 'Machine error...'
                if not session.errflag:
                    if session.errid != data[0]:
                        session.errid = data[0]
                    session.errflag = True
                    session.save()
                    sendEventMsg(4)
            else:
                if session.errflag:
                    session.errflag = False
                    session.save()
                    sendEventMsg(1, 'X2')
    else:
        pass

def sendEventMsg(evttype, code="", user="", params=""):
    scopemsg = xmlparser.getJobEventXml(evttype, code, user, params)
    return sendRequest(scopemsg)

def sendUpdateMsg(pcs=None, mct=None):
    if pcs is None:
        pcs = ProductionDataTS.objects.last().output
    if mct is None:
        mct = ProductionDataTS.objects.last().mct

    scopemsg = xmlparser.getJobUpdateXml(pcs, mct)
    return sendRequest(scopemsg)

def sendRequest(msg):
    session = SessionManagement.objects.first()
    if session.msgblock:
        xmlparser.logUnsyncMsg(msg)
        return True
    else:
        if session.msgsync:
            xmlparser.logUnsyncMsg(msg)
            return sendMsgBuffer()
        else:
            result = request_sender.sendPostRequest(msg)
            if result[0] is None:
                xmlparser.logUnsyncMsg(msg)
                return False
            else:
                # return result of the request True/False
                return result[0]

def setMsgBlock():
    global LOGGER
    SessionManagement.objects.first().set_msg_block()
    LOGGER.warning('Blocking data transfer due to fail recovery error.')
    print '\033[91m' + '[Scopy] Blocking data transfer to server due to fail recovery error.' + '\033[0m'

def sendMsgBuffer():
    global LOGGER
    # getUnsyncMsgStr() returns None if there's an error getting the xml string
    result = request_sender.sendPostRequest(xmlparser.getUnsyncMsgStr(), True)
    if result[0]:
        # Reset msgsync and msgblock flag
        session = SessionManagement.objects.first()
        session.msgsync = False
        session.msgblock = False
        session.save()
        # Clear unsync message buffer
        xmlparser.flushUnsyncMsg()
        LOGGER.warning('Resumed data transfer to server.')
        print '\033[91m' + '[Scopy] Resumed data transfer to server.' + '\033[0m'
    else:
        if result[1] == 'ServerError:sync fail':
            setMsgBlock()
            LOGGER.warning('Message sync failed.')
        #print '\033[91m' + '[Scopy] Cannot send message cache to server.' + '\033[0m'
    return result[0]

def modelCheck():
    print '******************************'
    print 'Checking models...'
    # Check default job exsits, create if not
    initJob, jCreated = Job.objects.get_or_create(jobid=0, active=False)
    session = SessionManagement.objects.first()
    # Check default session exist, create if not
    if not session:
        print 'Initializing session...'
        SessionManagement.objects.create(job=initJob)
    else:
        # If session object's job reference is None, fix it by referring
        # to default job
        if not session.job:
            print 'Fix missing job reference...'
            session.job = initJob
            session.save()
    # Create Machine object if it doesn't exist
    if not Machine.objects.first():
        print 'Initializing machine...'
        Machine.objects.create()
    print 'done!'
    print '******************************'

def setup(device_ref):
    """Initializes system environment:
    1) Set device reference
    2) Notify server node is up
    3) Get jobs for this node from server
    4) Check job state, resumer production output counter if necessary
    """
    global LOGGER
    global DEVICE_REFERENCE
    global LAST_OUTPUT

    DEVICE_REFERENCE = device_ref.get_instance()
    request_sender.sendPostRequest('false:up')
    getJobsFromServer()

    job = SessionManagement.objects.last().job
    prod_hist = ProductionDataTS.objects.last()
    if prod_hist is not None and (job.jobid == prod_hist.job.jobid) and job.active:
        LAST_OUTPUT = ProductionDataTS.objects.last().output
        LOGGER.warning('Resuming job output count at {} pcs.'.format(LAST_OUTPUT))
        print 'Resume job output counter at {} pcs.'.format(LAST_OUTPUT)
    if LAST_OUTPUT != 0:
        DEVICE_REFERENCE.total_output = LAST_OUTPUT

def getJobsFromServer(job_id="", user_id=""):
    # If all jobs in db are done (not active), get new jobs from server
    # Function returns True if there are executable jobs, False otherwise
    activeJobs = Job.objects.filter(active=True)
    if not activeJobs:
        result = request_sender.sendGetRequest(job_id, user_id)
        if result is not None:
            if result == 'ServerMsg:no more job':
                return False
            else:
                print result
                return xmlparser.isScopeXml(result)
    else:
        return True

def idleDetect(pcs):
    global LAST_OUTPUT
    global CYCLE_COUNT
    if LAST_OUTPUT != pcs:
        LAST_OUTPUT = pcs
        CYCLE_COUNT = 0
    else:
        CYCLE_COUNT += 1
        if CYCLE_COUNT == settings.IDLE_CYCLE:
            return True
    return False

def evalCOCondition(machine, session):
    # Evaluate CO condition only if machine is not offline nor in auto mode
    if 0 < machine.opmode < 3:

        # Conditions for the machine to enter mold change status:
        #   - current job's demanded quantity has been made
        #   - machine is not having erronous downtime
        #   - motor of the machine is switched OFF
        if (ProductionDataTS.objects.last().output >= session.job.quantity and
                not session.errflag and
                not Machine.objects.first().moldChangeStatus):
            return 'mold'

        # Conditions for the machine to enter material pipe cleaning status:
        #   - machine is not having erronous downtime
        #   - machine's mold adjustment switch is ON
        elif not session.errflag and Machine.objects.first().setupStatus:
            return 'moldadjust'

        # Conditions for the machine to enter material pipe cleaning status:
        #   - machine is not having erronous downtime
        #   - machine's material pipe cleaning switch is ON
        elif not session.errflag and Machine.objects.first().matChangeStatus:
            return 'material'

        else:
            pass

    return 'nochange'

def performChangeOver(session, task, moldserial=None):
    global LOGGER
    # Set current job inactive
    oldJob = session.job
    oldJob.inprogress = False
    oldJob.active = False
    oldJob.save()

    # Load new job information only if we can find executable jobs in the db
    if getJobsFromServer():
        # If the mold id of the production data has changed,
        # need to update session reference to the job using the new mold.
        newJob = Job.objects.filter(active=True)
        if newJob:
            session.job = newJob[0]
            session.save()
            if task is None:
                LOGGER.error('Cannot update task period of new job.')
                return False
            else:
                # Compare polling period with retrieved mct value
                ct = int(session.job.ct)
                if ct == 0:
                    ct = 60
                    session.job.ct = ct
                    session.job.save()
                if ct != task.interval.every:
                    intv, created = IntervalSchedule.objects.get_or_create(
                        every=ct, period='seconds'
                        )
                    task.interval_id = intv.id
                    task.save()
                return True
        else:
            print '\033[91m' + '[Scopy] No scheduled jobs for this machine.' + '\033[0m'
            return False

    # Warn unable to find new job
    else:
        if settings.JOBID0LOG:
            # Track unscheduled production activities with jobid=0
            session.job = Job.objects.get(jobid=0)
            session.save()
        print '\033[91m' + '[Scopy] Unable to obtain job info in CO process!' + '\033[0m'
        return False

def processBarcodeActivity(data):
    global LOGGER
    barcodes = data.split(',')
    uid = barcodes[0]
    activity = barcodes[1]
    params = ""
    if len(barcodes) > 2:
        params = barcodes[2]

    if activity == 'LOGIN' or activity == 'LOGOUT' or activity == 'ALLOUT':
        if activity == 'LOGIN':
            tLogin = datetime.now()
            user = UserActivity.objects.filter(uid=uid)
            if not user:
                UserActivity.objects.create(uid=uid, lastLogin=tLogin, lastLogout=None)
            else:
                user[0].lastLogin = tLogin
                user[0].lastLogout = None
                user[0].save()
            sendEventMsg(uid, activity)
            print "Users: ", UserActivity.objects.filter(lastLogout=None)
        else:
            try:
                user = UserActivity.objects.get(uid=uid)
                if user and user.lastLogout is None:
                    user.lastLogout = datetime.now()
                    user.save()
                    sendEventMsg(uid, 'LOGOUT')
                    if activity == 'ALLOUT':
                        socket_server.SocketServer.getInstance().send_bcast(
                            'PeerMsg-{0}:{1},{2}'.format(settings.DEVICE_INFO['ID'], uid, 'LOGOUT')
                            )
            except UserActivity.DoesNotExist:
                LOGGER.exception('User {0} did not logged in.'.format(uid))
                return 'fail'
            except UserActivity.MultipleObjectsReturned:
                LOGGER.exception('ScopePi login process error.')
                return 'fail'
            finally:
                print "Users: ", UserActivity.objects.filter(lastLogout=None)
        return 'ok'
    else:
        # If receiving request from barcode activity
        if activity == 'req':
            if params[0] == 'T':
                # Received mould serial check request
                job = SessionManagement.objects.first().job
                mold = job.moldid.strip(' \t\n\r')
                if params == mold or params == 'TZZZZZZZZZ':
                    return str(job.multiplier)
                else:
                    return str(0)
            if params[3] == 'P1B':
                msgdata = params.split(';')
                # Received job initiation request
                return getJobsFromServer(msgdata[0], msgdata[1])
            else:
                return 'unknown'

        # If performing change-over procedure
        if activity == 'CHGOVR':
            machine = Machine.objects.first()
            # Barcode CO event over-rides machine's mold change status
            if machine.opmode != 3 and not machine.cooverride:
                machine.cooverride = True
                machine.save()
                #print '***** barcode CO *****'

        # If performing mold trial, need to quit CO procedure without machine
        # switching to auto mode
        if activity == '1065':
            machine = Machine.objects.first()
            machine.cooverride = False
            machine.save()

        # If received TERM message during CO, end CO
        if activity == 'TERM' and Machine.objects.first().opstatus == 2:
            machine = Machine.objects.first()
            if machine.cooverride:
                machine.cooverride = False
                machine.save()

        # If recieved multiplier change event, need to update job multiplier and CT
        if activity == 'MULCHG':
            updateMultiplier(int(params))

        if sendEventMsg(activity, 'WS', uid, params):
            return 'ok'
        else:
            return 'fail'

def processServerAction(data):
    global DEVICE_REFERENCE
    actparam = data.split(',')
    if actparam[0] == 'co':
        result = performChangeOverByID(actparam[1])
        if result == 0:
            sendEventMsg(6, 'BG')
            machine = Machine.objects.first()
            machine.lastHaltReason = const.CHG_MOLD
            machine.save()
        elif result > 0:
            sendEventMsg(6, 'NJ')
        DEVICE_REFERENCE.total_output = 0
        return True
    else:
        return False

def updateMultiplier(multi):
    global LOGGER
    currJob = SessionManagement.objects.first().job
    oldCT = currJob.ct
    oldMulti = currJob.multiplier
    currJob.multiplier = multi
    newCT = multi*(oldCT/oldMulti)
    currJob.ct = newCT
    currJob.save()
    LOGGER.warning('Updated multiplier and CT. ({0},{1})'.format(multi, newCT))

def performChangeOverByID(id):
    global LOGGER
    session = SessionManagement.objects.first()
    # Don't change job if current JobId matches
    if session.job.jobid != int(id):
        # Set current job inactive
        oldJob = session.job
        oldJob.inprogress = False
        oldJob.active = False
        oldJob.save()

        # Load new job information only if we can find executable jobs in the db
        if getJobsFromServer():
            task = PeriodicTask.objects.filter(name='scope_core.tasks.poll_metrics_task')[0]
            # If the mold id of the production data has changed,
            # need to update session reference to the job using the new mold.
            newJob = Job.objects.filter(jobid=int(id), active=True)
            if newJob:
                session.job = newJob[0]
                session.save()
                if task is None:
                    LOGGER.error('Cannot update task period of new job.')
                    return 1
                else:
                    # Compare polling period with retrieved mct value
                    ct = int(session.job.ct)
                    if ct == 0:
                        ct = 60
                        session.job.ct = ct
                        session.job.save()
                    if ct != task.interval.every:
                        intv, created = IntervalSchedule.objects.get_or_create(
                            every=ct, period='seconds'
                            )
                        task.interval_id = intv.id
                        task.save()
                    LOGGER.warning('Server forced CO.')
                    print '\033[93m' + '[Scopy] Server force CO.' + '\033[0m'
                    return 0
            else:
                LOGGER.error('Cannot find job matching id {0}.'.format(id))
                print '\033[91m' + '[Scopy] Unable to find next job matching ID: ' + id + '\033[0m'
                return 2
    # Warn unable to find new job
    else:
        LOGGER.error('Ignore CO request for repeated job ({0}).'.format(id))
        print '\033[91m' + '[Scopy] Ignoring CO request for repeated job.' + '\033[0m'
        return -1

"""
def test_epoch_sec():
    last_10_cycles = ProductionDataTS.objects.all().order_by('-eventtime')[:10]
    if last_10_cycles:
        dataset = []
        last_10_cycles_r = reversed(last_10_cycles)
        for data in last_10_cycles_r:
            timeval = int((data.eventtime - datetime(1970,1,1,tzinfo=pytz.utc)).total_seconds())
            dataset.append({'x': timeval, 'y': data.mct})
        print dataset
    else:
        print 'No data!'
"""