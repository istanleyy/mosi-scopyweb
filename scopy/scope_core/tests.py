from django.test import TestCase
from .models import Job, SessionManagement
from .core import xmlparser
from .core import job_control

class XmlParserTestCase(TestCase):

    def test_unsync_log(self):
        Job.objects.create(productid="TESTJOB", moldid="TESTMOLD")
        SessionManagement.objects.create(job=Job.objects.first())
        updatemsg = xmlparser.getJobUpdateXml(0, 10)
        eventmsg = xmlparser.getJobEventXml(1, 'NJ')
        self.assertEqual(xmlparser.logUnsyncMsg(updatemsg), True)
        self.assertEqual(xmlparser.logUnsyncMsg(eventmsg), True)
        
class JobControlTestCase(TestCase):

    def test_co_condition(self):
        Machine.objects.create(opmode=3)
        self.assertEqual(job_control.evalCOCondition(), 'normal')
        Machine.objects.first().opmode = 2
        Machine.objects.first().save()
        self.assertEqual(job_control.evalCOCondition(), 'normal')
        Machine.objects.first().opmode = 1
        Machine.objects.first().save()
        self.assertEqual(job_control.evalCOCondition(), 'normal')
        Machine.objects.first().motorOnOffStatus = False
        Machine.objects.first().cleaningStatus = True
        Machine.objects.first().save()
        self.assertEqual(job_control.evalCOCondition(), 'material')
        