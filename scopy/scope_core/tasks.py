"""Celery task definition for scope_core app"""

from datetime import timedelta
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from djcelery.models import PeriodicTask
from django.core.cache import cache
from scope_core.core import job_control

logger = get_task_logger(__name__)
P_PRIOR_HIGH = 60
P_PRIOR_MID = 90
P_PRIOR_LOW = 120
LOCK_EXPIRE = 60
LOCK_ID = "shared-lock"

@periodic_task(run_every=timedelta(seconds=P_PRIOR_HIGH))
def pollDeviceStatus():
    global LOCK_ID
    global logger
    LOCK_ID = '{0}-lock'.format('statustask')
    acquire_lock = lambda: cache.add(LOCK_ID, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(LOCK_ID)

    if acquire_lock():
        logger.info("Polling device status (p={})...".format(P_PRIOR_HIGH))
        try:
            job_control.poll_device_status()
        finally:
            release_lock()
    else:
        logger.info("Blocked: previous task not finished yet! ({})".format(LOCK_ID))

@periodic_task(run_every=timedelta(seconds=P_PRIOR_LOW))
def pollAlarmStatus():
    global LOCK_ID
    global logger
    LOCK_ID = '{0}-lock'.format('alarmtask')
    acquire_lock = lambda: cache.add(LOCK_ID, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(LOCK_ID)

    if acquire_lock():
        logger.info("Polling alarm status (p={})...".format(P_PRIOR_LOW))
        try:
            job_control.poll_alarm_status()
        finally:
            release_lock()
    else:
        logger.info("Blocked: previous task not finished yet! ({})".format(LOCK_ID))

@periodic_task(run_every=timedelta(seconds=P_PRIOR_MID))
def pollProdStatus():
    global LOCK_ID
    global logger
    lock_id = '{0}-lock'.format('infotask')
    acquire_lock = lambda: cache.add(LOCK_ID, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(LOCK_ID)

    if acquire_lock():
        pTask = PeriodicTask.objects.filter(name='scope_core.tasks.pollProdStatus')[0]
        logger.info("Polling production data (p={})...".format(pTask.interval.every))
        try:
            job_control.poll_prod_status()
        finally:
            release_lock()
    else:
        logger.info("Blocked: previous task not finished yet! ({})".format(LOCK_ID))
