from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from djcelery.models import PeriodicTask
from datetime import timedelta
from device.fcs_injection_db import FCSInjectionDevice_db
from core import xmlparser
from core import request_sender
from core import job_control


logger = get_task_logger(__name__)
__fPeriod = 10      # fixed period of 10s
__dPeriod = 15      # dynamic period, default to 15s

@periodic_task(run_every=timedelta(seconds=__fPeriod))
def pollDeviceStatus():
    logger.info("Polling device status (p={})...".format(__fPeriod))
    result = FCSInjectionDevice_db.activeDevice.getDeviceStatus()
    if result is not None:
        job_control.processQueryResult('opStatus', result)
    
@periodic_task(run_every=timedelta(seconds=__dPeriod))
def pollProdStatus():
    pTask = PeriodicTask.objects.filter(name='scope_core.tasks.pollProdStatus')[0]
    logger.info("Polling production data (p={})...".format(pTask.interval.every))
    result = FCSInjectionDevice_db.activeDevice.getProductionStatus()
    if result is not None:    
        job_control.processQueryResult('opMetrics', result, pTask)