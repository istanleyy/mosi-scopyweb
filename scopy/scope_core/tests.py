from django.test import TestCase
from .models import Job, SessionManagement
from .core import xmlparser

class XmlParserTestCase(TestCase):

    def test_unsync_log(self):
        Job.objects.create(productid="TESTJOB", moldid="TESTMOLD")
        SessionManagement.objects.create(job=Job.objects.first())
        updatemsg = xmlparser.getJobUpdateXml(0, 10)
        eventmsg = xmlparser.getJobEventXml(1, 'NJ')
        self.assertEqual(xmlparser.logUnsyncMsg(updatemsg), True)
        self.assertEqual(xmlparser.logUnsyncMsg(eventmsg), True)