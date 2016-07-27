from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from djcelery.models import PeriodicTask
from django.core.cache import cache
from datetime import timedelta
from core import xmlparser
from core import request_sender
from core import job_control
from core import device_manager as device


logger = get_task_logger(__name__)
P_PRIOR_HIGH = 9
P_PRIOR_MID = 11
P_PRIOR_LOW = 17
LOCK_EXPIRE = 60

@periodic_task(run_every=timedelta(seconds=P_PRIOR_MID))
def pollDeviceStatus():
    lock_id = '{0}-lock'.format('statustask')
    acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)
    
    if acquire_lock():
        logger.info("Polling device status (p={})...".format(P_PRIOR_MID))
        try:
            result = device.getDeviceInstance().getDeviceStatus()
            pTask = PeriodicTask.objects.filter(name='scope_core.tasks.pollProdStatus')[0]
            job_control.processQueryResult('opStatus', result, pTask)
        finally:
            release_lock()
    else:
        logger.info("Blocked: previous task not finished yet! ({})".format(lock_id))

@periodic_task(run_every=timedelta(seconds=P_PRIOR_HIGH))
def pollAlarmStatus():
    lock_id = '{0}-lock'.format('alarmtask')
    acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)
    
    if acquire_lock():
        logger.info("Polling alarm status (p={})...".format(P_PRIOR_HIGH))
        try:
            result = device.getDeviceInstance().getAlarmStatus()
            if result is not None:
                job_control.processQueryResult('alarmStatus', result)
        finally:
            release_lock()
    else:
        logger.info("Blocked: previous task not finished yet! ({})".format(lock_id))

@periodic_task(run_every=timedelta(seconds=P_PRIOR_LOW))
def pollProdStatus():
    lock_id = '{0}-lock'.format('infotask')
    acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)
    
    if acquire_lock():
        pTask = PeriodicTask.objects.filter(name='scope_core.tasks.pollProdStatus')[0]
        logger.info("Polling production data (p={})...".format(pTask.interval.every))
        try:
            result = device.getDeviceInstance().getProductionStatus()
            if result is not None:    
                job_control.processQueryResult('opMetrics', result, pTask)
        finally:
            release_lock()
    else:
        logger.info("Blocked: previous task not finished yet! ({})".format(lock_id))
