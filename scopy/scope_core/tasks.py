"""Celery task definition for scope_core app"""
from __future__ import absolute_import, unicode_literals

from datetime import timedelta
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from djcelery.models import PeriodicTask
from django.core.cache import cache
from scope_core.core import job_control

LOGGER = get_task_logger(__name__)
P_PRIOR_HIGH = 60
P_PRIOR_MID = 90
P_PRIOR_LOW = 120
LOCK_EXPIRE = 60
LOCK_ID = "shared-lock"

def init_tasks():
    """Performs the initial execution of tasks when system is up."""
    poll_status_task.delay()

@periodic_task(run_every=(timedelta(seconds=P_PRIOR_HIGH)))
def poll_status_task():
    """Task to poll device status"""
    global LOCK_ID
    global LOGGER
    LOCK_ID = '{0}-lock'.format('statustask')
    acquire_lock = lambda: cache.add(LOCK_ID, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(LOCK_ID)

    if acquire_lock():
        LOGGER.info("Polling device status (p={})...".format(P_PRIOR_HIGH))
        try:
            job_control.poll_device_status()
        finally:
            release_lock()
    else:
        LOGGER.info("Blocked: previous task not finished yet! ({})".format(LOCK_ID))

@periodic_task(run_every=(timedelta(seconds=P_PRIOR_LOW)))
def poll_alarm_task():
    """Task to poll alarm status"""
    global LOCK_ID
    global LOGGER
    LOCK_ID = '{0}-lock'.format('alarmtask')
    acquire_lock = lambda: cache.add(LOCK_ID, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(LOCK_ID)

    if acquire_lock():
        LOGGER.info("Polling alarm status (p={})...".format(P_PRIOR_LOW))
        try:
            job_control.poll_alarm_status()
        finally:
            release_lock()
    else:
        LOGGER.info("Blocked: previous task not finished yet! ({})".format(LOCK_ID))

@periodic_task(run_every=(timedelta(seconds=P_PRIOR_MID)))
def poll_metrics_task():
    """Task to poll production metrics"""
    global LOCK_ID
    global LOGGER
    LOCK_ID = '{0}-lock'.format('infotask')
    acquire_lock = lambda: cache.add(LOCK_ID, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(LOCK_ID)

    if acquire_lock():
        p_task = PeriodicTask.objects.filter(name='scope_core.tasks.poll_metrics_task')[0]
        LOGGER.info("Polling production data (p={})...".format(p_task.interval.every))
        try:
            job_control.poll_prod_status()
        finally:
            release_lock()
    else:
        LOGGER.info("Blocked: previous task not finished yet! ({})".format(LOCK_ID))
