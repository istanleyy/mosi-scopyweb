from django.test import TestCase
from .models import Job, SessionManagement, Machine, ProductionDataTS
from .core import xmlparser
from .core import job_control

class XmlParserTestCase(TestCase):

    def test_unsync_log(self):
        # Setup test DB entries
        Job.objects.create(productid="TESTJOB", moldid="TESTMOLD", quantity=100)
        SessionManagement.objects.create(job=Job.objects.first())
        # Get xml messages to test logging methods
        updatemsg = xmlparser.getJobUpdateXml(0, 10)
        eventmsg = xmlparser.getJobEventXml(1, 'NJ')
        self.assertEqual(xmlparser.logUnsyncMsg(updatemsg), True)
        self.assertEqual(xmlparser.logUnsyncMsg(eventmsg), True)
        
class JobControlTestCase(TestCase):

    def test_co_condition(self):
        # Setup test DB entries
        Job.objects.create(productid="TESTJOB", moldid="TESTMOLD", quantity=100)
        session = SessionManagement.objects.create(job=Job.objects.first())
        ProductionDataTS.objects.create(job=Job.objects.first())
        machine = Machine.objects.create(opmode=0, motorOnOffStatus=True)
        # Test 1 - machine opmode = 0, CO condition should be 'nochange' 
        self.assertEqual(job_control.evalCOCondition(machine, session), 'nochange')
        # Test 2 - machine opmode = 3, CO condition should be 'nochange'
        machine.opmode = 3
        machine.save()
        self.assertEqual(job_control.evalCOCondition(machine, session), 'nochange')
        # Test 3 - machine opmode = 2, output < quantity, no error, switches all OFF
        # CO condition should be 'nochange'
        machine.opmode = 2
        machine.save()
        self.assertEqual(job_control.evalCOCondition(machine, session), 'nochange')
        # Test 4 - machine opmode = 1, output < quantity, no error, switches all OFF
        # CO condition should be 'nochange'
        machine.opmode = 1
        machine.save()
        self.assertEqual(job_control.evalCOCondition(machine, session), 'nochange')
        # Test 5 - machine opmode = 1, output < quantity, ERROR, clean pipe ON
        # CO condition should be 'nochange'
        session.errflag = True
        session.save()
        machine.cleaningStatus = True
        machine.save()
        self.assertEqual(job_control.evalCOCondition(machine, session), 'nochange')
        # Test 6 - machine opmode = 1, output < quantity, no error, clean pipe ON
        # CO condition should be 'material'
        session.errflag = False
        session.save()
        self.assertEqual(job_control.evalCOCondition(machine, session), 'material')
        # Test 7 - machine opmode = 1, output < quantity, no error, mold adjust ON
        # CO condition should be 'moldadjust'
        machine.cleaningStatus = False
        machine.moldAdjustStatus = True
        machine.save()
        self.assertEqual(job_control.evalCOCondition(machine, session), 'moldadjust')
        # Test 8 - machine opmode = 1, output < quantity, ERROR, mold adjust ON
        # CO condition should be 'nochange'
        session.errflag = True
        session.save()
        self.assertEqual(job_control.evalCOCondition(machine, session), 'nochange')
        # Test 9 - machine opmode = 1, output < quantity, no error, mold adjust and clean pipe ON
        # CO condition should be 'moldadjust'
        session.errflag = False
        session.save()
        machine.cleaningStatus = True
        machine.save()
        self.assertEqual(job_control.evalCOCondition(machine, session), 'moldadjust')
        # Test 10 - machine opmode = 1, output < quantity, no error, switches all OFF
        # CO condition should be 'nochange'
        machine.cleaningStatus = False
        machine.moldAdjustStatus = False
        machine.motorOnOffStatus = False
        machine.save()
        self.assertEqual(job_control.evalCOCondition(machine, session), 'nochange')
        # Test 11 - machine opmode = 1, output > quantity, no error, switches all OFF
        # CO condition should be 'mold'
        machine.cleaningStatus = False
        machine.moldAdjustStatus = False
        machine.motorOnOffStatus = False
        machine.save()
        ProductionDataTS.objects.create(job=Job.objects.first(), output=101)
        self.assertEqual(job_control.evalCOCondition(machine, session), 'mold')