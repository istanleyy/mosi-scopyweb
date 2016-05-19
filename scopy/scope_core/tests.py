from django.test import TestCase
from djcelery.models import PeriodicTask, IntervalSchedule
from .models import Job, SessionManagement, Machine, ProductionDataTS
from .core import xmlparser
from .core import job_control
from .device_manager.modbus_manager import ModbusConnectionManager
from .device import device_definition as const

class XmlParserTestCase(TestCase):

    def test_unsync_log(self):
        print '\n#####################################'
        print '# running unsync log test'
        print '#####################################'
        # Setup test DB entries
        Job.objects.create(productid="TESTJOB", moldid="TESTMOLD", quantity=100)
        SessionManagement.objects.create(job=Job.objects.first())
        # Get xml messages to test logging methods
        updatemsg = xmlparser.getJobUpdateXml(0, 10)
        eventmsg = xmlparser.getJobEventXml(6, 'NJ')
        self.assertEqual(xmlparser.logUnsyncMsg(updatemsg), True)
        self.assertEqual(xmlparser.logUnsyncMsg(eventmsg), True)
        
class ModbusManagerTestCase(TestCase):

    def test_read(self):
        print '\n#####################################'
        print '# running modbus manager read test'
        print '#####################################'
        mbconn = ModbusConnectionManager('tcp')
        mbconn.connect()
        self.assertEqual(mbconn.readHoldingReg(4001, 2), (0,0))
        self.assertEqual(mbconn.readCoil(11, 2), (0,0))

class JobControlTestCase(TestCase):

    def test_co_flow(self):
        print '\n#####################################'
        print '# running job control CO flow test'
        print '#####################################'
        # Setup test DB entries
        job1 = Job.objects.create(productid="TESTJOB1", moldid="TESTMOLD1", quantity=100, ct=30)
        job2 = Job.objects.create(productid="TESTJOB2", moldid="TESTMOLD2", quantity=100, ct=45)
        job3 = Job.objects.create(productid="TESTJOB3", moldid="TESTMOLD2", quantity=100, ct=50)
        session = SessionManagement.objects.create(job=Job.objects.first())
        intv, created = IntervalSchedule.objects.get_or_create(every=60, period='seconds')
        task = PeriodicTask.objects.create(name='scope_core.tasks.pollProdStatus', interval=intv)
        # Starting job1
        job_control.processQueryResult('opStatus', (const.AUTO_MODE, const.RUNNING, 'TESTMOLD1'))
        self.assertEqual(Job.objects.get(productid="TESTJOB1").inprogress, True)
        # Change job1 running mode, inprogress state should remain unchanged
        job_control.processQueryResult('opStatus', (const.MANUAL_MODE, const.RUNNING, 'TESTMOLD1'))
        self.assertEqual(Job.objects.get(productid="TESTJOB1").inprogress, True)
        # Change status of job1 to CHG_MATERIAL, inprogress state should become FALSE
        job_control.processQueryResult('opStatus', (const.MANUAL_MODE, const.CHG_MATERIAL, 'TESTMOLD1'))
        self.assertEqual(Job.objects.get(productid="TESTJOB1").inprogress, False)
        # Resume job1, inprogress should be TRUE
        job_control.processQueryResult('opStatus', (const.AUTO_MODE, const.RUNNING, 'TESTMOLD1'))
        self.assertEqual(Job.objects.get(productid="TESTJOB1").inprogress, True)
        # Change mold, select 'TESTMOLD2' should pick job2 as next job, and change job1 to inactive
        job_control.processQueryResult('opStatus', (const.MANUAL_MODE, const.CHG_MOLD, 'TESTMOLD2'), task)
        self.assertEqual(SessionManagement.objects.first().job.productid, 'TESTJOB2')
        self.assertEqual(Job.objects.get(productid="TESTJOB1").active, False)
        # Change mold complete, resume operation, job2 inprogres should be TRUE
        job_control.processQueryResult('opStatus', (const.AUTO_MODE, const.RUNNING, 'TESTMOLD2'))
        self.assertEqual(Job.objects.get(productid="TESTJOB2").inprogress, True)
        # Change status of job2 to CHG_MATERIAL, inprogress state should become FALSE
        job_control.processQueryResult('opStatus', (const.MANUAL_MODE, const.CHG_MATERIAL, 'TESTMOLD2'))
        self.assertEqual(Job.objects.get(productid="TESTJOB2").inprogress, False)
        # Resume job2, inprogress should be TRUE
        job_control.processQueryResult('opStatus', (const.AUTO_MODE, const.RUNNING, 'TESTMOLD2'))
        self.assertEqual(Job.objects.get(productid="TESTJOB2").inprogress, True)
        # Change mold, select 'TESTMOLD2' should pick job3 as next job, and change job2 to inactive
        job_control.processQueryResult('opStatus', (const.MANUAL_MODE, const.CHG_MOLD, 'TESTMOLD2'), task)
        self.assertEqual(SessionManagement.objects.first().job.productid, 'TESTJOB3')
        self.assertEqual(Job.objects.get(productid="TESTJOB2").active, False)
        # Change mold complete, resume operation, job3 inprogres should be TRUE
        job_control.processQueryResult('opStatus', (const.AUTO_MODE, const.RUNNING, 'TESTMOLD2'))
        self.assertEqual(Job.objects.get(productid="TESTJOB3").inprogress, True)
    
    """
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
    """