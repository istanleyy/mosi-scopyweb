"""
Simple XML parser to handle Scope XML messages
"""

import time
from datetime import date
from lxml import etree
from scope_core.models import Job, SessionManagement
from scope_core.config import settings

def isScopeXml(str):
    try:
        dom = etree.fromstring(str)
    except etree.XMLSyntaxError:
        print "[Exception] Bad XML format."
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
        
def getJobUpdateXml(actualPcs, mct):
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
    return etree.tostring(docRoot, encoding='utf-8', xml_declaration=True)

def getJobEventXml(eventType, eventCode):
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
    
    #print etree.tostring(docRoot, encoding='utf-8', pretty_print=True)
    return etree.tostring(docRoot, encoding='utf-8', xml_declaration=True)

def getStartupXml():
    docRoot = etree.Element("scope_job")
    jobQueue = etree.SubElement(docRoot, "job_queue", mode=settings.QUEUE_MODE)
    slot1 = etree.SubElement(jobQueue, "slot1")
    slot2 = etree.SubElement(jobQueue, "slot2") # For list mode use
    slot1.text = str(SessionManagement.objects.first().job.jobid)
    slot2.text = '0'
    #print etree.tostring(docRoot, encoding='utf-8', pretty_print=True)
    return etree.tostring(docRoot, encoding='utf-8', xml_declaration=True)

def getXmlTimeVal():
    today = date.today()
    session = SessionManagement.objects.first()
    if today > session.modified:
        session.msgid = 0
    else:
        session.msgid += 1
    session.save()
    
    timeText = time.strftime("%Y%m%d%H%M%S")
    msgIdText = timeText[2:-6] + "-" + str(session.msgid)
    return (msgIdText, timeText)
    
def createJobList(xmldom):
    try:
        for element in xmldom.iter("job_item"):
            newJob = Job.objects.create()
            newJob.jobid = int(element[0].text)
            newJob.productid = element[2].text
            newJob.quantity = int(element[3].text)
            newJob.ct = int(element[4].text)
            newJob.multiplier = int(element[5].text)
            newJob.moldid = element[6].text
            if element[1].text == 'yes':
                newJob.urgent = True
            newJob.save()
            
        print '\033[93m' + '[Scopy] New jobs added.' + '\033[0m'
        return True
    except etree.XMLSyntaxError:
        print '\033[91m' + '[Scopy] Cannot add new job. Check message format!' + msgContent[1] + '\033[0m'
        return False