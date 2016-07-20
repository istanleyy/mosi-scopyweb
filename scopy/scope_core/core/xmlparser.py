"""
MOSi Scope Device Framework:
Make real world manufacturing machines highly interoperable with different IT 
solutions. Implemented using python and django framework.

(C) 2016 - Stanley Yeh - ihyeh@mosi.com.tw
(C) 2016 - MOSi Technologies, LLC - http://www.mosi.com.tw

xmlparser.py
    Simple XML parser to manipulate Scope XML messages
"""

import os.path
import threading
import time
from io import BytesIO
from datetime import date
from lxml import etree
from scope_core.models import Job, SessionManagement
from scope_core.config import settings

LOCK = threading.Lock()

def isScopeXml(str):
    try:
        dom = etree.fromstring(str)
    except etree.XMLSyntaxError:
        print '\033[91m' + '[Scopy] XMLSyntaxError exception!' + '\033[0m'
        return False
        
    if dom.tag == 'scope_job':
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
        
def getJobUpdateXml(actualPcs, mct, users):
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
    stationTag.text = settings.DEVICE_INFO['ID']
    timeTag.text = timeText
    actualPcsTag.text = str(actualPcs)
    mctTag.text = str(mct)

    print 'users: ' + users
    if users:
        for user in users:
            userTag = etree.SubElement(jobUpdate, "user")
            userTag.text = user
    
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
    stationTag.text = settings.DEVICE_INFO['ID']
    timeTag.text = timeText
    typeTag.text = str(eventType)
    if user != "":
        userTag = etree.SubElement(jobEvent, "user")
        userTag.text = user
    if data != "":
        if data[0] != "W":
            qtyTag = etree.SubElement(jobEvent, "stock_qty")
            qtyTag.text = data
        else:
            refList = data.split('-')
            for ref in refList:
                serialTag = etree.SubElement(jobEvent, "ref_serial")
                serialTag.text = ref
    
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
                newJob.productid = element[3].text
                newJob.quantity = int(element[2].text)
                newJob.ct = int(element[4].text) if element[4].text is not None else 20
                newJob.multiplier = int(element[5].text) if element[5].text is not None else 1
                newJob.moldid = element[6].text
                if element[1].text == 'yes':
                    newJob.urgent = True
                newJob.save()
            
        print '\033[93m' + '[Scopy] New jobs added.' + '\033[0m'
        return True
    except etree.XMLSyntaxError:
        print '\033[91m' + '[Scopy] Cannot add new job. Check message format!' + msgContent[1] + '\033[0m'
        return False

def logUnsyncMsg(xmlstring):
    try:
        dom = etree.fromstring(xmlstring)
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
        if dom[0].tag == 'job_event' or dom[0].tag == 'job_update':
            insertpos = xmltree.find(".//unsync_messages")
        else:
            print '\033[91m' + '[Scopy] Unknown message content in logUnsyncMsg()' + '\033[0m'
            return False
        
        insertmsg = insertpos.append(dom[0])
        #print etree.tostring(xmltree, pretty_print=True, xml_declaration=True, encoding='utf-8')
        
        file = open(settings.UNSYNC_MSG_PATH, "w")
        file.write(etree.tostring(xmltree, pretty_print=True, xml_declaration=True, encoding='utf-8'))
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