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
        return True
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
    doneTag.text = '1' if actualPcs >= Job.objects.get(jobid=jobId).quantity else '0'
    session = SessionManagement.objects.first()
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