"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

xmlparser.py
    Simple XML parser to manipulate Scope XML messages
"""

import os
import os.path
import threading
import time
import logging
from decimal import Decimal
from io import BytesIO
from datetime import date
from lxml import etree
from scope_core.models import Job, SessionManagement, UserActivity
from scope_core.config import settings

LOCK = threading.Lock()
logger = logging.getLogger('scopepi.debug')

def isScopeXml(str):
    try:
        dom = etree.fromstring(str)
    except etree.XMLSyntaxError:
        print '\033[91m' + '[Scopy] XMLSyntaxError exception!' + '\033[0m'
        return False

    if dom.tag == 'scope_job':
        if settings.CLEAR_JOBLIST:
            with open(settings.JOBLIST_PATH, "w"): pass
            clearJobModel()
        file = open(settings.JOBLIST_PATH, "w")
        file.write(etree.tostring(dom, pretty_print=True, xml_declaration=True, encoding='utf-8'))
        file.close()
        return createJobList(dom)
    elif dom.tag == 'scope_config':
        file = open(settings.CONFIG_PATH, "w")
        file.write(etree.tostring(dom, pretty_print=True, xml_declaration=True, encoding='utf-8'))
        file.close()
        return True
    else:
        return False

def getJobUpdateXml(actualPcs, mct):
    global OPERATOR_LIST
    msgId, timeText = getXmlTimeVal()
    docRoot = etree.Element("scope_job")
    jobUpdate = etree.SubElement(docRoot, "job_update", msg_id=msgId)
    doneTag = etree.SubElement(jobUpdate, "done")
    jobIdTag = etree.SubElement(jobUpdate, "job_id")
    stationTag = etree.SubElement(jobUpdate, "station")
    timeTag = etree.SubElement(jobUpdate, "time")
    actualPcsTag = etree.SubElement(jobUpdate, "actual_pcs")
    mctTag = etree.SubElement(jobUpdate, "mct")

    # Get planned pcs (quantity) from models.Job
    session = SessionManagement.objects.first()
    doneTag.text = '1' if actualPcs >= session.job.quantity else '0'
    jobIdTag.text = str(session.job.jobid)
    stationTag.text = settings.DEVICE_INFO['NAME']
    timeTag.text = timeText
    actualPcsTag.text = str(actualPcs)
    mctTag.text = str(mct)

    users = UserActivity.objects.filter(lastLogout=None)
    if users:
        for user in users:
            userTag = etree.SubElement(jobUpdate, "user")
            userTag.text = user.uid

    print etree.tostring(docRoot, encoding='utf-8', pretty_print=True)
    return etree.tostring(docRoot, encoding='utf-8', xml_declaration=True)

def getJobEventXml(eventType, eventCode, user="", data=""):
    msgId, timeText = getXmlTimeVal()
    docRoot = etree.Element("scope_job")
    jobEvent = etree.SubElement(docRoot, "job_event", msg_id=msgId)
    jobIdTag = etree.SubElement(jobEvent, "job_id")
    stationTag = etree.SubElement(jobEvent, "station")
    timeTag = etree.SubElement(jobEvent, "time")
    typeTag = etree.SubElement(jobEvent, "type", code=eventCode)

    session = SessionManagement.objects.first()
    jobIdTag.text = str(session.job.jobid)
    stationTag.text = settings.DEVICE_INFO['NAME']
    timeTag.text = timeText
    typeTag.text = str(eventType)
    if typeTag.text == '6':
        workers = UserActivity.objects.filter(lastLogout=None)
        for worker in workers:
            userTag = etree.SubElement(jobEvent, "user")
            userTag.text = worker.uid
    else:
        if user != "":
            userTag = etree.SubElement(jobEvent, "user")
            userTag.text = user
    if data != "":
        if data[0] == 'C':
            refList = data.split('-')
            for ref in refList:
                serialTag = etree.SubElement(jobEvent, "ref_serial")
                serialTag.text = ref
        elif data[0] == 'T':
            mouldInfo = data.split('-')
            mouldTag = etree.SubElement(jobEvent, "mould")
            mouldTag.text = mouldInfo[0]
        elif typeTag.text == 'MULCHG':
            multiplierTag = etree.SubElement(jobEvent, "multiplier")
            multiplierTag.text = data
        else:
            qtyTag = etree.SubElement(jobEvent, "stock_qty")
            qtyTag.text = data

    print etree.tostring(docRoot, encoding='utf-8', pretty_print=True)
    return etree.tostring(docRoot, encoding='utf-8', xml_declaration=True)

# Job start message follows B2MML JobOrder schema
def getJobStartXml():
    msgId, timeText = getXmlTimeVal()
    docRoot = etree.Element("scope_job", msg_id=msgId)
    jobOrder = etree.SubElement(docRoot, "JobOrder")
    jobIdTag = etree.SubElement(jobOrder, "ID")
    descTag = etree.SubElement(jobOrder, "Description")
    hierTag = etree.SubElement(jobOrder, "HierarchyScope")
    workTTag = etree.SubElement(jobOrder, "WorkType")
    workMIDTag = etree.SubElement(jobOrder, "WorkMasterID")
    workMVerTag = etree.SubElement(jobOrder, "WorkMasterVersion")
    sTimeTag = etree.SubElement(jobOrder, "StartTime")
    eTimeTag = etree.SubElement(jobOrder, "EndTime")
    priorityTag = etree.SubElement(jobOrder, "Priority")
    cmdTag = etree.SubElement(jobOrder, "Command")
    cmdRuleTag = etree.SubElement(jobOrder, "CommandRule")
    dispatchTag = etree.SubElement(jobOrder, "DispatchStatus")

    joParam = etree.SubElement(jobOrder, "JobOrderParameter")
    jopIdTag = etree.SubElement(joParam, "ID")
    val1 = etree.SubElement(joParam, "Value")
    valStr1 = etree.SubElement(val1, "ValueString")
    dataType1 = etree.SubElement(val1, "DataType")
    uom1 = etree.SubElement(val1, "UnitOfMeasure")
    key1 = etree.SubElement(val1, "Key")
    val2 = etree.SubElement(joParam, "Value")
    valStr2 = etree.SubElement(val2, "ValueString")
    dataType2 = etree.SubElement(val2, "DataType")
    uom2 = etree.SubElement(val2, "UnitOfMeasure")
    key2 = etree.SubElement(val2, "Key")
    jopDescTag = etree.SubElement(joParam, "Description")
    jopParamTag = etree.SubElement(joParam, "Parameter")

    personReq = etree.SubElement(jobOrder, "PersonnelRequirement")

    equipReq = etree.SubElement(jobOrder, "EquipmentRequirement")
    equipClsId = etree.SubElement(equipReq, "EquipmentClassID")
    equipId = etree.SubElement(equipReq, "EquipmentID")
    equipDesc = etree.SubElement(equipReq, "Description")
    equipUse = etree.SubElement(equipReq, "EquipmentUse")
    equipQuantity = etree.SubElement(equipReq, "Quantity")
    equipHier = etree.SubElement(equipReq, "HierarchyScope")
    equipLevel = etree.SubElement(equipReq, "EquipmentLevel")
    equipReqProp = etree.SubElement(equipReq, "EquipmentRequirementProperty")
    equipRRS = etree.SubElement(equipReq, "RequiredByRequestedSegment")

    phyAssetReq = etree.SubElement(jobOrder, "PhysicalAssetRequirement")
    materialReq = etree.SubElement(jobOrder, "MaterialRequirement")

    session = SessionManagement.objects.first()
    jobIdTag.text = str(session.job.jobid)
    jopIdTag.text = session.job.productid
    sTimeTag.text = timeText
    cmdTag.text = 'Start'
    valStr1.text = str(session.job.quantity)
    dataType1.text = 'positiveInteger'
    uom1.text = 'pcs'
    key1.text = 'PlannedPcs'
    valStr2.text = str(session.job.ct)
    dataType2.text = 'positiveInteger'
    uom2.text = 'sec'
    key2.text = 'CycleTime'
    equipId.text = settings.DEVICE_INFO['NAME']

    print etree.tostring(docRoot, encoding='utf-8', pretty_print=True)
    return etree.tostring(docRoot, encoding='utf-8', xml_declaration=True)

def getStartupXml():
    docRoot = etree.Element("scope_job")
    jobQueue = etree.SubElement(docRoot, "job_queue", mode=settings.QUEUE_MODE)
    slot1 = etree.SubElement(jobQueue, "slot1")
    slot2 = etree.SubElement(jobQueue, "slot2") # For list mode use
    slot1.text = str(SessionManagement.objects.first().job.jobid)
    slot2.text = '0'
    #print etree.tostring(docRoot, encoding='utf-8', pretty_print=True)
    return etree.tostring(docRoot, encoding='utf-8', xml_declaration=False)

def getXmlTimeVal():
    global LOCK
    LOCK.acquire()
    try:
        today = date.today()
        session = SessionManagement.objects.first()
        if today > session.modified:
            session.msgid = 1
        else:
            session.msgid += 1
        session.save()

        timeText = time.strftime("%Y%m%d%H%M%S")
        # Check for valid date, if the year is less than 2000,
        # return invalid date string of zeroes.
        if timeText[0] != '2':
            timeText = '00000000000000'
        msgIdText = timeText[2:-6] + "-" + str(session.msgid)
    finally:
        LOCK.release()
    return (msgIdText, timeText)

def createJobList(xmldom):
    try:
        for element in xmldom.iter("job_item"):
            if not Job.objects.filter(jobid=int(element[0].text)):
                newJob = Job.objects.create()
                newJob.jobid = int(element[0].text)
                if element[1].text == 'yes':
                    newJob.urgent = True
                newJob.quantity = int(element[2].text)
                if element[3].text is not None:
                    newJob.productid = element[3].text
                newJob.ct = Decimal(element[4].text) if element[4].text is not None else 20.0
                newJob.multiplier = int(element[5].text) if element[5].text is not None else 1
                newJob.moldid = element[6].text if element[6].text is not None else 'TZZZZZZZZZ'
                newJob.save()
            else:
                if element[0].text != '0':
                    resurrectjob = Job.objects.get(jobid=int(element[0].text))
                    if resurrectjob and not resurrectjob.active:
                        resurrectjob.active = True
                        resurrectjob.save()

        print '\033[93m' + '[Scopy] Job list updated.' + '\033[0m'
        return True
    except (etree.XMLSyntaxError, IndexError, ValueError):
        # Remove job with incomplete data
        obsoleteJob = Job.objects.last()
        if obsoleteJob.jobid == 0:
            obsoleteJob.delete()
        print '\033[91m' + '[Scopy] Cannot add new job. Check message format!' + msgContent[1] + '\033[0m'
        return False

def logUnsyncMsg(xmlstring):
    # If message cannot be delivered to the server,
    # need to set msgsync flag to trigger message sync procedure to prevent
    # data lost due to out-of-sync message sequemce
    session = SessionManagement.objects.first()
    if not session.msgsync:
        session.msgsync = True
        session.save()

    try:
        dom = etree.fromstring(xmlstring)
        treecopy = dom[0]
        parser = etree.XMLParser(remove_blank_text=True)
        if not os.path.isfile(settings.UNSYNC_MSG_PATH):
            msgTemp = BytesIO('''\
            <scope_job>
                <unsync_messages></unsync_messages>
            </scope_job>''')
            xmltree = etree.parse(msgTemp, parser)
            file = open(settings.UNSYNC_MSG_PATH, "w")
            file.write(etree.tostring(xmltree, pretty_print=True, xml_declaration=True, encoding='utf-8'))
            file.close()
        else:
            xmltree = etree.parse(settings.UNSYNC_MSG_PATH, parser)

        # Log only event or update messages
        if dom[0].tag == 'job_event':
            insertpos = xmltree.find('.//unsync_messages')
            insertmsg = insertpos.append(dom[0])
        elif dom[0].tag == 'job_update':
            jobid = dom[0].findtext('.//job_id')
            updatemsg = xmltree.findall('.//job_update')
            if updatemsg:
                for msg in updatemsg:
                    id = msg.findtext('.//job_id')
                    if id == jobid:
                        msg.getparent().remove(msg)

            insertpos = xmltree.find('.//unsync_messages')
            insertmsg = insertpos.append(dom[0])
        else:
            print '\033[91m' + '[Scopy] Unknown message content in logUnsyncMsg()' + '\033[0m'
            return False

        timeval = treecopy.findtext('.//time')
        if timeval != '00000000000000':
            timetags = xmltree.xpath('.//time[text()="00000000000000"]')
            if timetags:
                for time in timetags:
                    time.text = timeval

        #print etree.tostring(xmltree, pretty_print=True, xml_declaration=True, encoding='utf-8')
        file = open(settings.UNSYNC_MSG_PATH, "w")
        file.write(
            etree.tostring(xmltree, pretty_print=True, xml_declaration=True, encoding='utf-8'))
        file.close()
        return True

    except etree.XMLSyntaxError:
        print '\033[91m' + '[Scopy] XML syntax error in logUnsyncMsg()' + '\033[0m'
        return False
    except IOError:
        print '\033[91m' + '[Scopy] Cannot access unsync message log file!' + '\033[0m'
        return False

def getUnsyncMsgStr():
    try:
        parser = etree.XMLParser(remove_blank_text=True)
        if not os.path.isfile(settings.UNSYNC_MSG_PATH):
            msgTemp = BytesIO('''\
            <scope_job>
                <unsync_messages></unsync_messages>
            </scope_job>''')
            xmltree = etree.parse(msgTemp, parser)
            file = open(settings.UNSYNC_MSG_PATH, "w")
            file.write(etree.tostring(xmltree, pretty_print=True, xml_declaration=True, encoding='utf-8'))
            file.close()
        else:
            xmltree = etree.parse(settings.UNSYNC_MSG_PATH, parser)

        print etree.tostring(xmltree, encoding='utf-8', pretty_print=True)
        return etree.tostring(xmltree, xml_declaration=True, encoding='utf-8')

    except etree.XMLSyntaxError:
        print '\033[91m' + '[Scopy] XML syntax error in getUnsyncMsgStr()' + '\033[0m'
        return None
    except IOError:
        print '\033[91m' + '[Scopy] Cannot access unsync message log file!' + '\033[0m'
        return None

def flushUnsyncMsg():
    try:
        parser = etree.XMLParser(remove_blank_text=True)
        msgTemp = BytesIO('''\
        <scope_job>
            <unsync_messages></unsync_messages>
        </scope_job>''')
        xmltree = etree.parse(msgTemp, parser)
        file = open(settings.UNSYNC_MSG_PATH, "w")
        file.write(etree.tostring(xmltree, pretty_print=True, xml_declaration=True, encoding='utf-8'))
        file.close()

    except IOError:
        print '\033[91m' + '[Scopy] Cannot access unsync message log file!' + '\033[0m'
        return None

def updateOperatorList(list):
    global OPERATOR_LIST
    OPERATOR_LIST = list[:]
    print OPERATOR_LIST

def clearJobModel():
    currentjid = SessionManagement.objects.first().job.jobid
    jobs = Job.objects.filter(jobid__gt=0, active=True).exclude(jobid=currentjid)
    for job in jobs:
        job.delete()
        logger.warning('Job {0} ({1}) deleted.'.format(job.jobid, job.productid))
        